from dataclasses import dataclass
from . import jira_api
from work_exposure.domain import cycle_time_overview
from . import jira_worklog_based_exporter
from datetime import datetime
from datetime import date
import functools
from functools import total_ordering
from typing import Dict
from typing import List
from work_exposure.plantuml import gantt_diagram_exporter


class JiraEpic:
    def __init__(self, key:str, description: str, colour: str):
        self.key = key
        self.description = description
        self.colour = colour
        self.jiraWorkLogs: List[JiraWorkLogItem] = []
        self.totalSecondsLogged = 0

@total_ordering
class JiraWorkLogItem:
    def __init__(self, dateOfWork: date):
        self.dateOfWork = dateOfWork  

    def __lt__(self, obj):
        return ((self.dateOfWork) < (obj.dateOfWork))
    
    def __eq__(self, obj):
        return (self.dateOfWork == obj.dateOfWork)


class JiraExportCycleTimeByEpic(jira_worklog_based_exporter.JiraExporter):

    def __init__(self, jiraApi: jira_api.JiraApi, fromDate: datetime, toDate: datetime, epicsToExclude: List[str]):
        self.jiraApi = jiraApi
        self.fromDate = fromDate
        self.toDate = toDate
        self.epics: Dict[str, JiraEpic] = {}
        self.epicsToExclude = epicsToExclude

    def process(self, worklogItem: jira_api.JiraWorklogItem, issue: jira_api.JiraIssue):
        if issue.epic != None:
            epicKey = issue.epic.key
            if epicKey not in self.epicsToExclude:
                epic = self.epics.get(epicKey)
                if epic == None:
                    epicDescription = issue.epic.description
                    epicColour = issue.epic.colour
                    epic = JiraEpic(epicKey, epicDescription, epicColour)
                    self.epics[epicKey] = epic
                epic.jiraWorkLogs.append(JiraWorkLogItem(dateOfWork=worklogItem.date.date()))
                epic.totalSecondsLogged += worklogItem.timeSpentSeconds

    def exportToFiles(self):
        listOfEpics : List[cycle_time_overview.ItemCycletimeOverview] = self._getItemCycletimeOverview()
        gantDiagramExporter = gantt_diagram_exporter.GanttDiagramExporter(title="Work In Progress overview",fromDate=self.fromDate, toDate=self.toDate)
        gantDiagramExporter.export(items = listOfEpics)

        with open(self._getCsvFilename('epic_flow_efficiency', self.fromDate, self.toDate), 'w') as epicFlowEfficiencyFile:
            epicFlowEfficiencyFile.write('epicKey|epicName|flow_efficiency\n')
            for item in listOfEpics:
                epicFlowEfficiencyFile.write('{0}|{1}|{2}\n'.format(item.itemKey, item.itemDescription, str(item.flowEfficiency())))

    

    def _getItemCycletimeOverview(self) -> List[cycle_time_overview.ItemCycletimeOverview]:
        itemsCycleTimeOverview: List[cycle_time_overview.ItemCycletimeOverview] = []
        for epic in self.epics.values():
            itemCycleTimeOverview = cycle_time_overview.ItemCycletimeOverview(itemKey=epic.key, itemDescription=epic.description, itemColour=epic.colour)
            itemCycleTimeOverview.totalTimeLoggedInSeconds = epic.totalSecondsLogged
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

    def _getCsvFilename(self, prefix: str, fromDate: datetime, toDate: datetime):
        return prefix + '_from_'+fromDate.date().isoformat()+'_until_'+toDate.date().isoformat()+'.csv'
    

    






   