import argparse
from pygit2 import Repository
import git
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo_path', type=str, required=True,
                    help='The relative or absolute path to the cloned repository.')
    
    args = parser.parse_args()

    repo = git.Repo(args.repo_path)

    main = Repository(args.repo_path).head.shorthand

    commits = list()

    commits.extend(list(repo.iter_commits(main)))
    print("\n")
    print(f"Original commit date: {commits[-1].committed_datetime}")
    print(f"Commit hex: {commits[-1].hexsha}")
    print("\n")
