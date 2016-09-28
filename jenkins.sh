#!/bin/bash
# Author: @ckelner
# init: 2016/09/28
# to be run from Jenkins

set +x
a_key=$(awk -F "=" '/access_key/ {print $2;exit}' /var/lib/jenkins/.grid-auth/prod/prod-v1-grid-auth.ini | tr -d ' ') > /dev/null 2>&1
s_key=$(awk -F "=" '/secret_access_key/ {print $2;exit}' /var/lib/jenkins/.grid-auth/prod/prod-v1-grid-auth.ini | tr -d ' ') > /dev/null 2>&1
source /var/lib/jenkins/.github_token > /dev/null 2>&1
python github_monitor.py -k $AUTOMATION_GITHUB_TOKEN -o TheWeatherCompany -aws_secret_access_key $s_key -aws_access_key_id $a_key -email_list grid-team@weather.com -l 1650 -n 75

### DEMO RUN BELOW
#python github_monitor.py -k $AUTOMATION_GITHUB_TOKEN -o TheWeatherCompany -aws_secret_access_key $s_key -aws_access_key_id $a_key -email_list #tim.mulhern.contractor@weather.com -l 1200 -n 500 -s
