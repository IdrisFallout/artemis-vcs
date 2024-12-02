import argparse
import os
import json
import hashlib
import shutil
import re
from typing import Dict, List, Optional


class Repository:
    def __init__(self, path: str):
        """
        Initialize a new repository or load an existing one

        :param path: Path to the repository root
        """
        self.root = os.path.abspath(path)
        self.repo_dir = os.path.join(self.root, '.artemis')

        # Create repository structure if it doesn't exist
        if not os.path.exists(self.repo_dir):
            os.makedirs(self.repo_dir)
            os.makedirs(os.path.join(self.repo_dir, 'objects'))
            os.makedirs(os.path.join(self.repo_dir, 'refs'))
            os.makedirs(os.path.join(self.repo_dir, 'branches'))

            # Initialize HEAD to point to master branch
            with open(os.path.join(self.repo_dir, 'HEAD'), 'w') as f:
                f.write('ref: refs/heads/master')

            # Create initial branches directory
            os.makedirs(os.path.join(self.repo_dir, 'refs', 'heads'))

        # Load .gitignore if it exists
        self.ignored_patterns = self.load_gitignore()

    def load_gitignore(self) -> List[str]:
        """
        Load patterns to ignore from .gitignore file

        :return: List of ignore patterns
        """
        gitignore_path = os.path.join(self.root, '.gitignore')
        if not os.path.exists(gitignore_path):
            return []

        with open(gitignore_path, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

    def is_ignored(self, path: str) -> bool:
        """
        Check if a file should be ignored based on .gitignore patterns

        :param path: Relative path of the file
        :return: True if file should be ignored, False otherwise
        """
        for pattern in self.ignored_patterns:
            if re.search(pattern.replace('.', r'\.').replace('*', '.*'), path):
                return True
        return False

    def _hash_object(self, data: bytes) -> str:
        """
        Create a hash for an object

        :param data: Bytes to hash
        :return: Hash string
        """
        return hashlib.sha1(data).hexdigest()

    def write_object(self, data: bytes) -> str:
        """
        Write an object to the repository

        :param data: Data to write
        :return: Hash of the object
        """
        obj_hash = self._hash_object(data)
        obj_path = os.path.join(self.repo_dir, 'objects', obj_hash)

        if not os.path.exists(obj_path):
            with open(obj_path, 'wb') as f:
                f.write(data)

        return obj_hash

    def read_object(self, obj_hash: str) -> bytes:
        """
        Read an object from the repository

        :param obj_hash: Hash of the object to read
        :return: Object data
        """
        obj_path = os.path.join(self.repo_dir, 'objects', obj_hash)

        if not os.path.exists(obj_path):
            raise ValueError(f"Object {obj_hash} not found")

        with open(obj_path, 'rb') as f:
            return f.read()

    def stage_file(self, path: str):
        """
        Stage a file for commit

        :param path: Path to the file relative to repository root
        """
        full_path = os.path.join(self.root, path)

        # Check if file is ignored
        if self.is_ignored(path):
            print(f"File {path} is ignored")
            return

        if not os.path.exists(full_path):
            raise ValueError(f"File {path} does not exist")

        # Read file contents
        with open(full_path, 'rb') as f:
            file_contents = f.read()

        # Write file object
        file_hash = self.write_object(file_contents)

        # Update index
        index_path = os.path.join(self.repo_dir, 'index')

        # Read existing index or create new
        index = {}
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                index = json.load(f)

        # Update index with new file hash
        index[path] = file_hash

        # Write updated index
        with open(index_path, 'w') as f:
            json.dump(index, f)

    def status(self):
        """
        Show the status of the repository: staged, modified, or untracked files.
        """
        index_path = os.path.join(self.repo_dir, 'index')

        # Load the staged files from the index (if exists)
        staged_files = {}
        if os.path.exists(index_path):
            with open(index_path, 'r') as f:
                staged_files = json.load(f)

        # List of all files in the working directory (ignoring files in .gitignore)
        untracked_files = []
        modified_files = []
        staged_files_names = list(staged_files.keys())

        for root, dirs, files in os.walk(self.root):
            # Skip the .artemis directory
            if root.startswith(os.path.join(self.root, '.artemis')):
                continue

            # Check all files in the directory
            for file in files:
                relative_path = os.path.relpath(os.path.join(root, file), self.root)

                # Skip ignored files
                if self.is_ignored(relative_path):
                    continue

                # Check if file is staged
                if relative_path in staged_files:
                    # Read the file content from both working directory and index to check for modifications
                    full_path = os.path.join(root, file)
                    with open(full_path, 'rb') as f:
                        current_data = f.read()

                    # Compare against the staged object
                    staged_hash = staged_files[relative_path]
                    staged_data = self.read_object(staged_hash)

                    if current_data != staged_data:
                        modified_files.append(relative_path)
                else:
                    untracked_files.append(relative_path)

        # Output the status
        print("Changes not staged for commit:")
        for file in modified_files:
            print(f"  modified:   {file}")

        print("\nUntracked files:")
        for file in untracked_files:
            print(f"  untracked: {file}")

        # Display files that are staged
        print("\nChanges to be committed:")
        for file in staged_files_names:
            print(f"  staged:     {file}")


    def commit(self, message: str):
        """
        Create a commit with staged files

        :param message: Commit message
        """
        index_path = os.path.join(self.repo_dir, 'index')

        if not os.path.exists(index_path):
            raise ValueError("No files staged")

        # Read index
        with open(index_path, 'r') as f:
            index = json.load(f)

        # Create tree object from index
        tree_contents = json.dumps(index, sort_keys=True).encode()
        tree_hash = self.write_object(tree_contents)

        # Get current branch
        with open(os.path.join(self.repo_dir, 'HEAD'), 'r') as f:
            current_branch = f.read().split('/')[-1]

        # Get previous commit hash if exists
        branch_path = os.path.join(self.repo_dir, 'refs', 'heads', current_branch)
        parent_hash = None
        if os.path.exists(branch_path):
            with open(branch_path, 'r') as f:
                parent_hash = f.read().strip()

        # Create commit object
        commit_data = {
            'tree': tree_hash,
            'parent': parent_hash,
            'message': message
        }
        commit_contents = json.dumps(commit_data, sort_keys=True).encode()
        commit_hash = self.write_object(commit_contents)

        # Update branch ref
        with open(os.path.join(self.repo_dir, 'refs', 'heads', current_branch), 'w') as f:
            f.write(commit_hash)

        # Clear index after commit
        os.remove(index_path)

    def log(self):
        """
        Display commit history
        """
        # Get current branch
        with open(os.path.join(self.repo_dir, 'HEAD'), 'r') as f:
            current_branch = f.read().split('/')[-1]

        branch_path = os.path.join(self.repo_dir, 'refs', 'heads', current_branch)

        if not os.path.exists(branch_path):
            print("No commits yet")
            return

        # Start from the latest commit
        with open(branch_path, 'r') as f:
            current_commit = f.read().strip()

        while current_commit:
            # Read commit object
            commit_data = json.loads(self.read_object(current_commit).decode())

            print(f"Commit: {current_commit}")
            print(f"Message: {commit_data['message']}")
            print("---")

            # Move to parent commit
            current_commit = commit_data.get('parent')

    def create_branch(self, branch_name: str):
        """
        Create a new branch from current HEAD

        :param branch_name: Name of the new branch
        """
        # Get current commit
        with open(os.path.join(self.repo_dir, 'HEAD'), 'r') as f:
            current_branch = f.read().split('/')[-1]

        branch_path = os.path.join(self.repo_dir, 'refs', 'heads', current_branch)
        new_branch_path = os.path.join(self.repo_dir, 'refs', 'heads', branch_name)

        if os.path.exists(new_branch_path):
            raise ValueError(f"Branch {branch_name} already exists")

        # Copy current branch's commit hash to new branch
        with open(branch_path, 'r') as f:
            current_commit = f.read().strip()

        with open(new_branch_path, 'w') as f:
            f.write(current_commit)

    def checkout(self, branch_or_commit: str):
        """
        Checkout a branch or commit

        :param branch_or_commit: Branch name or commit hash
        """
        branch_path = os.path.join(self.repo_dir, 'refs', 'heads', branch_or_commit)

        # Determine if it's a branch or a commit hash
        if os.path.exists(branch_path):
            # Branch checkout
            with open(branch_path, 'r') as f:
                commit_hash = f.read().strip()

            # Update HEAD
            with open(os.path.join(self.repo_dir, 'HEAD'), 'w') as f:
                f.write(f'ref: refs/heads/{branch_or_commit}')
        else:
            # Assume it's a commit hash
            commit_hash = branch_or_commit

        # Read commit object
        commit_data = json.loads(self.read_object(commit_hash).decode())

        # Read tree object
        tree_data = json.loads(self.read_object(commit_data['tree']).decode())

        # Restore files from tree
        for path, file_hash in tree_data.items():
            file_contents = self.read_object(file_hash)
            full_path = os.path.join(self.root, path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'wb') as f:
                f.write(file_contents)

    def diff(self, branch1: str, branch2: str):
        """
        Show differences between two branches

        :param branch1: First branch name
        :param branch2: Second branch name
        """
        # Get commit hashes for both branches
        branch1_path = os.path.join(self.repo_dir, 'refs', 'heads', branch1)
        branch2_path = os.path.join(self.repo_dir, 'refs', 'heads', branch2)

        with open(branch1_path, 'r') as f:
            commit1_hash = f.read().strip()

        with open(branch2_path, 'r') as f:
            commit2_hash = f.read().strip()

        # Read commit objects
        commit1_data = json.loads(self.read_object(commit1_hash).decode())
        commit2_data = json.loads(self.read_object(commit2_hash).decode())

        # Read tree objects
        tree1_data = json.loads(self.read_object(commit1_data['tree']).decode())
        tree2_data = json.loads(self.read_object(commit2_data['tree']).decode())

        # Find differences
        all_files = set(list(tree1_data.keys()) + list(tree2_data.keys()))

        for file in all_files:
            if file not in tree1_data:
                print(f"Added in {branch2}: {file}")
            elif file not in tree2_data:
                print(f"Deleted in {branch2}: {file}")
            elif tree1_data[file] != tree2_data[file]:
                print(f"Modified in {branch2}: {file}")

    def clone(self, destination: str):
        """
        Clone the repository to a new location

        :param destination: Path to clone repository
        """
        # Create destination directory
        os.makedirs(destination, exist_ok=True)

        # Copy entire .artemis directory
        shutil.copytree(
            os.path.join(self.root, '.artemis'),
            os.path.join(destination, '.artemis'),
            dirs_exist_ok=True
        )

        # Get current branch from HEAD
        with open(os.path.join(self.root, '.artemis', 'HEAD'), 'r') as f:
            current_branch = f.read().split('/')[-1]

        # Restore files from current branch's commit
        branch_path = os.path.join(destination, '.artemis', 'refs', 'heads', current_branch)

        with open(branch_path, 'r') as f:
            commit_hash = f.read().strip()

        # Read commit object
        commit_data = json.loads(self.read_object(commit_hash).decode())

        # Read tree object
        tree_data = json.loads(self.read_object(commit_data['tree']).decode())

        # Restore files from tree
        for path, file_hash in tree_data.items():
            file_contents = self.read_object(file_hash)
            full_path = os.path.join(destination, path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'wb') as f:
                f.write(file_contents)


def init_repo(path: str) -> Repository:
    """
    Initialize a new repository
    :param path: Path to initialize repository
    :return: Repository object
    """
    return Repository(path)


def parse_args():
    parser = argparse.ArgumentParser(description="A simple Artemis repository management CLI")

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # init command
    subparsers.add_parser('init', help='Initialize a new repository')

    # stage command
    stage_parser = subparsers.add_parser('stage', help='Stage a file for commit')
    stage_parser.add_argument('path', help='Path to the file to stage')

    # commit command
    commit_parser = subparsers.add_parser('commit', help='Create a commit')
    commit_parser.add_argument('message', help='Commit message')

    # log command
    subparsers.add_parser('log', help='Display commit history')

    # create-branch command
    create_branch_parser = subparsers.add_parser('create-branch', help='Create a new branch')
    create_branch_parser.add_argument('branch_name', help='Name of the new branch')

    # checkout command
    checkout_parser = subparsers.add_parser('checkout', help='Checkout a branch or commit')
    checkout_parser.add_argument('branch_or_commit', help='Branch name or commit hash to checkout')

    # clone command
    clone_parser = subparsers.add_parser('clone', help='Clone the repository to a new location')
    clone_parser.add_argument('destination', help='Destination path to clone the repository')

    # status command
    subparsers.add_parser('status', help='Show the status of the repository')

    return parser.parse_args()


def main():
    args = parse_args()

    # Initialize repository object
    repo = Repository(os.getcwd())  # Default to the current working directory

    if args.command == 'init':
        repo = init_repo(os.getcwd())
        print(f"Repository initialized at {os.getcwd()}")

    elif args.command == 'stage':
        repo.stage_file(args.path)
        print(f"File {args.path} staged")

    elif args.command == 'commit':
        repo.commit(args.message)
        print(f"Commit created with message: {args.message}")

    elif args.command == 'log':
        repo.log()

    elif args.command == 'create-branch':
        repo.create_branch(args.branch_name)
        print(f"Branch {args.branch_name} created")

    elif args.command == 'checkout':
        repo.checkout(args.branch_or_commit)
        print(f"Checked out to {args.branch_or_commit}")

    elif args.command == 'clone':
        repo.clone(args.destination)
        print(f"Repository cloned to {args.destination}")

    elif args.command == 'status':
        repo.status()


if __name__ == '__main__':
    main()