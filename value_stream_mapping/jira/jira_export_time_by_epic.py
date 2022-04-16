from . import jira_api
from .import jira_exporter
from value_stream_mapping.domain import epic_overview
from datetime import datetime
from typing import Dict


class JiraExportTimeByEpic(jira_exporter.JiraExporter):

    def __init__(self, jiraApi: jira_api.JiraApi, startDate: datetime):
        self.jiraApi = jiraApi
        self.startDate = startDate
        self.epics:Dict[str, epic_overview.TimeByEpic] = {}
        self.epicOverview = epic_overview.EpicOverview(startDate)
        self.ticketsWithoutEpic:Dict[str, epic_overview.Issue] = {}


    def process(self, worklogItem: jira_api.JiraWorklogItem, issue: jira_api.JiraIssue):
        if issue.epic != None:
            epicKey = issue.epic.key
            epicDescription = issue.epic.description
            epic = self.epics.get(epicKey)
            if epic == None:
                epic = epic_overview.TimeByEpic(epicKey, epicDescription)
                self.epics[epicKey] = epic
            epic.totalSecondsSpent += worklogItem.timeSpentSeconds
            secondsSpentByAuthor = epic.totalSecondsByPerson.get(worklogItem.author, 0)
            epic.totalSecondsByPerson[worklogItem.author] = secondsSpentByAuthor + worklogItem.timeSpentSeconds
            self.epicOverview.totalSecondsSpentOnEpics += worklogItem.timeSpentSeconds
        else:
            existingIssue = self.ticketsWithoutEpic.get(issue.issueKey)
            if (existingIssue == None):
                self.ticketsWithoutEpic[issue.issueKey] = epic_overview.Issue(issueKey=issue.issueKey, issueDescription=issue.description)

            self.epicOverview.totalSecondsSpent += worklogItem.timeSpentSeconds


    def exportToFiles(self):
        self.epicOverview.ticketsWithoutEpic = list(self.ticketsWithoutEpic.values())
        self.epicOverview.overviewByEpic = list(self.epics.values())
        today = datetime.today()

        with open(self._getCsvFilename('epic_overview_summary', self.startDate, today), 'w') as epicOverviewSummaryFile:
            epicOverviewSummaryFile.write('from|to|total_workdays_logged_on_epics|total_workdays_logged\n')
            totalWorkDaysLoggedOnEpics = self._secondsToWorkDays(self.epicOverview.totalSecondsSpentOnEpics)
            totalWorkDaysLogged = self._secondsToWorkDays(self.epicOverview.totalSecondsSpent)
            epicOverviewSummaryFile.write('{0}|{1}|{2}|{3}\n'.format(self.startDate.isoformat(),today.isoformat(),str(totalWorkDaysLoggedOnEpics),str(totalWorkDaysLogged)))
    
        with open(self._getCsvFilename('epic_overview', self.startDate, today), 'w') as epicOverviewFile:
            with open(self._getCsvFilename('epic_overview_by_person', self.startDate, today), 'w') as epicOverviewByPersonFile:
                epicOverviewFile.write('epicKey|epicName|total_workdays_logged\n')
                epicOverviewByPersonFile.write('epicKey|epicName|person|total_workdays_logged\n')
                for epic in self.epicOverview.overviewByEpic:
                    epicOverviewFile.write('{0}|{1}|{2}\n'.format(epic.epicKey, epic.epicName, str(self._secondsToWorkDays(epic.totalSecondsSpent))))
                    for key in epic.totalSecondsByPerson.keys():
                        epicOverviewByPersonFile.write('{0}|{1}|{2}|{3}\n'.format(epic.epicKey, epic.epicName, key, str(self._secondsToWorkDays(epic.totalSecondsByPerson[key]))))

        with open(self._getCsvFilename('epic_overview_issues_without_epic', self.startDate, today), 'w') as issuesWithoutEpicFile:
            issuesWithoutEpicFile.write('issueKey|description\n')
            for jiraIssue in self.epicOverview.ticketsWithoutEpic:
                issuesWithoutEpicFile.write('{0}|{1}\n'.format(jiraIssue.issueKey, jiraIssue.description))

    def _secondsToWorkDays(self, seconds):
        return round(seconds / 60 / 60 / 8, 1)

    def _getCsvFilename(self, prefix: str, fromDate: datetime, untilDate: datetime):
        return prefix + '_from_'+fromDate.date().isoformat()+'_until_'+untilDate.date().isoformat()+'.csv'
    

    