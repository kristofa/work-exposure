from dataclasses import dataclass
from . import jira_api
from value_stream_mapping.domain import cycle_time_overview
from datetime import datetime
from datetime import date
import functools
from functools import total_ordering
from typing import Dict
from typing import List


class JiraEpic:
    def __init__(self, key:str, description: str):
        self.key = key
        self.description = description
        self.jiraWorkLogs: List[JiraWorkLogItem] = []

@total_ordering
class JiraWorkLogItem:
    def __init__(self, dateOfWork: date):
        self.dateOfWork = dateOfWork  

    def __lt__(self, obj):
        return ((self.dateOfWork) < (obj.dateOfWork))
    
    def __eq__(self, obj):
        return (self.dateOfWork == obj.dateOfWork)


class JiraExportCycleTimeByEpic:

    def __init__(self, jiraApi: jira_api.JiraApi):
        self.jiraApi = jiraApi

    def export(self, startDate:datetime) -> List[cycle_time_overview.ItemCycletimeOverview]:
        workLogItemIds = self.jiraApi.getUpdatedWorklogIdsSince(startDate)
        jiraWorkLogItems = self.jiraApi.getWorkLogItems(workLogItemIds)

        jiraIssues: Dict[str, jira_api.JiraIssue] = {}
        epics: Dict[str, JiraEpic] = {}
        itemsCycleTimeOverview: List[cycle_time_overview.ItemCycletimeOverview] = []

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
                    epic = JiraEpic(epicKey, epicDescription)
                    epics[epicKey] = epic
                epic.jiraWorkLogs.append(JiraWorkLogItem(dateOfWork=jiraWorkLogItem.date.date()))
        
        for epic in epics.values():
            itemCycleTimeOverview = cycle_time_overview.ItemCycletimeOverview(itemKey=epic.key, itemDescription=epic.description)
            sortedJiraWorklogs = sorted(epic.jiraWorkLogs)
            startDate = sortedJiraWorklogs[0].dateOfWork
            previousDate = sortedJiraWorklogs[0].dateOfWork
            for jiraWorklog in sortedJiraWorklogs:
                if ((jiraWorklog.dateOfWork - previousDate).days == 1):
                    previousDate = jiraWorklog.dateOfWork
                elif ((jiraWorklog.dateOfWork - previousDate).days > 1):
                    itemInProgress = cycle_time_overview.ItemInProgress(start=startDate, end=previousDate)
                    itemCycleTimeOverview.inProgress.append(itemInProgress)
                    startDate = jiraWorklog.dateOfWork
                    previousDate = jiraWorklog.dateOfWork
            
            itemInProgress = cycle_time_overview.ItemInProgress(start=startDate, end=previousDate)
            itemCycleTimeOverview.inProgress.append(itemInProgress)
            itemsCycleTimeOverview.append(itemCycleTimeOverview)

        return itemsCycleTimeOverview