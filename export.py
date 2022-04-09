from datetime import datetime
from value_stream_mapping.jira import jira_api
from value_stream_mapping.jira import jira_export_time_per_epic

since = datetime.fromisoformat('2022-01-01')
today = datetime.today()

jiraApi = jira_api.JiraApi(baseUrl='https://company.atlassian.net/',user='user@company.com',password='userToken')

exportPerEpic = jira_export_time_per_epic.JiraExportTimePerEpic(jiraApi=jiraApi)
epicOverview = exportPerEpic.export(startDate = since)

def secondsToWorkDays(seconds):
    return round(seconds / 60 / 60 / 8, 1)

def getCsvFilename(prefix: str, fromDate: datetime, untilDate: datetime):
    return prefix + '_from_'+fromDate.date().isoformat()+'_until_'+untilDate.date().isoformat()+'.csv'


with open(getCsvFilename('epic_overview_summary', since, today), 'w') as epicOverviewSummaryFile:
    epicOverviewSummaryFile.write('from|to|total_workdays_logged_on_epics|total_workdays_logged\n')
    totalWorkDaysLoggedOnEpics = secondsToWorkDays(epicOverview.totalSecondsSpentOnEpics)
    totalWorkDaysLogged = secondsToWorkDays(epicOverview.totalSecondsSpent)
    
    epicOverviewSummaryFile.write('{0}|{1}|{2}|{3}\n'.format(since.isoformat(),today.isoformat(),str(totalWorkDaysLoggedOnEpics),str(totalWorkDaysLogged)))
    
with open(getCsvFilename('epic_overview', since, today), 'w') as epicOverviewFile:
    with open(getCsvFilename('epic_overview_by_person', since, today), 'w') as epicOverviewByPersonFile:
        epicOverviewFile.write('epicKey|epicName|total_workdays_logged\n')
        epicOverviewByPersonFile.write('epicKey|epicName|person|total_workdays_logged\n')
        for epic in epicOverview.overviewByEpic:
            epicOverviewFile.write('{0}|{1}|{2}\n'.format(epic.epicKey, epic.epicName, str(secondsToWorkDays(epic.totalSecondsSpent))))
            for key in epic.totalSecondsByPerson.keys():
                epicOverviewByPersonFile.write('{0}|{1}|{2}|{3}\n'.format(epic.epicKey, epic.epicName, key, str(secondsToWorkDays(epic.totalSecondsByPerson[key]))))

with open(getCsvFilename('epic_overview_issues_without_epic', since, today), 'w') as issuesWithoutEpicFile:
    issuesWithoutEpicFile.write('issueKey\n')
    for issueKey in epicOverview.ticketsWithoutEpic:
        issuesWithoutEpicFile.write('{0}\n'.format(issueKey))

