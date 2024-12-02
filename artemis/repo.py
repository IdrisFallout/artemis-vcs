import ctypes
import os
import platform

from colorama import Fore, Style

ARTEMIS_DIR = '.artemis'
STAGING_AREA = os.path.join(ARTEMIS_DIR, 'staging_area')


def set_hidden_windows(folder):
    """Sets the hidden attribute on a folder for Windows."""
    FILE_ATTRIBUTE_HIDDEN = 0x02
    try:
        # Set the hidden attribute on the folder
        ctypes.windll.kernel32.SetFileAttributesW(folder, FILE_ATTRIBUTE_HIDDEN)
    except Exception as e:
        print(f"Failed to set hidden attribute on {folder}: {e}")


def init():
    """
    Initializes a new repository by creating the .artemis directory and its substructure.
    """
    subdirs = [
        os.path.join(ARTEMIS_DIR, "objects"),
        os.path.join(ARTEMIS_DIR, "refs"),
        os.path.join(ARTEMIS_DIR, "refs/heads"),
        os.path.join(ARTEMIS_DIR, "refs/tags"),
        os.path.join(ARTEMIS_DIR, "staging_area")  # Ensure there's a staging area for staging files
    ]
    files = {
        os.path.join(ARTEMIS_DIR, "HEAD"): "ref: refs/heads/main\n",
        os.path.join(ARTEMIS_DIR, "config"): """
[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
""".strip(),
        os.path.join(ARTEMIS_DIR, "description"): "Unnamed repository; edit this file to name the repository.\n"
    }

    if os.path.exists(ARTEMIS_DIR):
        print("Reinitialized existing repository in", os.path.abspath(ARTEMIS_DIR))
        return

    try:
        # Create subdirectories
        for subdir in subdirs:
            os.makedirs(subdir, exist_ok=True)

        # Create files in the repository
        for file_path, content in files.items():
            with open(file_path, "w") as file:
                file.write(content)

        # Initialize default branch files
        with open(os.path.join(ARTEMIS_DIR, 'refs/heads/main'), 'w') as branch_file:
            branch_file.write('')

        print("Initialized empty repository in", os.path.abspath(ARTEMIS_DIR))
    except Exception as e:
        print(f"Error initializing repository: {e}")


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


def list_files_in_directory(directory):
    """
    Returns a list of files in a directory, excluding hidden files or directories.
    """
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if not file.startswith('.'):  # Skip hidden files
                file_list.append(os.path.relpath(os.path.join(root, file), directory))
    return file_list

def status():
    """
    Display the status of the repository, including staged, untracked, and committed files.
    """
    if not is_repo():
        print(Fore.RED + "Error: Not an Artemis repository." + Style.RESET_ALL)
        return

    current_branch = get_head()
    if current_branch is None:
        print(Fore.RED + "Error: Unable to determine the current branch." + Style.RESET_ALL)
        return

    print(Fore.GREEN + f"On branch {current_branch}" + Style.RESET_ALL)

    # Check for existing commits
    branch_path = os.path.join(ARTEMIS_DIR, 'refs/heads', current_branch)
    if not os.path.exists(branch_path):
        print(Fore.YELLOW + "No commits yet." + Style.RESET_ALL)
    else:
        with open(branch_path, 'r') as branch_file:
            commit_hash = branch_file.read().strip()
        print(Fore.CYAN + f"Current commit: {commit_hash}" + Style.RESET_ALL)

    # Detect staged and untracked files
    tracked_dir = os.path.join(ARTEMIS_DIR, 'objects', current_branch)
    if not os.path.exists(tracked_dir):
        print(Fore.YELLOW + "No objects directory found for the current branch." + Style.RESET_ALL)

    staged_files = set(os.listdir(STAGING_AREA))
    working_dir_files = set(os.listdir('.')) - {ARTEMIS_DIR}

    # Identify untracked and modified files
    untracked_files = working_dir_files - staged_files
    modified_files = staged_files & working_dir_files

    # Handle the case where no files are tracked or staged
    if not staged_files and not untracked_files:
        print(Fore.GREEN + "\nNothing to commit (create/copy files and use 'artemis add' to track)." + Style.RESET_ALL)
        return

    # Report staged changes
    if staged_files:
        print("\nChanges to be committed:" + "\n  (use 'artemis rm --cached <file>...' to unstage)")
        for file in sorted(staged_files):
            file_path = os.path.join(STAGING_AREA, file)
            # If it's a file, show it
            if os.path.isfile(file_path):
                print(Fore.GREEN + f"  {file}" + Style.RESET_ALL)
            # If it's a directory, show files inside
            elif os.path.isdir(file_path):
                files_in_dir = list_files_in_directory(file_path)
                for file_in_dir in files_in_dir:
                    print(Fore.GREEN + f"  {file_in_dir}" + Style.RESET_ALL)
    else:
        print(Fore.GREEN + "\nNo changes staged for commit." + Style.RESET_ALL)

    # Report untracked files
    if untracked_files:
        print("\nUntracked files:" + "\n  (use 'artemis add <file>...' to include in what will be committed)")
        for file in sorted(untracked_files):
            if os.path.isdir(file):
                print(Fore.RED + f"  {file}/" + Style.RESET_ALL)  # Directory
            else:
                print(Fore.RED + f"  {file}" + Style.RESET_ALL)  # File
    else:
        print(Fore.GREEN + "\nNo untracked files." + Style.RESET_ALL)

    # Final clean working tree message
    if not untracked_files and not modified_files:
        print(Fore.GREEN + "\nNothing to commit, working tree clean." + Style.RESET_ALL)