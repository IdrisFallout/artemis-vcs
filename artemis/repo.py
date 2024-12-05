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

            # Create current_branch file and set it to 'main'
            current_branch_path = os.path.join(repo_dir, 'current_branch')
            with open(current_branch_path, 'w') as f:
                f.write('main')

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
    # Remove './' prefix from staged files and normalize path separators
    staged_files = [file[2:].replace('\\', '/') for file in staged_files]
    untracked_files = get_untracked_files(staged_files, excluded_files)  # Untracked files
    # Normalize untracked files path separators
    untracked_files = [file.replace('\\', '/') for file in untracked_files]

    # Get the current branch name
    head_path = os.path.join(repo_dir, 'HEAD')
    branch_name = "master"  # Default branch name
    if os.path.exists(head_path):
        with open(head_path, 'r') as f:
            ref = f.read().strip()
            if ref.startswith("ref: refs/heads/"):
                branch_name = ref[len("ref: refs/heads/"):]

    # Display branch info
    print(f"On branch {branch_name}")

    # Check if there are any commits
    index_path = os.path.join(repo_dir, 'index')
    if not os.path.exists(index_path) or os.stat(index_path).st_size == 0:
        print("\nNo commits yet")

    # Changes to be committed section
    if staged_files:
        print("\nChanges to be committed:")
        print('  (use "artemis rm --cached <file>..." to unstage)')
        for file in sorted(staged_files):
            print(Fore.GREEN + f"        new file:   {file}" + Style.RESET_ALL)

    # Untracked files section
    # Filter out staged files from untracked files list
    untracked_files = [file for file in untracked_files if file not in staged_files]

    if untracked_files:
        # Separate untracked directories and files
        untracked_dirs = set()
        untracked_file_list = set()

        for file in untracked_files:
            parts = file.split('/')
            # If file is in a subdirectory and not a direct child of the root
            if len(parts) > 1:
                # Mark the entire directory as untracked if no files in this directory are staged
                root_dir = parts[0]
                if not any(staged_file.startswith(root_dir + '/') for staged_file in staged_files):
                    untracked_dirs.add(root_dir)
                else:
                    # If the directory contains any staged files, list individual untracked files
                    untracked_file_list.add(file)
            else:
                # Root-level untracked files
                untracked_file_list.add(file)

        # Print untracked section
        if untracked_dirs or untracked_file_list:
            print("\nUntracked files:")
            print('  (use "artemis add <file>..." to include in what will be committed)')

            # Print untracked directories first
            for dir_name in sorted(untracked_dirs):
                print(Fore.RED + f"        {dir_name}/" + Style.RESET_ALL)

            # Then print individual untracked files
            for file in sorted(untracked_file_list):
                print(Fore.RED + f"        {file}" + Style.RESET_ALL)

    # Additional messages
    if not staged_files and untracked_files:
        print("\nnothing added to commit but untracked files present (use \"artemis add\" to track)")
    elif staged_files and not untracked_files:
        print("\nnothing added to commit")

