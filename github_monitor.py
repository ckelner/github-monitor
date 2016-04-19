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
from github_monitor.github import github

def reconcileGitHubOutsideCollaborators(gh_org):
  gh_org.getAllOrgMembers()

def checkPublicWhitelist(gh_org):
  gh_org.checkPublicWhitelist()

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
  print 'Reconciling outside collaborators...'
  print ''
  gh_org = github(args.k, args.o)
  reconcileGitHubOutsideCollaborators(gh_org)
  print '-' * 50
  print 'Outside collaborators reconciliation complete.'

  print 'Checking for non whitelisted public repositories...'
  print("")
  checkPublicWhitelist(gh_org)
  print '-' * 50
  print 'Whitelist check complete.'

  sys.exit()
