import os

def read_staged_files():
    """Reads the '.artemis/index' file to get a list of currently staged files."""
    staged_files = set()
    index_path = os.path.join(os.getcwd(), '.artemis', 'index')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            staged_files = set(line.strip() for line in f)
    return staged_files

def add_files(files_to_add):
    """Adds files to the staging area (i.e., the '.artemis/index' file)."""
    index_path = os.path.join(os.getcwd(), '.artemis', 'index')
    staged_files = read_staged_files()

    # Ensure the .artemis/index file exists
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    if not os.path.exists(index_path):
        with open(index_path, 'w'):  # Create an empty index file if it doesn't exist
            pass

    # Open the index file to append staged files
    with open(index_path, 'a') as index_file:
        for file in files_to_add:
            # Check if the file exists and is not already staged
            if os.path.exists(file) and file not in staged_files:
                index_file.write(file + '\n')
                print(f"Added: {file}")
            else:
                if not os.path.exists(file):
                    print(f"[Error] File '{file}' does not exist.")
                else:
                    print(f"[Warning] File '{file}' is already staged.")

def artemis_add(files):
    """Add files to the staging area (index)."""
    index_path = os.path.join(os.getcwd(), '.artemis', 'index')

    # Read existing staged files
    staged_files = set()
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            staged_files = set(line.strip() for line in f)

    # Add the new files to the staged files
    staged_files.update(files)

    # Write the updated staged files back to the index
    with open(index_path, 'w') as f:
        for file in staged_files:
            f.write(file + '\n')

    print(f"Added {', '.join(files)} to the staging area.")


def remove_files(files_to_remove, cached=False):
    """
    Removes the specified files from the staging area (i.e., the '.artemis/index' file).
    If `cached` is True, only remove from the staging area, not the working directory.
    """
    index_path = os.path.join(os.getcwd(), '.artemis', 'index')

    # Check if the index file exists
    if not os.path.exists(index_path):
        print("[Error] No staging area exists. Use 'artemis add' to add files first.")
        return

    # Read the current staged files
    with open(index_path, 'r') as f:
        staged_files = set(line.strip() for line in f)

    # Remove specified files from the staged files
    removed_files = []
    for file in files_to_remove:
        if file in staged_files:
            staged_files.remove(file)
            removed_files.append(file)
        else:
            print(f"[Warning] File '{file}' is not in the staging area.")

    # Write the updated staged files back to the index
    with open(index_path, 'w') as f:
        for file in staged_files:
            f.write(file + '\n')

    # If `cached` is False, remove files from the working directory
    if not cached:
        for file in removed_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    print(f"Deleted '{file}' from the working directory.")
                except OSError as e:
                    print(f"[Error] Could not delete '{file}': {e}")

    # Display the result
    if removed_files:
        print(f"Removed {', '.join(removed_files)} from the staging area.")
    else:
        print("No files were removed.")