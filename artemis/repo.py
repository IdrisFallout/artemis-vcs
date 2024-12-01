import os
import json

ARTEMIS_DIR = '.artemis'

def init():
    """
    Initializes an Artemis repository by creating a .artemis directory
    with necessary subdirectories and files.
    """
    if os.path.exists(ARTEMIS_DIR):
        print("Artemis repository already exists in this directory.")
        return

    # Create the .artemis structure
    os.makedirs(f'{ARTEMIS_DIR}/objects')  # For storing file snapshots (blobs)
    os.makedirs(f'{ARTEMIS_DIR}/refs/heads')  # For branches
    os.makedirs(f'{ARTEMIS_DIR}/refs/tags')  # For tags (optional, for future)

    # Create essential files
    with open(f'{ARTEMIS_DIR}/HEAD', 'w') as head_file:
        head_file.write('ref: refs/heads/main')  # Default branch is "main"

    with open(f'{ARTEMIS_DIR}/config', 'w') as config_file:
        config = {
            "core": {
                "repositoryformatversion": 0,
                "filemode": False,
                "bare": False,
            }
        }
        json.dump(config, config_file, indent=4)

    print(f"Initialized empty Artemis repository in {ARTEMIS_DIR}/")


def is_repo():
    """
    Checks if the current directory is inside an Artemis repository.
    """
    return os.path.exists(ARTEMIS_DIR) and os.path.isdir(ARTEMIS_DIR)


def get_head():
    """
    Reads the HEAD pointer to determine the current branch.
    Returns:
        str: Current branch name (e.g., "main") or commit hash if detached.
    """
    try:
        with open(f'{ARTEMIS_DIR}/HEAD', 'r') as head_file:
            ref = head_file.read().strip()
            if ref.startswith('ref:'):
                branch = ref.split(' ')[1]
                return branch.replace('refs/heads/', '')
            else:
                return ref  # Detached HEAD points directly to a commit hash
    except FileNotFoundError:
        print(f"Error: Not an Artemis repository or HEAD is missing.")
        return None


def update_head(branch_name):
    """
    Updates the HEAD to point to a new branch.
    Args:
        branch_name (str): The branch name to point HEAD to.
    """
    try:
        with open(f'{ARTEMIS_DIR}/HEAD', 'w') as head_file:
            head_file.write(f'ref: refs/heads/{branch_name}')
        print(f"Switched to branch '{branch_name}'")
    except FileNotFoundError:
        print("Error: Not an Artemis repository or HEAD is missing.")


def list_branches():
    """
    Lists all branches in the repository.
    """
    branches_dir = f'{ARTEMIS_DIR}/refs/heads'
    try:
        branches = os.listdir(branches_dir)
        current_branch = get_head()
        for branch in branches:
            if branch == current_branch:
                print(f"* {branch}")
            else:
                print(f"  {branch}")
    except FileNotFoundError:
        print("Error: Not an Artemis repository or refs/heads is missing.")


def create_branch(branch_name):
    """
    Creates a new branch pointing to the current commit.
    Args:
        branch_name (str): The name of the branch to create.
    """
    head_ref = get_head()
    if not head_ref:
        print("Error: Cannot create branch, HEAD is invalid.")
        return

    branch_path = f'{ARTEMIS_DIR}/refs/heads/{branch_name}'
    if os.path.exists(branch_path):
        print(f"Branch '{branch_name}' already exists.")
        return

    # Get current commit hash
    current_commit_path = f'{ARTEMIS_DIR}/{head_ref}'
    if os.path.exists(current_commit_path):
        with open(current_commit_path, 'r') as commit_file:
            commit_hash = commit_file.read().strip()
    else:
        commit_hash = "null"  # No commits yet

    # Create the branch
    with open(branch_path, 'w') as branch_file:
        branch_file.write(commit_hash)
    print(f"Created branch '{branch_name}'")
