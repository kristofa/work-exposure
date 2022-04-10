from . import jira_api
from value_stream_mapping.domain import epic_overview
from datetime import datetime


class JiraExportTimeByEpic:

    def __init__(self, jiraApi: jira_api.JiraApi):
        self.jiraApi = jiraApi


    def export(self, startDate: datetime) -> epic_overview.EpicOverview:
        workLogItemIds = self.jiraApi.getUpdatedWorklogIdsSince(startDate)
        jiraWorkLogItems = self.jiraApi.getWorkLogItems(workLogItemIds)

        jiraIssues = {}
        epics = {}
        ticketsWithoutEpics = {}
        epicOverview = epic_overview.EpicOverview(startDate)

        index = 0
        for jiraWorkLogItem in jiraWorkLogItems:
            index += 1
            print('Processing JiraWorklogItem', index, 'from', len(jiraWorkLogItems))
            jiraIssue = jiraIssues.get(jiraWorkLogItem.issueId)
            if (jiraIssue == None):
                jiraIssue = self.jiraApi.getIssue(jiraWorkLogItem.issueId)
                jiraIssues[jiraWorkLogItem.issueId] = jiraIssue

            if jiraIssue.epic != None:
                epicKey = jiraIssue.epic.key
                epicDescription = jiraIssue.epic.description
                epic = epics.get(epicKey)
                if epic == None:
                    epic = epic_overview.TimeByEpic(epicKey, epicDescription)
                    epics[epicKey] = epic
                epic.totalSecondsSpent += jiraWorkLogItem.timeSpentSeconds
                secondsSpentByAuthor = epic.totalSecondsByPerson.get(jiraWorkLogItem.author, 0)
                epic.totalSecondsByPerson[jiraWorkLogItem.author] = secondsSpentByAuthor + jiraWorkLogItem.timeSpentSeconds
                epicOverview.totalSecondsSpentOnEpics += jiraWorkLogItem.timeSpentSeconds
            else:
                existingIssue = ticketsWithoutEpics.get(jiraIssue.issueKey)
                if (existingIssue == None):
                    ticketsWithoutEpics[jiraIssue.issueKey] = epic_overview.Issue(issueKey=jiraIssue.issueKey, issueDescription=jiraIssue.description)

            epicOverview.totalSecondsSpent += jiraWorkLogItem.timeSpentSeconds
        
        epicOverview.ticketsWithoutEpic = list(ticketsWithoutEpics.values())
        epicOverview.overviewByEpic = list(epics.values())

        return epicOverview