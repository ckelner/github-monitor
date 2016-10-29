import requests
import json
import sys
from custom_exceptions import GitHubHTTPException

class github(object):
  """Provides wrapper for querying the GitHub Org.
  Attributes:
    token: A personal access token with read privileges
    org: The GitHub organization to interact with
  """
  OK = 200
  FORBIDDEN = 403

  def __init__(self, token, org):
    """Return a GitHub object configured with *token* and *org*."""
    self.HEADERS = {
        'Content-Type': 'application/json',
        'Authorization': 'token %s' % token,
        'Accept': 'application/vnd.github.ironman-preview+json'
    }
    self.token = token
    self.org = org
    self.github_api_endpoint = 'https://api.github.com'
    self.github_url_members_list = '%s/orgs/%s/members' % (self.github_api_endpoint, org)
    self.github_url_repos_list = '%s/orgs/%s/repos' % (self.github_api_endpoint, org)

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
  
  @staticmethod
  def printRateLimit(response):
    print "Rate limit remaining: " + response.headers["X-RateLimit-Remaining"]
    print "Rate limit reset: " + time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(float(response.headers["X-RateLimit-Reset"])))
    print "Current UTC time: " + time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())

  def formatInvalidHttpStatusMessage(self, url, status_code):
    return ('ERROR: Did not recieve 200 OK from ' + url + '\nReceived ' +
      str(status_code) + ' instead')

  def githubGet(self, url, data=[]):
    response = requests.get(url, headers=self.HEADERS)
    self.printRateLimit(response)
    if response.status_code is not self.OK:
      print 'Recieved non-200 response code: %s' % response.status_code
      #kelnerhax - deal with it
      if response.status_code is self.FORBIDDEN:
        print response.json()
        print '!INVESTIGATE! 403 while querying %s' % url
        print 'Data dump:'
        print json.dumps(json.loads(data), indent=4, sort_keys=True)
      else: 
        raise GitHubHTTPException(self.formatInvalidHttpStatusMessage(url, response.status_code))
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

  def getAllOrgRepos(self):
    print 'Getting all repos for %s org...' % self.org
    return self.githubGet(self.github_url_repos_list)

  def getCollaboratorsForRepo(self, repo):
    #/repos/:owner/:repo/collaborators
    url = '%s/repos/%s/%s/collaborators' % (self.github_api_endpoint, self.org, repo['name'])
    return self.githubGet(url)
