from datetime import datetime
from typing import List
from . import jira_api


class WorkTypeOverview:

    def __init__(self, since:datetime):
        self.since = since
        self.totalSecondsSpent = 0
        self.totalSecondsSpentOnItemsWithWorkType = 0
        self.ticketsWithoutWorkType = []
        self.overviewByWorkType = []


class TimeByWorkType:

    def __init__(self, workType:str):
        self.workType = workType
        self.totalSecondsSpent = 0
        self.totalSecondsByPerson = {}

class JiraIssue:

    def __init__(self, issueKey:str, issueDescription:str):
        self.issueKey = issueKey
        self.description = issueDescription

class JiraExportTimeByWorkType:

    def __init__(self, jiraApi: jira_api.JiraApi):
        self.jiraApi = jiraApi


    def _getWorkTypes(self, aJiraIssue: jira_api.JiraIssue) -> List[str]:
        workTypes = []
        for label in aJiraIssue.labels:
            if (label.startswith('worktype:')):
                workTypes.append(label[9:])
        return workTypes

    def export(self, startDate: datetime) -> WorkTypeOverview:
        workLogItemIds = self.jiraApi.getUpdatedWorklogIdsSince(startDate)
        jiraWorkLogItems = self.jiraApi.getWorkLogItems(workLogItemIds)

        jiraIssues = {}
        timeByWorkType = {}
        ticketsWithoutWorkType = {}
        workTypeOverview = WorkTypeOverview(startDate)

        index = 0
        for jiraWorkLogItem in jiraWorkLogItems:
            index += 1
            print('Processing JiraWorklogItem', index, 'from', len(jiraWorkLogItems))
            jiraIssue = jiraIssues.get(jiraWorkLogItem.issueId)
            if (jiraIssue == None):
                jiraIssue = self.jiraApi.getIssue(jiraWorkLogItem.issueId)
                jiraIssues[jiraWorkLogItem.issueId] = jiraIssue

            workTypesFromIssue = self._getWorkTypes(aJiraIssue = jiraIssue)
            if (len(workTypesFromIssue) > 0):
                for workTypeFromIssueAsString in workTypesFromIssue:
                    workType = timeByWorkType.get(workTypeFromIssueAsString)
                    if workType == None:
                        workType = TimeByWorkType(workType=workTypeFromIssueAsString)
                        timeByWorkType[workTypeFromIssueAsString] = workType
                workType.totalSecondsSpent += jiraWorkLogItem.timeSpentSeconds
                secondsSpentByAuthor = workType.totalSecondsByPerson.get(jiraWorkLogItem.author, 0)
                workType.totalSecondsByPerson[jiraWorkLogItem.author] = secondsSpentByAuthor + jiraWorkLogItem.timeSpentSeconds
                workTypeOverview.totalSecondsSpentOnItemsWithWorkType += jiraWorkLogItem.timeSpentSeconds
            else:
                existingIssue = ticketsWithoutWorkType.get(jiraIssue.issueKey)
                if (existingIssue == None):
                    ticketsWithoutWorkType[jiraIssue.issueKey] = JiraIssue(issueKey=jiraIssue.issueKey, issueDescription=jiraIssue.description)

            workTypeOverview.totalSecondsSpent += jiraWorkLogItem.timeSpentSeconds
        
        workTypeOverview.ticketsWithoutWorkType = list(ticketsWithoutWorkType.values())
        workTypeOverview.overviewByWorkType = list(timeByWorkType.values())

        return workTypeOverview