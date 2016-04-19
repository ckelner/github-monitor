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

def reconcileGitHubOutsideCollaborators(gh_org):
  print 'Reconciling outside collaborators...'
  members = gh_org.getAllOrgMembers() #set
  repos = gh_org.getAllOrgRepos() #dict
  print 'Processing GitHub Repos for outside collaborators...'
  for repo in tqdm(repos):
    repo_collaborators = gh_org.getCollaboratorsForRepo(repo)
    if repo_collaborators is not None and len(repo_collaborators) != 0:
      for collaborator in repo_collaborators:
        if collaborator['login'] not in members:
          print 'Found outside collaborator %s' % collaborator['login']
  # TODO: parse in whitelist
  # TODO: send email
  print '-' * 50
  print 'Outside collaborators reconciliation complete.'

def checkPublicWhitelist(gh_org):
  print 'Checking for non whitelisted public repositories...'
  gh_org.checkPublicWhitelist()
  print '-' * 50
  print 'Whitelist check complete.'

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
  description='Reconcile GitHub outside collaborators and public repos against \
    whitelists, and monitors billing for number of repos.  Alerts on conditions \
    where collaborators or repos are found that aren not in whitelists or if \
    number of repos is within organization plan limit')
  parser.add_argument('-k', '-key', help='The GitHub token(key) to use to talk to the API',
    required=True)
  parser.add_argument('-o', '-org', help='The Org name in GitHub', required=True)
  args = parser.parse_args()
  compileall.compile_dir('github_monitor/', force=True)
  gh_org = github(args.k, args.o)
  reconcileGitHubOutsideCollaborators(gh_org)
  checkPublicWhitelist(gh_org)

  sys.exit()
