from dataclasses import dataclass
from . import jira_api
from value_stream_mapping.domain import cycle_time_overview
from .import jira_exporter
from datetime import datetime
from datetime import date
import functools
from functools import total_ordering
from typing import Dict
from typing import List
from value_stream_mapping.plantuml import gantt_diagram_exporter


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


class JiraExportCycleTimeByEpic(jira_exporter.JiraExporter):

    def __init__(self, jiraApi: jira_api.JiraApi, startDate: datetime):
        self.jiraApi = jiraApi
        self.startDate = startDate
        self.epics: Dict[str, JiraEpic] = {}

    def process(self, worklogItem: jira_api.JiraWorklogItem, issue: jira_api.JiraIssue):
        if issue.epic != None:
            epicKey = issue.epic.key
            epicDescription = issue.epic.description
            epic = self.epics.get(epicKey)
            if epic == None:
                epic = JiraEpic(epicKey, epicDescription)
                self.epics[epicKey] = epic
            epic.jiraWorkLogs.append(JiraWorkLogItem(dateOfWork=worklogItem.date.date()))

    def _getItemCycletimeOverview(self) -> List[cycle_time_overview.ItemCycletimeOverview]:
        itemsCycleTimeOverview: List[cycle_time_overview.ItemCycletimeOverview] = []
        for epic in self.epics.values():
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

    def exportToFiles(self):
        today = datetime.today()
        listOfEpics : List[cycle_time_overview.ItemCycletimeOverview] = self._getItemCycletimeOverview()
        gantDiagramExporter = gantt_diagram_exporter.GanttDiagramExporter(title="Export",fromDate=self.startDate, toDate=today)
        gantDiagramExporter.export(items = listOfEpics, outputFileName="plantuml")


   