from datetime import datetime
import requests
from typing import List
from dateutil.parser import parse

class JiraIssueChange:
    def __init__(self, date: datetime, fromStatus: str, toStatus: str):
        self.date = date
        self.fromStatus = fromStatus
        self.toStatus = toStatus

class JiraIssue:
    def __init__(self, issueKey, issueType):
        self.issueKey = issueKey
        self.issueType = issueType
        self.hasBeenBlocked = False
        self.hasBeenPartOfSprint = False
        self.changes = []

    def addChange(self, change: JiraIssueChange):
        self.changes.append(change)


class JiraApi:

    def __init__(self, baseUrl, user, password, maxResultsPerRequest=25):
        self.baseUrl = baseUrl
        self.user = user
        self.password = password
        self.maxResultsPerRequest = maxResultsPerRequest


    def getUpdatedWorklogsSince(self, since: datetime) -> List[int]:
        isLastPage = False
        # sinceMs = unit timestamp ms
        sinceUnixTimestampMs = int(since.timestamp() * 1000)
        workLogIds = []
        while isLastPage == False:
            jsonResponse = self._getUpdatedWorklogsSince(sinceUnixTimestampMs)
            sinceUnixTimestampMs = jsonResponse["until"] + 1
            isLastPage = jsonResponse["lastPage"]
            for worklogItem in jsonResponse["values"]:
                workLogIds.append(worklogItem["worklogId"])

        return workLogIds

    def _getUpdatedWorklogsSince(self, sinceUnixTimeStampMs: float):
        requestUrl = self.baseUrl + 'rest/api/3/worklog/updated'
        defaultHeaders = {'Content-Type':'application/json'}
        queryParams = {'since':sinceUnixTimeStampMs}
        timeoutSeconds = 10

        response = requests.get(requestUrl, headers=defaultHeaders, params=queryParams, auth=(self.user, self.password), timeout=timeoutSeconds)
        response.raise_for_status
        return response.json()

    def getIssuesFor(self, projectKey: str) -> List[JiraIssue]:
        
        jsonResponse = self._searchRequest(projectKey=projectKey, startAt=0, maxResults=self.maxResultsPerRequest)
        totalItems = jsonResponse['total']
        print("Total items: " + str(totalItems))
        processedItems = 0
        issues = []
        
        while (processedItems < totalItems):
            for jsonIssue in jsonResponse['issues']:
                issue = JiraIssue(issueKey=jsonIssue['key'], issueType=jsonIssue['fields']['issuetype']['name'])
                changelog = jsonIssue['changelog']
                for history in changelog['histories']:
                    creationDate = parse(history['created'])
                    for historyItem in history['items']:
                        if (historyItem['field'] == 'status'):
                            issue.addChange(JiraIssueChange(date = creationDate, fromStatus=historyItem['fromString'], toStatus=historyItem['toString']))
                        elif ((historyItem['field'] == 'Sprint') and (historyItem['toString'] != None)):
                            issue.hasBeenPartOfSprint = True
                        elif (historyItem['field'] == 'Flagged'):
                            issue.hasBeenBlocked = True
                issues.append(issue)
                processedItems += 1
            print("Processed items: " + str(processedItems))
            if (processedItems < totalItems):
                jsonResponse = self._searchRequest(projectKey=projectKey, startAt=processedItems, maxResults=self.maxResultsPerRequest)
        return issues

    def _searchRequest(self, projectKey, startAt, maxResults):
        requestUrl = self.baseUrl + 'rest/api/2/search'
        defaultHeaders = {'Content-Type':'application/json'}
        
        queryParams = {'jql':'project=' + projectKey, 'startAt': startAt, 'maxResults': maxResults, 'fields':'key,issuetype', 'expand':'changelog'}
        timeoutSeconds = 10

        response = requests.get(requestUrl, headers=defaultHeaders, params=queryParams, auth=(self.user, self.password), timeout=timeoutSeconds)
        response.raise_for_status
        return response.json()
        


