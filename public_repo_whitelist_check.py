import requests
import json
import sys

# Scan public repos for TWC Org and compare to a whitelist,
# send email if they are entries that are not in the whitelist


ORG_NAME = 'TheWeatherCompany'
GITHUB_BASE_URL = 'https://api.github.com'
GITHUB_ORGS_URL = 'orgs'
GITHUB_REPOS_URL = 'repos'

WHITELIST_FILENAME = 'public_whitelist.json'

PRIVATE_JSON_KEY = 'private'
FULL_NAME_JSON_KEY = 'full_name'

SUCCESS = 'SUCCESS'

OK = 200

def formatOrgRepoGetURL(org_name): return (GITHUB_BASE_URL + '/' +
  GITHUB_ORGS_URL + '/' + org_name + '/' + GITHUB_REPOS_URL)
def formatInvalidHttpStatusMessage(url, status_code): return ('ERROR: Did ' +
  'not recieve 200 OK from ' + url + '\nReceived ' + status_code + ' instead')
def formatIOError(): return "ERROR: Could not open file " + WHITELIST_FILENAME

def queryGitHubAPI(url):
  response = requests.get(url)
  resp_json = json.loads(response.content)
  if response.status_code is not OK:
    sys.exit(formatInvalidHttpStatusMessage(url, str(response.status_code)))

  return resp_json

def parseWhitelist():
  whitelist_set = set()
  try:
    with open(WHITELIST_FILENAME) as json_file:
      json_data = json.load(json_file)
      for name in json_data.get(FULL_NAME_JSON_KEY):
	    whitelist_set.add(name)

      return whitelist_set
  except IOError:
    sys.exit(formatIOError())


def checkWhitelist(all_repos):
  whitelist_set = parseWhitelist()
  for repo in all_repos:
    if repo.get(PRIVATE_JSON_KEY) == False and not repo.get(FULL_NAME_JSON_KEY) in whitelist_set:
      # TODO: Send email notifying user
      print 'REPO \'' + repo.get(FULL_NAME_JSON_KEY) + ' SHOULD BE PRIVATE'

checkWhitelist(queryGitHubAPI(formatOrgRepoGetURL(ORG_NAME)))
print SUCCESS
