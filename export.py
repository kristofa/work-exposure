from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict
from typing import List
from value_stream_mapping import plantuml
from value_stream_mapping.jira import jira_api
from value_stream_mapping.jira import jira_export_time_by_epic
from value_stream_mapping.jira import jira_export_time_by_worktype
from value_stream_mapping.jira import jira_export_cycletime_by_epic
from value_stream_mapping.jira import jira_exporter
from value_stream_mapping.domain import epic_overview
from value_stream_mapping.domain import worktype_overview
from value_stream_mapping.plantuml import gantt_diagram_exporter

# between which dates do we want to export data.
fromDate = datetime(2021, 10, 1, tzinfo=ZoneInfo("Europe/Brussels"))
toDate = datetime(2022,4,15, tzinfo=ZoneInfo("Europe/Brussels"))

jiraApi = jira_api.JiraApi(baseUrl='https://company.atlassian.net/',user='user@company.com',password='userToken')
workLogItemIds = jiraApi.getUpdatedWorklogIdsSince(fromDate)
jiraWorkLogItems = jiraApi.getWorkLogItems(worklogItemIds = workLogItemIds, toDate = toDate)
jiraIssues:Dict[str,jira_api.JiraIssue] = {}

exportByEpic = jira_export_time_by_epic.JiraExportTimeByEpic(jiraApi=jiraApi, fromDate=fromDate, toDate=toDate)
exportByWorktype = jira_export_time_by_worktype.JiraExportTimeByWorkType(jiraApi=jiraApi, fromDate=fromDate, toDate=toDate)
exportCycletimeByEpic = jira_export_cycletime_by_epic.JiraExportCycleTimeByEpic(jiraApi=jiraApi, fromDate=fromDate, toDate=toDate)

exporters:List[jira_exporter.JiraExporter] = [exportByEpic, exportByWorktype, exportCycletimeByEpic]


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

