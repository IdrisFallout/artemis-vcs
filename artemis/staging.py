import os
import shutil

from colorama import Fore, Style

from artemis.repo import get_head, is_repo

ARTEMIS_DIR = '.artemis'
STAGING_AREA = os.path.join(ARTEMIS_DIR, 'staging_area')
OBJECTS_DIR = os.path.join(ARTEMIS_DIR, 'objects')


def add(files):
    """
    Stages the specified files by copying them to the staging area and adding them to objects.
    """
    if not os.path.exists(ARTEMIS_DIR):
        print("Error: Not inside a repository.")
        return

    # Ensure the objects and staging area directories exist
    if not os.path.exists(OBJECTS_DIR):
        os.makedirs(OBJECTS_DIR)

    if not os.path.exists(STAGING_AREA):
        os.makedirs(STAGING_AREA)

    # Get the current branch to organize staged files
    current_branch = get_head()
    if current_branch is None:
        print("Error: Unable to determine the current branch.")
        return

    # Create the staging directory for the current branch if it doesn't exist
    branch_staging_dir = os.path.join(STAGING_AREA, current_branch)
    if not os.path.exists(branch_staging_dir):
        os.makedirs(branch_staging_dir)

    # Create the objects directory for the current branch if it doesn't exist
    branch_objects_dir = os.path.join(OBJECTS_DIR, current_branch)
    if not os.path.exists(branch_objects_dir):
        os.makedirs(branch_objects_dir)

    # Process each file and stage it
    for file in files:
        if os.path.exists(file):
            # Get the relative path for the file
            relative_path = os.path.relpath(file, ".")

            # Create the necessary directories in the staging area
            dest = os.path.join(branch_staging_dir, relative_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)

            # Copy the file to the staging area
            shutil.copy(file, dest)

            # Move the file to the objects directory for the current branch
            object_dest = os.path.join(branch_objects_dir, relative_path)
            os.makedirs(os.path.dirname(object_dest), exist_ok=True)
            shutil.copy(file, object_dest)

            print(f"Staged and added to objects: {relative_path}")
        else:
            print(f"Error: {file} does not exist.")


def rm_cached(files):
    """
    Removes the specified files from the staging area (the cached area),
    but leaves them in the working directory.
    """
    if not is_repo():
        print(Fore.RED + "Error: Not an Artemis repository." + Style.RESET_ALL)
        return

    current_branch = get_head()
    if current_branch is None:
        print(Fore.RED + "Error: Unable to determine the current branch." + Style.RESET_ALL)
        return

    # Check if the staging area for the current branch exists
    branch_staging_area = os.path.join(STAGING_AREA, current_branch)
    if not os.path.exists(branch_staging_area):
        print(Fore.RED + "Error: Staging area for the current branch is missing." + Style.RESET_ALL)
        return

    # Process each file
    for file in files:
        file_path = os.path.join(branch_staging_area, file)

        # Check if the file is in the staging area
        if os.path.exists(file_path):
            try:
                # Remove the file from the staging area
                os.remove(file_path)
                print(Fore.GREEN + f"Removed {file} from staging area." + Style.RESET_ALL)
            except Exception as e:
                print(Fore.RED + f"Failed to remove {file} from staging area: {e}" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"Error: {file} not found in staging area." + Style.RESET_ALL)
