# GitHub monitor

A little script to monitor certain scenarios in GitHub and alert on them via email.

Monitors in place are:
- Public source repositories not in a whitelist
- Outside collaborators not in a whitelist
- Number of private repositories near organization limit

Whitelists are defined in files:
- `outside_collaborators_whitelist.json`
- `public_repos_whitelist.json`

The GitHub Org limit and billing information is not available from the GitHub API (v3), so this value is defined via command line arguement.

# Setup

Required:
- python 2.7.9

Run `setup.sh` which will install the necessary python packages.

# Running

```
$ python github_monitor.py -h
usage: github_monitor.py [-h] -k K -o O -l L -n N -aws_access_key_id
                         AWS_ACCESS_KEY_ID -aws_secret_access_key
                         AWS_SECRET_ACCESS_KEY -email_list EMAIL_LIST [-s]
                         [-p] [-c] [-d]

Reconcile GitHub outside collaborators and public repos against whitelists,
and monitors billing for number of repos. Alerts on conditions where
collaborators or repos are found that are not in whitelists or if the number
of repos is within organization plan limit

optional arguments:
  -h, --help            show this help message and exit
  -k K, -key K          The GitHub token(key) to use to talk to the API
  -o O, -org O          The Org name in GitHub
  -l L, -private_repo_limit L
                        The private repo limit for the GitHub org
  -n N, -private_repo_alert_value N
                        The diff between the -l flag value (upper bound
                        private repo limit) and the actual private repo limit
                        count
  -aws_access_key_id AWS_ACCESS_KEY_ID
                        A access key id for AWS to send email via SES
  -aws_secret_access_key AWS_SECRET_ACCESS_KEY
                        A secret access key for AWS to send email via SES
  -email_list EMAIL_LIST
                        CSV of emails to send alerts to
  -s, -skip_outside_collab
                        Skips checking outside collaborators
  -p, -skip_public_repos
                        Skips checking publics repos
  -c, -skip_private_repo_count
                        Skips checking private repo count
  -d, -debug            Enables debug mode for development
```
