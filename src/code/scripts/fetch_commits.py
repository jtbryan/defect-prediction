#!/usr/bin/env python

import argparse
import subprocess
import sys
import json
import os
import git

def git_log_to_json(init_hash, path_to_repo):

    os.makedirs('commits/', exist_ok=True)

    repo = git.Repo(path_to_repo)

    # Typically main would be replaced with master, but in the vagrant repository master is called main
    # list of commits is used for iterating over each commit in chronoligical order, while the dictionary is used for fast looks up of O(1) time
    commits = list(repo.iter_commits("main"))
    commit_dict = {}

    for commit in commits:
        commit_dict[commit.hexsha] = commit

    # list containing all logs that will be json serialized
    json_list = []
    # list of newest commits already found to avoid duplicates
    newest_commits = set()
    # number of commits associated with the repository
    length = len(commits)

    for count, cur_commit in enumerate(commits, 1):
        
        print("%d of %d commits checked" % (count, length), end='\r')
        
        exists = False
        for commit in newest_commits:
            parents = commit.iter_parents()
            if len([parent for parent in parents if cur_commit == parent]) > 0:
                exists = True
                break
        if exists == True: continue
        else: newest_commits.add(cur_commit)

        logs = {'SHA-hash': cur_commit.hexsha, 
                'Author name': cur_commit.author.name, 
                'Author email': cur_commit.author.email, 
                'Date': str(cur_commit.authored_datetime), 
                'Message': cur_commit.message,
                'Parents': []}

        '''
         git rev-list <commit> provides a graph of commits that have revised similar files in reverse chronological order
         Example:
            Commit 3: Changed foo.py & bar.py
            Commit 2: Changed foo.c & and bar.c
            Commit 1: Changed foo.py & bar.java
            In this example, if git rev-list <commit> is used on commit 3, the log will show only commit 3 and commit 1 since they both changed foo.py
        '''

        hashes = subprocess.run(['git', 'rev-list', cur_commit.hexsha], cwd=path_to_repo,
            stdout=subprocess.PIPE).stdout.decode('ascii').split()

        for hash in hashes:
            if hash == cur_commit.hexsha:
                continue
            '''
            git show --quiet --date=iso <commit> provides extra details about a commit (e.g. name, email, commit message, date)
            # NOTE: this was in the original version of this file, but to improve speed this has been swapped to use the git module for Python
            
            entry = subprocess.run(['git', 'show', '--quiet', '--date=iso', hash],
                cwd=path_to_repo, stdout=subprocess.PIPE)\
                .stdout.decode(errors='replace')
            logs[cur_commit].append(entry)
            '''
            if hash in commit_dict:
                child_log = {'SHA-hash': commit_dict[hash].hexsha, 
                             'Author name': commit_dict[hash].author.name, 
                             'Author email': commit_dict[hash].author.email, 
                             'Date': str(commit_dict[hash].authored_datetime), 
                             'Message': commit_dict[hash].message}
                logs['Parents'].append(child_log)
        json_list.append(logs)

    with open('commits/gitlog.json', 'w') as f:
        f.write(json.dumps(json_list, indent=2))
    print('\nTask Completed')

# Commits are saved in reverse chronological order from newest to oldest
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="""Convert a git log output to json.
                                                 """)
    # NOTE: This was in the original version of this script but has been revised to create the graph of every commit
    parser.add_argument('--from-commit', type=str,
            help="A SHA-1 representing a commit. Runs git rev-list from this commit.")
    parser.add_argument('--repo-path', type=str, required=True,
            help="The absolute path to a local copy of the git repository from where the git log is taken.")

    args = parser.parse_args()
    path_to_repo = args.repo_path
    init_hash = args.from_commit
    git_log_to_json(init_hash, path_to_repo)

