from . import jira_api
from flow_metrics_toolkit.core import domain
from typing import List
import datetime

class Either(object):
    pass

class Left(Either):
    def __init__(self, v): self.v = v
    def is_left(self): return True
    def is_right(self): return False
    def value(self): return self.v 

class Right(Either):
    def __init__(self, v): self.v = v
    def is_left(self): return False
    def is_right(self): return True
    def value(self): return self.v 


class JiraExporter:

    def __init__(self, jiraApi: jira_api.JiraApi, workflow: domain.Workflow):
        self.jiraApi = jiraApi
        self.workflow = workflow
        
    def export(self, projectId: str) -> List[domain.WorkItem]:
        
        workItems: List[domain.WorkItem] = []
        jiraIssues = self.jiraApi.getIssuesFor(projectKey = projectId)
        for jiraIssue in jiraIssues:
            result = self._convert(issueKey=jiraIssue.issueKey, jiraIssueChanges=jiraIssue.changes)
            if (isinstance(result, Left)):
                workItem = domain.WorkItem(key=jiraIssue.issueKey, type=jiraIssue.issueType)
                workItem.workflowErrors.append(result.v)
                workItem.hasBeenBlocked = jiraIssue.hasBeenBlocked
                workItem.hasBeenPartOfSprint = jiraIssue.hasBeenPartOfSprint
                workItems.append(workItem)
            else:
                workItem = domain.WorkItem(key=jiraIssue.issueKey, type=jiraIssue.issueType, states=result.v)
                workItem.hasBeenBlocked = jiraIssue.hasBeenBlocked
                workItem.hasBeenPartOfSprint = jiraIssue.hasBeenPartOfSprint
                workItems.append(workItem)
        return workItems    
    

    def _convert(self, issueKey: str, jiraIssueChanges: List[jira_api.JiraIssueChange]) -> Either:
        
        stateTransitions: List[domain.StateArrivalAndDeparture] = []
        currentState: domain.State = None
        currentStateArrival: datetime = None
        finishedWorkflow = False
        for jiraIssueChange in jiraIssueChanges:
            if (currentState == None):
                fromStatus = self.workflow.stateFromName(jiraIssueChange.fromStatus)
                currentState = self.workflow.stateFromName(jiraIssueChange.toStatus)
                if (currentState == None):
                    return Left(domain.WorkflowError.UNKNOWN_STATE)
                if (fromStatus.stateType != domain.StateType.TODO):
                    return Left(domain.WorkflowError.INVALID_START_STATE)
                currentStateArrival = jiraIssueChange.date
                if (currentState.stateType == domain.StateType.DONE):
                    finishedWorkflow = True
            else:
                fromStatus = self.workflow.stateFromName(jiraIssueChange.fromStatus)
                if (fromStatus != currentState):
                    return Left(domain.WorkflowError.INVALID_STATE_TRANSITION)
                date = jiraIssueChange.date
                stateTransitions.append(domain.StateArrivalAndDeparture(workItemKey=issueKey,state=currentState,arrival=currentStateArrival,departure=date))

                currentState = self.workflow.stateFromName(jiraIssueChange.toStatus)
                if (currentState == None):
                    return Left(domain.WorkflowError.UNKNOWN_STATE)
                if (self.workflow.validTransition(fromState=fromStatus, toState=currentState) == False):
                    return Left(domain.WorkflowError.BACKWARD_FLOW)
                currentStateArrival = date
                if (currentState.stateType == domain.StateType.DONE):
                    finishedWorkflow = True

        if (finishedWorkflow):
            if (len(stateTransitions) == 0):
                return Left(domain.WorkflowError.IMMEDIATELY_CLOSED)
            return Right(stateTransitions)
        return Left(domain.WorkflowError.DIDNT_FINISH)



