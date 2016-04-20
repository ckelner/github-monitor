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

# TODO: some weird return values here-in for some of the methods.  Python-fu is
# weak -- do some research on how to better handle multiple returns values?

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
EMAIL_SUBJECT = 'Attn: TWC GitHub Org Issues detected!'

def reconcileGitHubOutsideCollaborators(gh_org, repos, skip, debug):
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
      return 1
    try:
      whitelist = parseWhitelist(OUTSIDE_COLLABORATORS_WHITELIST_FILENAME)
    # @ckelner: not try... but need to capture to error to send via email
    except IOError as e:
      # @ckelner: a bit fugly... but considering we send it via email should be slightly helpful?
      # TODO: Improve?
      ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling parseWhitelist")
      return 1
    except ValueError as e:
      ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling parseWhitelist")
      return 1
    print 'Processing GitHub Repos for outside collaborators...'
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
    first_find = True
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
    return 0

def checkPublicSourceReposAgainstWhitelist(gh_org, repos, skip):
  global ERRORS
  global EMAIL_BODY
  if skip is False:
    print 'Checking for public repositories...'
    try:
      publicSourceRepos = getPublicSourceRepos(repos)
    except GitHubHTTPException as e:
      ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling github.getAllOrgRepos")
      return 1
    try:
      whitelist = parseWhitelist(REPO_WHITELIST_FILENAME)
    except IOError as e:
      ERRORS.append(str(e) + " -- during execution of checkPublicSourceReposAgainstWhitelist while calling parseWhitelist")
      return 1
    except ValueError as e:
      ERRORS.append(str(e) + " -- during execution of checkPublicSourceReposAgainstWhitelist while calling parseWhitelist")
      return 1
    first_find = True
    for repo in publicSourceRepos:
      if repo not in whitelist:
        if first_find:
          first_find = False
          EMAIL_BODY += 'Public Source Repos not in whitelist:\n'
        EMAIL_BODY += '- %s\n' % repo
    if first_find is False:
      EMAIL_BODY += '\nPlease contact the owners of these repos.\n\n'
  else:
    print 'Skipping check for publics repositories'
    return 0

def checkPrivateRepoCount(repos, limit, diff, skip):
  global ERRORS
  global EMAIL_BODY
  if skip is False:
    count = 0
    for repo in repos:
      if repo['private'] is True and repo['fork'] is False:
        count += 1
    if count >= (int(limit) - int(diff)):
      EMAIL_BODY += 'Private repository count is %s; Limit passed to script is %s.  ' % (count, limit)
      EMAIL_BODY += 'The allowable difference is %s, please update your billing tier in GitHub ASAP.' % diff
      return True
    else:
      return False
  else:
    print 'Skipping check for private repository count'
    return 0

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

def getAllOrgRepos(gh_org):
  try:
    return gh_org.getAllOrgRepos() #dict
  except GitHubHTTPException as e:
    ERRORS.append(str(e) + " -- during execution of reconcileGitHubOutsideCollaborators while calling github.getAllOrgRepos")
    return 1

def getPublicSourceRepos(repos):
  public_repos = set()
  for repo in repos:
    if repo['private'] is False and repo['fork'] is False:
      public_repos.add(repo['full_name'])
  return public_repos

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
  description='Reconcile GitHub outside collaborators and public repos against \
    whitelists, and monitors billing for number of repos.  Alerts on conditions \
    where collaborators or repos are found that are not in whitelists or if the \
    number of repos is within organization plan limit')
  parser.add_argument('-k', '-key', help='The GitHub token(key) to use to talk to the API',
    required=True)
  parser.add_argument('-o', '-org', help='The Org name in GitHub', required=True)
  parser.add_argument('-l', '-private_repo_limit', help='The private repo limit \
    for the GitHub org', required=True)
  parser.add_argument('-n', '-private_repo_alert_value', help='The diff between the \
    -l flag value (upper bound private repo limit) and the actual private repo limit count',
    required=True)
  parser.add_argument('-aws_access_key_id', help='A access key id for AWS to send email via SES',
    required=True)
  parser.add_argument('-aws_secret_access_key', help='A secret access key for AWS to send email via SES',
    required=True)
  parser.add_argument('-email_list', help='CSV of emails to send alerts to', required=True)
  parser.add_argument('-s', '-skip_outside_collab', help='Skips checking outside collaborators',
    action='store_true', default=False)
  parser.add_argument('-p', '-skip_public_repos', help='Skips checking publics repos',
    action='store_true', default=False)
  parser.add_argument('-c', '-skip_private_repo_count', help='Skips checking private repo count',
    action='store_true', default=False)
  parser.add_argument('-d', '-debug', help='Enables debug mode for development',
    action='store_true', default=False)
  args = parser.parse_args()
  compileall.compile_dir('github_monitor/', force=True)
  aws_ses = Amazon(args.aws_access_key_id, args.aws_secret_access_key, args.email_list,
    'grid-team@weather.com')
  gh_org = github(args.k, args.o)
  if args.d:
    print '!' * 25
    print '---- In debug mode ----'
    print '!' * 25
  repos = getAllOrgRepos(gh_org)
  if repos is not 1:
    reconcileGitHubOutsideCollaborators(gh_org, repos, args.s, args.d)
    checkPublicSourceReposAgainstWhitelist(gh_org, repos, args.p)
    checkPrivateRepoCount(repos, args.l, args.n, args.c)
  else:
    print 'Skipping checks, there was an error getting the GitHub organization repos'
  handleErrors(args.d)
  if args.d:
    print 'DEBUG: printing email body:\n'
    print '-' * 50
    print ''
    print EMAIL_BODY
    print ''
    print '-' * 50
  aws_ses.send(EMAIL_SUBJECT, EMAIL_BODY)
  print 'Reconciliation complete.'
  print '-' * 50
  sys.exit()
