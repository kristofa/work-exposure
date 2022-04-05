from datetime import datetime
from . import jira_api


class EpicOverview:

    def __init__(self, since:datetime):
        self.since = since
        self.totalSecondsSpent = 0
        self.totalSecondsSpentOnEpics = 0
        self.ticketsWithoutEpic = []
        self.overviewByEpic = []


class TimeByEpic:

    def __init__(self, epicKey:str, epicName:str):
        self.epicKey = epicKey
        self.epicName = epicName
        self.totalSecondsSpent = 0
        self.totalSecondsByPerson = {}



class JiraExportTimePerEpic:

    def __init__(self, jiraApi: jira_api.JiraApi):
        self.jiraApi = jiraApi


    def export(self, startDate: datetime) -> EpicOverview:
        workLogItemIds = self.jiraApi.getUpdatedWorklogIdsSince(startDate)
        jiraWorkLogItems = self.jiraApi.getWorkLogItems(workLogItemIds)

        jiraIssues = {}
        epics = {}
        epicOverview = EpicOverview(startDate)

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
                    epic = TimeByEpic(epicKey, epicDescription)
                    epics[epicKey] = epic
                epic.totalSecondsSpent += jiraWorkLogItem.timeSpentSeconds
                secondsSpentByAuthor = epic.totalSecondsByPerson.get(jiraWorkLogItem.author, 0)
                epic.totalSecondsByPerson[jiraWorkLogItem.author] = secondsSpentByAuthor + jiraWorkLogItem.timeSpentSeconds
                epicOverview.totalSecondsSpentOnEpics += jiraWorkLogItem.timeSpentSeconds
            else:
                epicOverview.ticketsWithoutEpic.append(jiraIssue.issueKey)

            epicOverview.totalSecondsSpent += jiraWorkLogItem.timeSpentSeconds
        
        epicOverview.overviewByEpic = list(epics.values())

        return epicOverview