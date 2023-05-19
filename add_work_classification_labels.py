import csv
import sys
import configparser
import getpass
from work_exposure.jira import jira_api


if (len(sys.argv) != 2):
    print('Expect one command-line argument with the path to the CSV file name with JIRA issues and label to add to the issue')
    sys.exit(-1)

config_filename = 'worklog_based_export.ini'
config = configparser.ConfigParser()

successfully_read_file = config.read(config_filename)
if not successfully_read_file:
    print("Couldn't find config file " + config_filename)
    print('See README.md for details about the format and content')
    sys.exit(-2)

jira_base_url = config['jira']['jiraBaseUrl']
jira_user = config['jira']['jiraUser']

jira_password = getpass.getpass("Jira password (api token): ")

jira_api = jira_api.JiraApi(baseUrl=jira_base_url,user=jira_user,password=jira_password)

with open(sys.argv[1], 'rt') as f:
    csv_reader = csv.reader(f, delimiter='|')
    header = True
    for row in csv_reader:
        if (header):
            if (len(row) != 3):
                print('Expected 3 header values. Expected: issueKey|description|label but got '+ '|'.join(row))
                sys.exit(-3)
            elif (row[0] != 'issueKey' or row[1] != 'description' or row[2] != 'label'):
                print('Unexpected header values. Expected: issueKey|description|label but got '+ '|'.join(row))
                sys.exit(-4)
            header = False
        else:
            if (len(row) != 3):
                print('Expected 3 values. Expected: issueKey|description|label but got '+ '|'.join(row))
                sys.exit(-5)
            issue_key = row[0]
            label = row[2]
            print('Add label ' + label + ' to issue ' + issue_key)
            jira_api.addLabel(issueId=issue_key, labelValue=label)
