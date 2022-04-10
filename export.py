from datetime import datetime
from value_stream_mapping.jira import jira_api
from value_stream_mapping.jira import jira_export_time_by_epic
from value_stream_mapping.jira import jira_export_time_by_worktype

since = datetime.fromisoformat('2022-01-01')
today = datetime.today()

jiraApi = jira_api.JiraApi(baseUrl='https://company.atlassian.net/',user='user@company.com',password='userToken')

def _secondsToWorkDays(seconds):
    return round(seconds / 60 / 60 / 8, 1)

def _getCsvFilename(prefix: str, fromDate: datetime, untilDate: datetime):
    return prefix + '_from_'+fromDate.date().isoformat()+'_until_'+untilDate.date().isoformat()+'.csv'


def _exportEpicOverview(epicOverview: jira_export_time_by_epic.EpicOverview):
    with open(_getCsvFilename('epic_overview_summary', since, today), 'w') as epicOverviewSummaryFile:
        epicOverviewSummaryFile.write('from|to|total_workdays_logged_on_epics|total_workdays_logged\n')
        totalWorkDaysLoggedOnEpics = _secondsToWorkDays(epicOverview.totalSecondsSpentOnEpics)
        totalWorkDaysLogged = _secondsToWorkDays(epicOverview.totalSecondsSpent)
        epicOverviewSummaryFile.write('{0}|{1}|{2}|{3}\n'.format(since.isoformat(),today.isoformat(),str(totalWorkDaysLoggedOnEpics),str(totalWorkDaysLogged)))
    
    with open(_getCsvFilename('epic_overview', since, today), 'w') as epicOverviewFile:
        with open(_getCsvFilename('epic_overview_by_person', since, today), 'w') as epicOverviewByPersonFile:
            epicOverviewFile.write('epicKey|epicName|total_workdays_logged\n')
            epicOverviewByPersonFile.write('epicKey|epicName|person|total_workdays_logged\n')
            for epic in epicOverview.overviewByEpic:
                epicOverviewFile.write('{0}|{1}|{2}\n'.format(epic.epicKey, epic.epicName, str(_secondsToWorkDays(epic.totalSecondsSpent))))
                for key in epic.totalSecondsByPerson.keys():
                    epicOverviewByPersonFile.write('{0}|{1}|{2}|{3}\n'.format(epic.epicKey, epic.epicName, key, str(_secondsToWorkDays(epic.totalSecondsByPerson[key]))))

    with open(_getCsvFilename('epic_overview_issues_without_epic', since, today), 'w') as issuesWithoutEpicFile:
        issuesWithoutEpicFile.write('issueKey|description\n')
        for jiraIssue in epicOverview.ticketsWithoutEpic:
            issuesWithoutEpicFile.write('{0}|{1}\n'.format(jiraIssue.issueKey, jiraIssue.description))

exportByEpic = jira_export_time_by_epic.JiraExportTimePerEpic(jiraApi=jiraApi)
epicOverview = exportByEpic.export(startDate = since)
_exportEpicOverview(epicOverview=epicOverview)


def _exportWorktypeOverview(worktypeOverview: jira_export_time_by_worktype.WorkTypeOverview):
    with open(_getCsvFilename('worktype_overview_summary', since, today), 'w') as worktypeOverviewSummaryFile:
        worktypeOverviewSummaryFile.write('from|to|total_workdays_logged_items_with_worktype|total_workdays_logged\n')
        totalWorkDaysLoggedOnItemsWithWorktype = _secondsToWorkDays(worktypeOverview.totalSecondsSpentOnItemsWithWorkType)
        totalWorkDaysLogged = _secondsToWorkDays(worktypeOverview.totalSecondsSpent)
        worktypeOverviewSummaryFile.write('{0}|{1}|{2}|{3}\n'.format(since.isoformat(),today.isoformat(),str(totalWorkDaysLoggedOnItemsWithWorktype),str(totalWorkDaysLogged)))
    
    with open(_getCsvFilename('worktype_overview', since, today), 'w') as worktypeOverviewFile:
        with open(_getCsvFilename('worktype_overview_by_person', since, today), 'w') as worktypeOverviewByPersonFile:
            worktypeOverviewFile.write('worktype|total_workdays_logged\n')
            worktypeOverviewByPersonFile.write('worktype|person|total_workdays_logged\n')
            for worktype in worktypeOverview.overviewByWorkType:
                worktypeOverviewFile.write('{0}|{1}\n'.format(worktype.workType, str(_secondsToWorkDays(worktype.totalSecondsSpent))))
                for person in worktype.totalSecondsByPerson.keys():
                    worktypeOverviewByPersonFile.write('{0}|{1}|{2}\n'.format(worktype.workType, person, str(_secondsToWorkDays(worktype.totalSecondsByPerson[person]))))

    with open(_getCsvFilename('worktype_overview_issues_without_worktype', since, today), 'w') as issuesWithoutWorktypeFile:
        issuesWithoutWorktypeFile.write('issueKey|description\n')
        for jiraIssue in worktypeOverview.ticketsWithoutWorkType:
            issuesWithoutWorktypeFile.write('{0}|{1}\n'.format(jiraIssue.issueKey, jiraIssue.description))


exportByWorktype = jira_export_time_by_worktype.JiraExportTimeByWorkType(jiraApi=jiraApi)
worktypeOverview = exportByWorktype.export(startDate = since)
_exportWorktypeOverview(worktypeOverview=worktypeOverview)


