import os
import hashlib
import shutil
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


def get_staged_files():
    """Retrieve the list of staged files (from the index)."""
    index_path = os.path.join(os.getcwd(), '.artemis', 'index')
    if not os.path.exists(index_path):
        return []

    with open(index_path, 'r') as index_file:
        return index_file.read().splitlines()


def save_file_to_objects(file_path, repo_dir):
    """Save file content to the 'objects' directory and return its hash."""
    file_hash = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            file_hash.update(chunk)

    file_hash_hex = file_hash.hexdigest()
    objects_dir = os.path.join(repo_dir, 'objects', file_hash_hex[:2])
    os.makedirs(objects_dir, exist_ok=True)

    # Store file content in the 'objects' directory
    object_file_path = os.path.join(objects_dir, file_hash_hex[2:])
    if not os.path.exists(object_file_path):
        shutil.copy(file_path, object_file_path)

    return file_hash_hex


def get_untracked_files():
    """Return a list of untracked files."""
    untracked_files = []
    # Traverse the repository directory to find untracked files
    repo_dir = os.getcwd()
    for root, _, files in os.walk(repo_dir):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), repo_dir)
            untracked_files.append(relative_path)
    return untracked_files


def update_untracked_files(untracked_files):
    """Update the list of untracked files in the repository."""
    # This could involve clearing some file or list that tracks untracked files
    untracked_file_path = os.path.join(os.getcwd(), '.artemis', 'untracked_files.txt')
    with open(untracked_file_path, 'w') as untracked_file:
        for file in untracked_files:
            untracked_file.write(f"{file}\n")


def commit(message):
    """Commit staged files with the provided message."""
    repo_dir = os.path.join(os.getcwd(), '.artemis')

    # Ensure the repository exists
    if not os.path.exists(repo_dir):
        print(Fore.RED + "[Error] Not an Artemis repository." + Style.RESET_ALL)
        return

    # Get the list of staged files
    staged_files = get_staged_files()
    if not staged_files:
        print(Fore.RED + "[Error] No files staged for commit." + Style.RESET_ALL)
        return

    # Generate commit ID (SHA1 hash of the commit message)
    commit_id = hashlib.sha1(message.encode('utf-8')).hexdigest()[:7]

    # Create a new commit object directory
    commit_dir = os.path.join(repo_dir, 'commits', commit_id)
    os.makedirs(commit_dir, exist_ok=True)

    # Save the staged file contents and create references to them
    file_references = []
    for file in staged_files:
        file_path = os.path.join(os.getcwd(), file)
        if os.path.exists(file_path):
            file_hash = save_file_to_objects(file_path, repo_dir)
            file_references.append(f"{file}: {file_hash}")

    # Record commit metadata (commit message, timestamp, parent commit)
    commit_info_path = os.path.join(commit_dir, 'commit_info.txt')
    with open(commit_info_path, 'w') as commit_file:
        commit_file.write(f"Message: {message}\n")
        commit_file.write(f"Commit ID: {commit_id}\n")
        commit_file.write(f"Timestamp: {datetime.now().isoformat()}\n")
        commit_file.write(f"Files:\n")
        for file_ref in file_references:
            commit_file.write(f"  {file_ref}\n")

    # Retrieve the current branch name
    current_branch_path = os.path.join(repo_dir, 'current_branch')
    if not os.path.exists(current_branch_path):
        # If the current_branch file is missing, default it to 'main'
        print(Fore.YELLOW + "[Warning] No current branch set, defaulting to 'main'." + Style.RESET_ALL)
        with open(current_branch_path, 'w') as branch_file:
            branch_file.write('main')

    with open(current_branch_path, 'r') as branch_file:
        current_branch = branch_file.read().strip()

    # Update the branch reference to point to the new commit
    branch_ref_path = os.path.join(repo_dir, 'refs', 'heads', current_branch)
    os.makedirs(os.path.dirname(branch_ref_path), exist_ok=True)
    with open(branch_ref_path, 'w') as branch_ref:
        branch_ref.write(commit_id)

    # Clear the staging area (index) after commit
    index_path = os.path.join(repo_dir, 'index')
    with open(index_path, 'w') as f:
        f.write("")  # Clear the staging area

    # Remove committed files from the untracked list
    untracked_files = get_untracked_files()
    for file in staged_files:
        if file in untracked_files:
            untracked_files.remove(file)

    # Update the untracked files list
    update_untracked_files(untracked_files)

    # Show success message
    print(Fore.GREEN + f"[Success] Committed changes with message: '{message}' and commit ID: {commit_id}" + Style.RESET_ALL)
