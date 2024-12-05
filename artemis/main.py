import argparse

from artemis import repo, staging, commit


def parse_args():
    parser = argparse.ArgumentParser(description="A simple Artemis repository management CLI")

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # init command
    subparsers.add_parser('init', help='Initialize a new repository')

    # status command
    subparsers.add_parser('status', help='Show the working tree status')

    # add command with file arguments
    add_parser = subparsers.add_parser('add', help='Add file contents to the index')
    add_parser.add_argument('files', nargs='+', help="List of files to add")

    # remove command with file arguments
    remove_parser = subparsers.add_parser('rm', help='Remove files from the index')
    remove_parser.add_argument('files', nargs='+', help="List of files to remove")
    remove_parser.add_argument(
        '--cached',
        action='store_true',
        help="Remove files only from the staging area, not from the working directory"
    )

    # implement commit -m command
    commit_parser = subparsers.add_parser('commit', help='Record changes to the repository')
    commit_parser.add_argument('-m', '--message', required=True, help='Commit message')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == 'init':
        repo.init_repository()

    elif args.command == 'status':
        repo.status()

    elif args.command == 'add':
        staging.artemis_add(args.files)

    elif args.command == 'rm':
        staging.remove_files(args.files, cached=args.cached)

    elif args.command == 'commit':
        commit.commit(args.message)

if __name__ == '__main__':
    main()