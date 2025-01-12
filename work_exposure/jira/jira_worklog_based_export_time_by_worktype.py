from datetime import datetime
from typing import List
from typing import Dict
from work_exposure.domain import worktype_overview
from . import jira_api
from . import jira_worklog_based_exporter


class JiraExportTimeByWorkType(jira_worklog_based_exporter.JiraExporter):

    def __init__(self, jiraApi: jira_api.JiraApi, fromDate: datetime, toDate: datetime, work_classification_prefix: str):
        self.jiraApi = jiraApi
        self.fromDate = fromDate
        self.toDate = toDate
        self.timeByWorkType:Dict[str,worktype_overview.TimeByWorkType] = {}
        self.worktypeOverview = worktype_overview.WorkTypeOverview(fromDate)
        self.ticketsWithoutWorkType:Dict[str, worktype_overview.Issue] = {}
        self.allIssuesByKey:Dict[str, worktype_overview.Issue] = {}
        self.work_classification_prefix = work_classification_prefix


    def process(self, worklogItem: jira_api.JiraWorklogItem, issue: jira_api.JiraIssue):
        
        indexedIssue = self.allIssuesByKey.get(issue.issueKey)
        if indexedIssue == None:
            self.allIssuesByKey[issue.issueKey] = issue

        workTypesFromIssue = self._getWorkTypes(aJiraIssue = issue)
        if (len(workTypesFromIssue) > 0):
            for workTypeFromIssueAsString in workTypesFromIssue:
                workType = self.timeByWorkType.get(workTypeFromIssueAsString)
                if workType == None:
                    workType = worktype_overview.TimeByWorkType(workType=workTypeFromIssueAsString)
                    self.timeByWorkType[workTypeFromIssueAsString] = workType
                workType.totalSecondsSpent += worklogItem.timeSpentSeconds
                
                # add time by author
                secondsSpentByAuthor = workType.totalSecondsByPerson.get(worklogItem.author, 0)
                workType.totalSecondsByPerson[worklogItem.author] = secondsSpentByAuthor + worklogItem.timeSpentSeconds

                # add time by issue
                secondsSpentByIssue = workType.totalSecondsByIssue.get(issue.issueKey, 0)
                workType.totalSecondsByIssue[issue.issueKey] = secondsSpentByIssue + worklogItem.timeSpentSeconds

                # add time by year and month
                yearMonth = worklogItem.date.strftime('%Y%m')
                secondsSpentByYearMonth = workType.totalSecondsByYearAndMonth.get(yearMonth, 0)
                workType.totalSecondsByYearAndMonth[yearMonth] = secondsSpentByYearMonth + worklogItem.timeSpentSeconds

                self.worktypeOverview.totalSecondsSpentOnItemsWithWorkType += worklogItem.timeSpentSeconds
        else:
            existingIssue = self.ticketsWithoutWorkType.get(issue.issueKey)
            if (existingIssue == None):
                self.ticketsWithoutWorkType[issue.issueKey] = worktype_overview.Issue(issueKey=issue.issueKey, issueDescription=issue.description)

        self.worktypeOverview.totalSecondsSpent += worklogItem.timeSpentSeconds
    

    def exportToFiles(self):
        self.worktypeOverview.ticketsWithoutWorkType = list(self.ticketsWithoutWorkType.values())
        self.worktypeOverview.overviewByWorkType = list(self.timeByWorkType.values())

        with open(self._getCsvFilename('worktype_overview_summary', self.fromDate, self.toDate), 'w') as worktypeOverviewSummaryFile:
            worktypeOverviewSummaryFile.write('from|to|total_workdays_logged_items_with_worktype|total_workdays_logged\n')
            totalWorkDaysLoggedOnItemsWithWorktype = self._secondsToWorkDays(self.worktypeOverview.totalSecondsSpentOnItemsWithWorkType)
            totalWorkDaysLogged = self._secondsToWorkDays(self.worktypeOverview.totalSecondsSpent)
            worktypeOverviewSummaryFile.write('{0}|{1}|{2}|{3}\n'.format(self.fromDate.isoformat(),self.toDate.isoformat(),str(totalWorkDaysLoggedOnItemsWithWorktype),str(totalWorkDaysLogged)))
    
        with open(self._getCsvFilename('worktype_overview', self.fromDate, self.toDate), 'w') as worktypeOverviewFile:
            with open(self._getCsvFilename('worktype_overview_by_person', self.fromDate, self.toDate), 'w') as worktypeOverviewByPersonFile:
                with open(self._getCsvFilename('worktype_overview_by_issue', self.fromDate, self.toDate), 'w') as worktypeOverviewByIssueFile:
                    with open(self._getCsvFilename('worktype_overview_by_yearmonth', self.fromDate, self.toDate), 'w') as worktypeOverviewByYearMonthFile:
                
                        worktypeOverviewFile.write('worktype|total_workdays_logged\n')
                        worktypeOverviewByPersonFile.write('worktype|person|total_workdays_logged\n')
                        worktypeOverviewByIssueFile.write('worktype|issue|description|total_minutes_logged\n')
                        worktypeOverviewByYearMonthFile.write('worktype|yearmonth|total_workdays_logged\n')
                        for worktype in self.worktypeOverview.overviewByWorkType:
                            worktypeOverviewFile.write('{0}|{1}\n'.format(worktype.workType, str(self._secondsToWorkDays(worktype.totalSecondsSpent))))
                            for person in worktype.totalSecondsByPerson.keys():
                                worktypeOverviewByPersonFile.write('{0}|{1}|{2}\n'.format(worktype.workType, person, str(self._secondsToWorkDays(worktype.totalSecondsByPerson[person]))))
                            for issueKey in worktype.totalSecondsByIssue.keys():
                                issueDescription = self.allIssuesByKey[issueKey].description
                                worktypeOverviewByIssueFile.write('{0}|{1}|{2}|{3}\n'.format(worktype.workType, issueKey, issueDescription, str(self._secondsToMinutes(worktype.totalSecondsByIssue[issueKey]))))
                            for yearMonth in worktype.totalSecondsByYearAndMonth.keys():
                                worktypeOverviewByYearMonthFile.write('{0}|{1}|{2}\n'.format(worktype.workType, yearMonth, str(self._secondsToWorkDays(worktype.totalSecondsByYearAndMonth[yearMonth]))))

        with open(self._getCsvFilename('worktype_overview_issues_without_worktype', self.fromDate, self.toDate), 'w') as issuesWithoutWorktypeFile:
            issuesWithoutWorktypeFile.write('issueKey|description\n')
            for jiraIssue in self.worktypeOverview.ticketsWithoutWorkType:
                issuesWithoutWorktypeFile.write('{0}|{1}\n'.format(jiraIssue.issueKey, jiraIssue.description))    

    def _getWorkTypes(self, aJiraIssue: jira_api.JiraIssue) -> List[str]:
        workTypes = []
        for label in aJiraIssue.labels:
            if (label.startswith(self.work_classification_prefix)):
                workTypes.append(label[len(self.work_classification_prefix):])
        return workTypes

    def _secondsToWorkDays(self, seconds):
        return round(seconds / 60 / 60 / 8, 1)

    def _secondsToMinutes(self, seconds):
        return round(seconds / 60, 0)

    def _getCsvFilename(self, prefix: str, fromDate: datetime, toDate: datetime):
        return prefix + '_from_'+fromDate.date().isoformat()+'_until_'+toDate.date().isoformat()+'.csv'


    