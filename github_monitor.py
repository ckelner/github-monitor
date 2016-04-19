#!/usr/bin/env python
##############################################################################
# Looks at the organization's outside collaborators list and compares it to
# the local outside_collaborators_whitelist.json and sends an email if any
# outside collaborator is found that isn't in the whitelist
# Author: @ckelner
# Init: 2016.04.19
##############################################################################

import argparse
import sys
import json
import compileall

from github_monitor.github import github

def reconcileGitHub(gh_org):
  gh_org.getAllOrgMembers()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
  description='Reconcile GitHub outside collaborators against a whitelist, \
      "outside_collaborators_whitelist.json" and send email alert if entity \
      found in GitHub Org but not in whitelist.')
  parser.add_argument('-k', '-key', help='The GitHub token(key) to use to talk to the API',
      required=True)
  parser.add_argument('-o', '-org', help='The Org name in GitHub', required=True)
  args = parser.parse_args()
  compileall.compile_dir('github_monitor/', force=True)
  print('Reconciling outside collaborators...')
  print("")
  gh_org = github(args.k, args.o)
  reconcileGitHub(gh_org)
  print '-' * 50
  print 'Reconciliation complete.'
  sys.exit()
