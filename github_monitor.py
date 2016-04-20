#!/usr/bin/env python
##############################################################################
# Looks at a GitHub organization's:
#   - Outside collaborators
#   - Public Source (non-fork) repositories
#   - Organization Billing
# Fires email if:
#   - collaborators or repos are found that are not in whitelist files
#   - number of used private repos is within certain limit of organization plan
# Author: @ckelner & @tmulhern3
# Init: 2016.04.19
##############################################################################

import argparse
import sys
import json
import compileall
from tqdm import tqdm
from github_monitor.github import github
from github_monitor.amazon import amazon
from github_monitor.custom_exceptions import GitHubHTTPException

REPO_WHITELIST_FILENAME = 'public_repos_whitelist.json'
OUTSIDE_COLLABORATORS_WHITELIST_FILENAME = 'outside_collaborators_whitelist.json'
ERRORS = []
EMAIL_BODY = 'The following issues were found in the TWC GitHub Org:\n\n'

def reconcileGitHubOutsideCollaborators(gh_org, skip, debug):
  global ERRORS
  global EMAIL_BODY
  if skip is False:
    print 'Reconciling outside collaborators...'
    outside_collabs = set()
    # @ckelner: more DRY? better way?
    try:
      members = gh_org.getAllOrgMembers() #set
    except GitHubHTTPException as e:
      ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling github.getAllOrgMembers")
    try:
      repos = gh_org.getAllOrgRepos() #dict
    except GitHubHTTPException as e:
      ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling github.getAllOrgRepos")
    try:
      whitelist = parseWhitelist(OUTSIDE_COLLABORATORS_WHITELIST_FILENAME)
    # @ckelner: not try... but need to capture to error to send via email
    except IOError as e:
      # @ckelner: a bit fugly... but considering we send it via email should be slightly helpful?
      # TODO: Improve?
      ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling parseWhitelist")
      return
    except ValueError as e:
      ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling parseWhitelist")
      return
    print 'Processing GitHub Repos for outside collaborators...'
    first_find = True
    if debug:
      print 'In debug mode, setting false data, skipping calling all repos...'
      outside_collabs.add('debug-test-user')
    else:
      for repo in tqdm(repos):
        repo_collaborators = gh_org.getCollaboratorsForRepo(repo)
        if repo_collaborators is not None and len(repo_collaborators) != 0:
          for collaborator in repo_collaborators:
            if collaborator['login'] not in members:
              if collaborator['login'] not in outside_collabs:
                outside_collabs.add(collaborator['login'])
    for collab in outside_collabs:
      if collab not in whitelist:
        if first_find:
          first_find = False
          EMAIL_BODY += 'Outside Collaborators not in whitelist:\n'
        EMAIL_BODY += '- %s\n' % collab
    if first_find is False:
      EMAIL_BODY += '\nPlease remove the collaborators for the TWC Org.\n\n'
  else:
    print 'Skipping reconciling outside collaborators'

def checkPublicSourceReposAgainstWhitelist(gh_org, skip):
  global ERRORS
  global EMAIL_BODY
  if skip is False:
    print 'Checking for public repositories...'
    try:
      publicSourceRepos = gh_org.getPublicSourceRepos()
    except GitHubHTTPException as e:
      ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling github.getAllOrgRepos")
      return
    try:
      whitelist = parseWhitelist(REPO_WHITELIST_FILENAME)
    except IOError as e:
      ERRORS.append(str(e) + " -- during execution of checkPublicSourceReposAgainstWhitelist while calling parseWhitelist")
      return
    except ValueError as e:
      ERRORS.append(str(e) + " -- during execution of checkPublicSourceReposAgainstWhitelist while calling parseWhitelist")
      return
    for repo in publicSourceRepos:
      if repo not in whitelist:
        # TODO: add to email body
        print repo
  else:
    print 'Skipping check for publics repositories'

# can throw: ValueError
# can throw: IOError
def parseWhitelist(which_list):
  whitelist_set = set()
  # @ckelner 04/20: Handle file exceptions in calling method, pass error back via email
  with open(which_list) as json_file:
    json_data = json.load(json_file)
    for data in json_data.get('data'):
      whitelist_set.add(data)
  return whitelist_set

def handleErrors(debug):
  global EMAIL_BODY
  if debug:
    print '# of errors while running script: %s' % str(len(ERRORS))
  if len(ERRORS) is not 0 and ERRORS is not None:
    EMAIL_BODY = 'There were errors while reconciling GitHub.\n'
    EMAIL_BODY += '\nThe errors are as follows: \n'
    for err in ERRORS:
      EMAIL_BODY += '- %s\n' % err
    EMAIL_BODY += 'Please investigate.\n'

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
  description='Reconcile GitHub outside collaborators and public repos against \
    whitelists, and monitors billing for number of repos.  Alerts on conditions \
    where collaborators or repos are found that aren not in whitelists or if \
    number of repos is within organization plan limit')
  parser.add_argument('-k', '-key', help='The GitHub token(key) to use to talk to the API',
    required=True)
  parser.add_argument('-o', '-org', help='The Org name in GitHub', required=True)
  parser.add_argument('-aws_access_key_id', help='The access key id for AWS', required=True)
  parser.add_argument('-aws_secret_access_key', help='The secret access key for AWS', required=True)
  parser.add_argument('-email_list', help='CSV of emails to send to', required=True)
  parser.add_argument('-s', '-skip_outside_collab', help='Skips checking outside collaborators',
    action='store_true', default=False)
  parser.add_argument('-p', '-skip_public_repos', help='Skips checking publics repos',
    action='store_true', default=False)
  parser.add_argument('-d', '-debug', help='Enables debug mode for development',
    action='store_true', default=False)
  args = parser.parse_args()
  compileall.compile_dir('github_monitor/', force=True)
  aws_ses = amazon(args.aws_access_key_id, args.aws_secret_access_key, args.email_list)
  gh_org = github(args.k, args.o)
  if args.d:
    print '!' * 25
    print '---- In debug mode ----'
    print '!' * 25
  reconcileGitHubOutsideCollaborators(gh_org, args.s, args.d)
  checkPublicSourceReposAgainstWhitelist(gh_org, args.p)
  handleErrors(args.d)
  if args.d:
    print 'DEBUG: printing email body:\n'
    print EMAIL_BODY
  # TODO: add email call
  # TODO: GitHub Billing
  print 'Reconciliation complete.'
  print '-' * 50
  sys.exit()
