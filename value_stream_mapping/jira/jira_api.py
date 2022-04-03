from concurrent.futures.process import _WorkItem
from datetime import datetime
import requests
from typing import List
from dateutil.parser import parse
import json
from itertools import islice

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

class JiraWorklogItem:
    def __init__(self, issueId: str, author: str, date: datetime, timeSpentSeconds: int):
        self.issueId = issueId
        self.author = author
        self.date = date
        self.timeSpentSeconds = timeSpentSeconds


class JiraApi:

    def __init__(self, baseUrl, user, password, maxResultsPerRequest=25):
        self.baseUrl = baseUrl
        self.user = user
        self.password = password
        self.maxResultsPerRequest = maxResultsPerRequest


    def getUpdatedWorklogIdsSince(self, since: datetime) -> List[int]:
        isLastPage = False
        sinceUnixTimestampMs = int(since.timestamp() * 1000)
        workLogIds = []
        while isLastPage == False:
            jsonResponse = self._getUpdatedWorklogsSince(sinceUnixTimestampMs)
            sinceUnixTimestampMs = jsonResponse["until"] + 1
            isLastPage = jsonResponse["lastPage"]
            for worklogItem in jsonResponse["values"]:
                workLogIds.append(worklogItem["worklogId"])
        return workLogIds

    def getWorkLogItems(self, worklogItemIds: List[int], maxNrWorklogItemsInSingleRequest = 100) -> List[JiraWorklogItem]:
        nrOfWorkLogItems = len(worklogItemIds)
        nrOfIterations = int(nrOfWorkLogItems / maxNrWorklogItemsInSingleRequest)
        if ((nrOfWorkLogItems % maxNrWorklogItemsInSingleRequest) > 0):
            nrOfIterations += 1

        workLogItems = []
        for i in range(0, nrOfIterations):
            fromIndex = i * maxNrWorklogItemsInSingleRequest
            toIndex = fromIndex + maxNrWorklogItemsInSingleRequest
            if (fromIndex + maxNrWorklogItemsInSingleRequest > nrOfWorkLogItems):
                toIndex = nrOfWorkLogItems

            workLogItemsForRequest = list(islice(worklogItemIds, fromIndex, toIndex))
            jsonResponse = self._getWorklogs(workLogItemsForRequest)
            for worklogItem in jsonResponse:
                author = worklogItem["author"]["displayName"]
                issueId = worklogItem["issueId"]
                date = parse(worklogItem["started"])
                timeSpentSeconds = worklogItem["timeSpentSeconds"]

                worklogItem = JiraWorklogItem(issueId, author, date, timeSpentSeconds)
                workLogItems.append(worklogItem)

        return workLogItems


    def _getUpdatedWorklogsSince(self, sinceUnixTimeStampMs: float):
        requestUrl = self.baseUrl + 'rest/api/3/worklog/updated'
        defaultHeaders = {'Content-Type':'application/json'}
        queryParams = {'since':sinceUnixTimeStampMs}
        timeoutSeconds = 10

        response = requests.get(requestUrl, headers=defaultHeaders, params=queryParams, auth=(self.user, self.password), timeout=timeoutSeconds)
        response.raise_for_status
        return response.json()

    def _getWorklogs(self, worklogIds: List[int]):
        requestUrl = self.baseUrl + 'rest/api/3/worklog/list'
        defaultHeaders = {'Content-Type':'application/json'}
        timeoutSeconds = 10
        requestBody = { "ids": worklogIds }

        response = requests.post(requestUrl, headers=defaultHeaders, auth=(self.user, self.password), data=json.dumps(requestBody), timeout=timeoutSeconds)
        response.raise_for_status
        return response.json()
        


