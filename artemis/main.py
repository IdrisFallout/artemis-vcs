import argparse
import pkg_resources
from artemis import repo


def main():
    """
    Main entry point for the Artemis command-line tool.
    """
    parser = argparse.ArgumentParser(description="Artemis Repository Management")

    # Add version argument to show version info
    parser.add_argument('--version', action='version', version=f"%(prog)s {get_version()}")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Initialize a new Artemis repository")
    subparsers.add_parser("is-repo", help="Check if the current directory is an Artemis repository")
    subparsers.add_parser("get-head", help="Show the current branch or detached HEAD")
    subparsers.add_parser("list-branches", help="List all branches")

    branch_parser = subparsers.add_parser("create-branch", help="Create a new branch")
    branch_parser.add_argument("branch_name", type=str, help="Name of the branch to create")

    args = parser.parse_args()

    if args.command == "init":
        repo.init()
    elif args.command == "is-repo":
        print("Is this a repo?", repo.is_repo())
    elif args.command == "get-head":
        print("Current HEAD:", repo.get_head())
    elif args.command == "list-branches":
        repo.list_branches()
    elif args.command == "create-branch":
        repo.create_branch(args.branch_name)
    else:
        print("Unknown command. Use --help for options.")


def get_version():
    """
    Fetches the version from the installed package.
    """
    try:
        return pkg_resources.get_distribution("artemis-vcs").version
    except pkg_resources.DistributionNotFound:
        return "Unknown"


if __name__ == "__main__":
    main()
