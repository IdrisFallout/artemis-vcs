import os
import stat
from colorama import Fore, Style
import ctypes
import hashlib

def init_repository():
    """
    Initializes an Artemis repository by creating a .artemis directory
    in the current working directory, along with necessary subdirectories
    and files, replicating Git's init behavior. Ensures the folder is hidden
    on Windows.
    """
    repo_dir = os.path.join(os.getcwd(), '.artemis')

    if os.path.exists(repo_dir):
        print(Fore.YELLOW + f"[Warning] The repository '{repo_dir}' already exists." + Style.RESET_ALL)
    else:
        try:
            # Create the main .artemis directory
            os.mkdir(repo_dir)

            # Hide the folder on Windows
            if os.name == 'nt':
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(repo_dir, FILE_ATTRIBUTE_HIDDEN)

            # Create subdirectories
            os.makedirs(os.path.join(repo_dir, 'objects'))
            os.makedirs(os.path.join(repo_dir, 'refs', 'heads'))
            os.makedirs(os.path.join(repo_dir, 'refs', 'tags'))
            os.makedirs(os.path.join(repo_dir, 'logs', 'refs', 'heads'))
            os.makedirs(os.path.join(repo_dir, 'logs', 'refs', 'tags'))
            os.makedirs(os.path.join(repo_dir, 'info'))

            # Create necessary files
            description_path = os.path.join(repo_dir, 'description')
            with open(description_path, 'w') as f:
                f.write("Unnamed repository; edit this file to name the repository.\n")

            head_path = os.path.join(repo_dir, 'HEAD')
            with open(head_path, 'w') as f:
                f.write("ref: refs/heads/main\n")

            config_path = os.path.join(repo_dir, 'config')
            with open(config_path, 'w') as f:
                f.write("""[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
""")

            index_path = os.path.join(repo_dir, 'index')
            with open(index_path, 'w') as f:
                f.write("")  # Empty file for staging

            exclude_path = os.path.join(repo_dir, 'info', 'exclude')
            with open(exclude_path, 'w') as f:
                f.write("""# gitignore-style patterns go here
""")

            # Set permissions (replicating Git behavior)
            os.chmod(repo_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

            print(Fore.GREEN + f"[Success] Initialized empty Artemis repository in '{repo_dir}'." + Style.RESET_ALL)
        except OSError as e:
            print(Fore.RED + f"[Error] Failed to create repository: {e}" + Style.RESET_ALL)


def read_exclude():
    """Reads the '.artemis/info/exclude' file to get a list of ignored files."""
    exclude_file_path = os.path.join(os.getcwd(), '.artemis', 'info', 'exclude')
    if os.path.exists(exclude_file_path):
        with open(exclude_file_path, 'r') as f:
            return set(line.strip() for line in f if line.strip() and not line.startswith('#'))
    return set()


def get_staged_files():
    """Reads the '.artemis/index' file to get a list of staged files."""
    staged_files = set()
    index_path = os.path.join(os.getcwd(), '.artemis', 'index')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            staged_files = set(line.strip() for line in f)
    return staged_files


def get_untracked_files(staged_files, excluded_files):
    """Returns a list of untracked files (files that are not staged or ignored)."""
    untracked_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        # Skip the .artemis directory and its subdirectories
        if '.artemis' in root:
            continue
        for file in files:
            full_path = os.path.join(root, file)
            # Ignore files that are staged or excluded
            if full_path not in staged_files and file not in excluded_files:
                # Store the file relative to the repository root
                relative_path = os.path.relpath(full_path, os.getcwd())
                untracked_files.append(relative_path)
    return untracked_files


def status():
    repo_dir = os.path.join(os.getcwd(), '.artemis')

    if not os.path.exists(repo_dir):
        print(Fore.RED + "[Error] Not an Artemis repository (or any of the parent directories)." + Style.RESET_ALL)
        return

    excluded_files = read_exclude()
    staged_files = get_staged_files()  # Files that are staged for commit
    # staged_files starts with ./, so we need to remove it
    staged_files = [file[2:] for file in staged_files]
    untracked_files = get_untracked_files(staged_files, excluded_files)  # Untracked files

    # Get the current branch name (defaulting to 'master' if not found)
    head_path = os.path.join(repo_dir, 'HEAD')
    branch_name = "master"  # Default branch name
    if os.path.exists(head_path):
        with open(head_path, 'r') as f:
            ref = f.read().strip()
            if ref.startswith("ref: refs/heads/"):
                branch_name = ref[len("ref: refs/heads/"):]

    # Display branch info
    print(f"On branch {branch_name}\n")

    # Check if the repository is empty (no files at all except .artemis directory)
    repo_empty = not any(os.scandir(os.getcwd()))  # Check if there are any files in the repo
    repo_contains_only_artemis = not any(
        entry.name != '.artemis' for entry in os.scandir(os.getcwd()) if entry.is_dir()
    ) and not any(
        file != '.artemis' for file in os.listdir(os.getcwd()) if os.path.isfile(file)
    )

    if repo_empty or repo_contains_only_artemis:
        print("No commits yet")
        print("nothing to commit (create/copy files and use \"artemis add\" to track)")

    # Check if there are any commits made (by checking if the 'index' file exists and is not empty)
    index_path = os.path.join(repo_dir, 'index')
    if not os.path.exists(index_path) or os.stat(index_path).st_size == 0:
        print("No commits yet")

    # Changes to be committed section
    if staged_files:
        print("\nChanges to be committed:")
        print('  (use "artemis rm --cached <file>..." to unstage)')
        for file in staged_files:
            print(Fore.GREEN + f"        new file:   {file}" + Style.RESET_ALL)

    # Untracked files section
    if untracked_files:
        print("\nUntracked files:")
        print('  (use "artemis add <file>..." to include in what will be committed)')

        # Filter out staged files from untracked files list
        untracked_files = [file for file in untracked_files if file not in staged_files]

        # Group untracked files by top-level directories
        grouped_dirs = set()
        for file in untracked_files:
            top_level_dir = file.split(os.sep)[0]
            grouped_dirs.add(top_level_dir)

        # Print untracked top-level directories and their files
        for dir_name in grouped_dirs:
            if os.path.isdir(dir_name):
                print(Fore.RED + f"    {dir_name}/" + Style.RESET_ALL)
            else:
                print(Fore.RED + f"    {dir_name}" + Style.RESET_ALL)

    # Display the additional message about untracked files
    if not staged_files and untracked_files:
        print("\nnothing added to commit but untracked files present (use \"artemis add\" to track)")

    elif staged_files and not untracked_files:
        print("\nnothing added to commit")
