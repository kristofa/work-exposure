from datetime import datetime
from value_stream_mapping.jira import jira_api
from value_stream_mapping.jira import jira_export_time_per_epic

since = datetime.fromisoformat('2022-01-01')

jiraApi = jira_api.JiraApi(baseUrl='https://jira.net/',user='user',password='pwd')

exportPerEpic = jira_export_time_per_epic.JiraExportTimePerEpic(jiraApi=jiraApi)
epicOverview = exportPerEpic.export(startDate = since)

def secondsToDays(days):
    return round(days / 60 / 60 / 24, 1)

totalDaysLogged = secondsToDays(epicOverview.totalSecondsSpent)
totalDaysLoggedOnEpics = secondsToDays(epicOverview.totalSecondsSpentOnEpics)

print('From', since, 'until', datetime.now())
print('Total days logged',totalDaysLogged)
print('Total days logged on epics',totalDaysLoggedOnEpics)

for epic in epicOverview.overviewByEpic:
    print('----------------------------------')
    print('Epic key', epic.epicKey)
    print('Epic name', epic.epicName)
    print('Total days spent ', secondsToDays(epic.totalSecondsSpent))
    for key in epic.totalSecondsByPerson.keys():
        print('User', key,'Total days spent:', secondsToDays(epic.totalSecondsByPerson[key])) 
    print('----------------------------------')


print('Tickets without epic assigned:', epicOverview.ticketsWithoutEpic)

