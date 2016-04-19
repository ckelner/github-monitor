import requests
import json
import sys

class github(object):
  """Provides wrapper for querying the GitHub Org.
  Attributes:
    token: A personal access token with read privileges
    org: The GitHub organization to interact with
  """
  OK = 200
  PRIVATE_JSON_KEY = 'private'
  FORK_JSON_KEY = 'fork'
  FULL_NAME_JSON_KEY = 'full_name'
  REPO_WHITELIST_FILENAME = 'public_whitelist.json'

  def __init__(self, token, org):
    """Return a GitHub object configured with *token* and *org*."""
    self.HEADERS = {
        'Content-Type': 'application/json',
        'Authorization': 'token %s' % token,
        'Accept': 'application/vnd.github.ironman-preview+json'
    }
    self.token = token
    self.org = org
    self.github_url_members_list = 'https://api.github.com/orgs/%s/members' % org
    self.github_url_repos_list = 'https://api.github.com/orgs/%s/repos' % org

  @staticmethod
  def parseGitHubLinkHeader(links):
    next_link = None
    for link in links:
      if link.find('next') != -1:
        # format:
        # <https://api.github.com/organizations/2650031/members?filter=2fa_disabled&page=2>;
        # rel="next"
        next_link = link.split(';')[0].replace('<', '').replace('>', '')
    return next_link

  def githubGet(self, url, data=[]):
    response = requests.get(url, headers=self.HEADERS)
    if response.status_code is not self.OK:
      sys.exit(formatInvalidHttpStatusMessage(url, str(response.status_code)))
    response_json = response.json()
    link = None
    try:
      if 'link' in response.headers:
        link = self.parseGitHubLinkHeader(response.headers['link'].split(','))
    except KeyError:
      pass
    if response.status_code is self.OK:
      data = data + response_json
    if link != None:
      return self.githubGet(link, data)
    else:
      return data

  def getAllOrgMembers(self):
    print 'Getting all members of %s org...' % self.org
    all_members = self.githubGet(self.github_url_members_list,[])
    # @ckelner: build set -- per @tmulhern3 faster!  Science!
    members = set()
    for member_json in all_members:
      members.add(member_json['login'])
    return members

  def parsePublicWhitelist(self):
    whitelist_set = set()
    try:
      with open(self.REPO_WHITELIST_FILENAME) as json_file:
        json_data = json.load(json_file)
        for name in json_data.get(self.FULL_NAME_JSON_KEY):
          whitelist_set.add(name)

        return whitelist_set
    except IOError:
      sys.exit(formatIOError())

  def checkPublicWhitelist(self):
    whitelist_set = self.parsePublicWhitelist()
    for repo in self.githubGet(self.github_url_repos_list):
      if repo.get(self.PRIVATE_JSON_KEY) == False and repo.get(self.FORK_JSON_KEY) == False and not repo.get(self.FULL_NAME_JSON_KEY) in whitelist_set:
        # TODO: Send email notifying user
        print 'REPO \'' + repo.get(self.FULL_NAME_JSON_KEY) + ' SHOULD BE PRIVATE'
