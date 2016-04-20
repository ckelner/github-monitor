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

def reconcileGitHubOutsideCollaborators(gh_org, skip):
  if skip is False:
    print 'Reconciling outside collaborators...'
    # @ckelner: more DRY? better way?
    gh_errs = False
    try:
      members = gh_org.getAllOrgMembers() #set
    except GitHubHTTPException as e:
      print e
      ERRORS = ERRORS + e
      gh_errs = True
    try:
      repos = gh_org.getAllOrgRepos() #dict
    except GitHubHTTPException as e:
      print e
      ERRORS = ERRORS + e
      gh_errs = True
    if gh_errs is False:
      print 'Processing GitHub Repos for outside collaborators...'
      for repo in tqdm(repos):
        repo_collaborators = gh_org.getCollaboratorsForRepo(repo)
        if repo_collaborators is not None and len(repo_collaborators) != 0:
          for collaborator in repo_collaborators:
            if collaborator['login'] not in members:
              print 'Found outside collaborator %s' % collaborator['login']
      # TODO: parse in whitelist
      # TODO: add to email body
  else:
    print 'Skipping reconciling outside collaborators'

def checkPublicSourceReposAgainstWhitelist(gh_org, skip):
  if skip is False:
    print 'Checking for public repositories...'
    gh_errs = False
    try:
      publicSourceRepos = gh_org.getPublicSourceRepos()
    except GitHubHTTPException as e:
      print e
      ERRORS = ERRORS + e
      gh_errs = True
    if gh_errs is False:
      whitelist = parseWhitelist(REPO_WHITELIST_FILENAME)
      for repo in publicSourceRepos:
        if repo not in whitelist:
          # TODO: add to email body
          print repo
  else:
    print 'Skipping check for publics repositories'

def parseWhitelist(which_list):
  whitelist_set = set()
  try:
    with open(which_list) as json_file:
      json_data = json.load(json_file)
      for data in json_data.get('data'):
        whitelist_set.add(data)
      return whitelist_set
  except IOError:
    sys.exit(formatIOError())

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
  args = parser.parse_args()
  compileall.compile_dir('github_monitor/', force=True)
  aws_ses = amazon(args.aws_access_key_id, args.aws_secret_access_key, args.email_list)
  gh_org = github(args.k, args.o)
  reconcileGitHubOutsideCollaborators(gh_org, args.s)
  checkPublicSourceReposAgainstWhitelist(gh_org, args.p)
  # TODO: handle ERRORS
  # TODO: add email call
  # TODO: GitHub Billing
  print 'Reconciliation complete.'
  print '-' * 50
  sys.exit()
