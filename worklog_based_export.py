from datetime import datetime
from queue import Empty
from zoneinfo import ZoneInfo
from typing import Dict
from typing import List
import configparser
import getpass
import sys
from work_exposure import plantuml
from work_exposure.jira import jira_api
from work_exposure.jira import jira_worklog_based_export_time_by_epic
from work_exposure.jira import jira_worklog_based_export_time_by_worktype
from work_exposure.jira import jira_worklog_based_export_cycletime_by_epic
from work_exposure.jira import jira_worklog_based_exporter
from work_exposure.domain import epic_overview
from work_exposure.domain import worktype_overview
from work_exposure.plantuml import gantt_diagram_exporter

# between which dates do we want to export data.

configFileName = 'worklog_based_export.ini'
config = configparser.ConfigParser()

successfullyReadFileNames = config.read(configFileName)
if not successfullyReadFileNames:
    print("Couldn't find config file " + configFileName)
    print('See README.md for details about the format and content')
    sys.exit(-1)

fromDate = datetime.fromisoformat(config['DEFAULT']['fromDate'])
toDate = datetime.fromisoformat(config['DEFAULT']['toDate'])

jiraBaseUrl = config['jira']['jiraBaseUrl']
jiraUser = config['jira']['jiraUser']
work_classification_prefix = config['jira']['workClassificationPrefix']

jiraPassword = getpass.getpass("Jira password (api token): ")

jiraApi = jira_api.JiraApi(baseUrl=jiraBaseUrl,user=jiraUser,password=jiraPassword)
workLogItemIds = jiraApi.getUpdatedWorklogIdsSince(fromDate)
jiraWorkLogItems = jiraApi.getWorkLogItems(worklogItemIds = workLogItemIds, toDate = toDate)
jiraIssues:Dict[str,jira_api.JiraIssue] = {}

exportByEpic = jira_worklog_based_export_time_by_epic.JiraExportTimeByEpic(jiraApi=jiraApi, fromDate=fromDate, toDate=toDate)
exportByWorktype = jira_worklog_based_export_time_by_worktype.JiraExportTimeByWorkType(jiraApi=jiraApi, fromDate=fromDate, toDate=toDate, work_classification_prefix=work_classification_prefix)
exportCycletimeByEpic = jira_worklog_based_export_cycletime_by_epic.JiraExportCycleTimeByEpic(jiraApi=jiraApi, fromDate=fromDate, toDate=toDate)

exporters:List[jira_worklog_based_exporter.JiraExporter] = [exportByEpic, exportByWorktype, exportCycletimeByEpic]


index = 0
for jiraWorkLogItem in jiraWorkLogItems:
    index += 1
    print('Processing JiraWorklogItem', index, 'from', len(jiraWorkLogItems))
    jiraIssue = jiraIssues.get(jiraWorkLogItem.issueId)
    if (jiraIssue == None):
        print('Get JiraIssue', jiraWorkLogItem.issueId)
        jiraIssue = jiraApi.getIssue(jiraWorkLogItem.issueId)
        jiraIssues[jiraWorkLogItem.issueId] = jiraIssue

    for exporter in exporters:
        exporter.process(worklogItem=jiraWorkLogItem, issue=jiraIssue)

for exporter in exporters:
    exporter.exportToFiles()

