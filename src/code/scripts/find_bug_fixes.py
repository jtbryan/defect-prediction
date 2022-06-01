#!/usr/bin/env python

import os
import json
import re
import argparse
import copy

def find_bug_fixes(issue_path, gitlog_path):

    os.makedirs('bugfixes/', exist_ok=True)

    i = 0 # Used to display progress
    no_matches = []
    matches_per_issue = {}
    total_matches = 0

    # retrieve the issue list
    issue_list = build_issue_list(issue_path)

    with open(gitlog_path) as f:
        gitlog_commits = json.loads(f.read())

    gitlog = []
    for commit in gitlog_commits:
        # create a deep copy of commit so that parents can be removed
        temp_commit = copy.deepcopy(commit)
        del(temp_commit['Parents'])
        gitlog.append(temp_commit)
        for parent in commit['Parents']:
            gitlog.append(parent)

    for id in issue_list:
        # NOTE: split was used to separate JENKINS-XXX in the original version but has been revised
        #nbr = key.split('-')[1]
        nbr = id # issue ID
        matches = []

        for commit in gitlog:
            # Given a string such as ____{price:d}____ ___str___.format(price = 50) can be used to change the value after price to be 50.
            # NOTE: The original pattern used in the example is: pattern = r'JENKINS-{nbr}\D|#{nbr}\D|HUDSON-{nbr}\D'
            pattern = (r'#{nbr}\D').format(nbr=nbr)
            if re.search(pattern, commit['Message']):
                # searches for commits that contain the current issue and contain the keyword 'Fix' or 'fix'
                if re.search(pattern, commit['Message']) \
                    and not re.search('[Ff]ix', commit['Message']):
                    pass
                else:
                    matches.append(commit)
        
        total_matches += len(matches)
        matches_per_issue[id] = len(matches)

        if matches:
            selected_commit = commit_selector_heuristic(matches)
            if not selected_commit:
                no_matches.append(id)
            else:
                issue_list[id]['hash'] = selected_commit['SHA-hash']
                # Original format for Github Date is 2020-11-11 09:56:03-08:00. New format for this will be 2020-11-11 09:56:03
                
                if id == 9796:
                    print(selected_commit['Date'])

                # TODO: Adjust script to account for -08:00 vs +08:00
                if len(selected_commit['Date'].split('-')) > 3 or len(selected_commit['Date'].split('+')) > 1:
                    zero_hour_offset = "+" + selected_commit['Date'][-5:]
                    selected_commit['Date'] = selected_commit['Date'][:-6] + " "
                    zero_hour_offset = zero_hour_offset.replace('-', '')
                    zero_hour_offset = zero_hour_offset.replace(':', '')
                    issue_list[id]['commitdate'] = selected_commit['Date'] + zero_hour_offset
                else:
                    zero_hour_offset = "+0000"
                    issue_list[id]['commitdate'] = selected_commit['Date'] + zero_hour_offset
                '''
                issue_list[id]['hash'] = \
                    re.search('(?<=^commit )[a-z0-9]+(?=\n)', \
                    selected_commit).group(0)
                issue_list[id]['commitdate'] = \
                    re.search('(?<=\nDate:   )[0-9 -:+]+(?=\n)',\
                    selected_commit).group(0)
                '''
        else:
            no_matches.append(id)

        # Progress counter
        i += 1
        if i % 10 == 0:
            print(i, end='\r')

    print('Total issues: ' + str(len(issue_list)))
    print('Issues matched to a bugfix: ' + str(len(issue_list) - len(no_matches)))
    print('Percent of issues matched to a bugfix: ' + \
          str((len(issue_list) - len(no_matches)) / len(issue_list)))
    for key in no_matches:
        issue_list.pop(key)

    return issue_list


def build_issue_list(path):
    """ Helper method for find_bug_fixes """
    '''
    This function creates the issue list of all availabile issues retrieved from the fetch_issues script
    The issue list object is a dictionary that is keyed on the unique ID for each issue and contains a dictionary of the
    creation date and resolution date for the issue
    NOTE: This function has been modifed to instead expect Github issues rather than JIRA
    '''
    issue_list = {}
    with open(path) as f:
        for issue in json.loads(f.read()):
            issue_list[issue['number']] = {}

            created_date = issue['created_at'].replace('T', ' ')
            created_date = created_date.replace('.000', ' ')
            created_date = created_date.replace('Z', ' +0000')

            issue_list[issue['number']]['creationdate'] = created_date

            res_date = issue['closed_at'].replace('T', ' ')
            res_date = res_date.replace('.000', ' ')
            res_date = res_date.replace('Z', ' +0000')

            issue_list[issue['number']]['resolutiondate'] = res_date
    return issue_list

def commit_selector_heuristic(commits):
    """ Helper method for find_bug_fixes.
    Commits are assumed to be ordered in reverse chronological order.
    Given said order, pick first commit that does not match the pattern.
    If all commits match, return newest one. """
    for commit in commits:
        if not re.search('[Mm]erge|[Cc]herry|[Nn]othing', commit['Message']):
            return commit
    return commits[0]

def main():
    """ Main method """
    parser = argparse.ArgumentParser(description="""Identify bugfixes. Use this script together with a
                                                    gitlog.json and a path with issues. The gitlog.json
                                                    is created using the git_log_to_array.py script and
                                                    the issue directory is created and populated using
                                                    the fetch.py script.""")
    parser.add_argument('--gitlog', type=str, required=True,
                        help='Path to json file containing gitlog')
    parser.add_argument('--issue-list', type=str, required=True,
                        help='Path to directory containing issue json files')
    #parser.add_argument('--gitlog-pattern', type=str,
    #                    help='Pattern to match a bugfix')
    args = parser.parse_args()

    issue_list = find_bug_fixes(args.issue_list, args.gitlog)
    with open('bugfixes/issue_list.json', 'w') as f:
        f.write(json.dumps(issue_list, indent=2))

if __name__ == '__main__':
    main()
