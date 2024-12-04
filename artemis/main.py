import argparse
import os
import sys
from artemis import repo, staging

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

    return parser.parse_args()


def main():
    args = parse_args()

    if args.command == 'init':
        repo.init_repository()

    elif args.command == 'status':
        repo.status()

    elif args.command == 'add':
        staging.artemis_add(args.files)

if __name__ == '__main__':
    main()