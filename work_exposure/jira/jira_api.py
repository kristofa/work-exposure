from concurrent.futures.process import _WorkItem
from datetime import datetime
import requests
from typing import List
from dateutil.parser import parse
import json
from itertools import islice


class JiraIssue:
    def __init__(self, issueId, issueKey, description):
        self.issueId = issueId
        self.issueKey = issueKey
        self.description = description
        self.epic = None
        self.labels = []

    def addLabel(self, labelValue: str):
        self.labels.append(labelValue)

class JiraEpic:
    def __init__(self, key, description, colour):
        self.key = key
        self.description = description
        self.colour = colour


class JiraWorklogItem:
    def __init__(self, issueId: str, author: str, date: datetime, timeSpentSeconds: int):
        self.issueId = issueId
        self.author = author
        self.date = date
        self.timeSpentSeconds = timeSpentSeconds


class JiraApi:


    # These colours are retrieved using the API by assigning an epic the different colours
    # available in JIRA, next use Digital Colour Meter on macos to get the RGB values
    # because the JIRA api doesn't define those :-(
    # These colours might be different depending on the JIRA version that's used...
    # So it is probably better to make these configurable later.
    jiraEpicColourToHexColour = {
        'purple': '#8478D3',
        'blue': '#4382F7',
        'green': '#7CD6A7',
        'teal': '#5AC4E2',
        'yellow': '#F6C644',
        'orange': '#EE7C5C',
        'grey': '#6E778A',
        'dark_purple': '#5044A4',
        'dark_blue': '#2151C5',
        'dark_green': '#3A855D',
        'dark_teal': '#48A0BC',
        'dark_yellow': '#F19E41',
        'dark_orange': '#CC4525',
        'dark_grey': '#293756'
    }

    # dictionary will be built up as we process different epics
    jiraEpicColours = {}

    # name of the custom field that contains the jira epic colour
    jiraCustomFieldRepresentingEpicColor = 'customfield_11016'

    # fallback colour in case we can't get colour from api or in case we don't have mapping from
    # jira value to hex value. Fall back to a bright yellow colour.
    jiraEpicFallbackColour = '#fcf803'

    def __init__(self, baseUrl, user, password, maxResultsPerRequest=25):
        self.baseUrl = baseUrl
        self.user = user
        self.password = password
        self.maxResultsPerRequest = maxResultsPerRequest


    def getUpdatedWorklogIdsSince(self, since: datetime) -> List[int]:
        print('Getting updated worklog ids since', since)
        isLastPage = False
        sinceUnixTimestampMs = int(since.timestamp() * 1000)
        workLogIds = []
        while isLastPage == False:
            print('Querying page')
            jsonResponse = self._getUpdatedWorklogsSince(sinceUnixTimestampMs)
            sinceUnixTimestampMs = jsonResponse["until"] + 1
            isLastPage = jsonResponse["lastPage"]
            for worklogItem in jsonResponse["values"]:
                workLogIds.append(worklogItem["worklogId"])
        return workLogIds

    def getWorkLogItems(self, worklogItemIds: List[int], toDate: datetime, maxNrWorklogItemsInSingleRequest = 100) -> List[JiraWorklogItem]:
        print('Getting worklog items')
        nrOfWorkLogItems = len(worklogItemIds)
        nrOfIterations = int(nrOfWorkLogItems / maxNrWorklogItemsInSingleRequest)
        if ((nrOfWorkLogItems % maxNrWorklogItemsInSingleRequest) > 0):
            nrOfIterations += 1

        workLogItems = []
        for i in range(0, nrOfIterations):
            print('iteration', i, '/', nrOfIterations)
            fromIndex = i * maxNrWorklogItemsInSingleRequest
            toIndex = fromIndex + maxNrWorklogItemsInSingleRequest
            if (fromIndex + maxNrWorklogItemsInSingleRequest > nrOfWorkLogItems):
                toIndex = nrOfWorkLogItems

            workLogItemsForRequest = list(islice(worklogItemIds, fromIndex, toIndex))
            jsonResponse = self._getWorklogs(workLogItemsForRequest)
            for worklogItem in jsonResponse:
                date = parse(worklogItem["started"])
                if (toDate != None and date <= toDate):
                    author = worklogItem["author"]["displayName"]
                    issueId = worklogItem["issueId"]
                    timeSpentSeconds = worklogItem["timeSpentSeconds"]

                    worklogItem = JiraWorklogItem(issueId, author, date, timeSpentSeconds)
                    workLogItems.append(worklogItem)

        return workLogItems

    def getIssue(self, issueId: str) -> JiraIssue:
        requestUrl = self.baseUrl + 'rest/api/3/issue/' + issueId
        defaultHeaders = {'Content-Type':'application/json'}
        queryParams = {'fields':'parent,labels,summary,issuetype'}
        timeoutSeconds = 10

        response = requests.get(requestUrl, headers=defaultHeaders, params=queryParams, auth=(self.user, self.password), timeout=timeoutSeconds)
        response.raise_for_status
        jsonResponse = response.json()

        issueKey = jsonResponse["key"]
        issueDescription = jsonResponse["fields"]["summary"]
        jiraIssue = JiraIssue(issueId=issueId, issueKey=issueKey, description=issueDescription)

        fieldsJsonObject = jsonResponse["fields"]
        if 'labels' in fieldsJsonObject:
            for labelValue in jsonResponse["fields"]["labels"]:
                jiraIssue.addLabel(labelValue)

        if 'parent' in fieldsJsonObject:
            parentField = jsonResponse["fields"]["parent"]
            epicKey = parentField["key"]
            epicDescription = parentField["fields"]["summary"]
            epicColour = self._getEpicColour(epicKey)
            jiraIssue.epic = JiraEpic(key=epicKey, description=epicDescription, colour=epicColour)
        else:
            # If we have no parent it could be that time is logged to the epic itself
            if 'issuetype' in fieldsJsonObject:
                issueTypeField = issuetypefield = jsonResponse["fields"]["issuetype"]
                issueTypeName = issueTypeField["name"]
                if (issueTypeName == "Epic"):
                    epicKey = issueKey
                    epicDescription = issueDescription
                    epicColour = self._getEpicColour(epicKey)
                    jiraIssue.epic = JiraEpic(key=epicKey, description=epicDescription, colour=epicColour)

        return jiraIssue


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

    def _getEpicColour(self, epicKey: str):
        if epicKey in self.jiraEpicColours:
            return self.jiraEpicColours[epicKey]
        else:
            requestUrl = self.baseUrl + 'rest/api/3/issue/' + epicKey
            defaultHeaders = {'Content-Type':'application/json'}
            queryParams = {'fields': self.jiraCustomFieldRepresentingEpicColor}
            timeoutSeconds = 10

            response = requests.get(requestUrl, headers=defaultHeaders, params=queryParams, auth=(self.user, self.password), timeout=timeoutSeconds)
            response.raise_for_status
            jsonResponse = response.json()
            if 'fields' in jsonResponse:
                fieldsJsonObject = jsonResponse["fields"]
                if self.jiraCustomFieldRepresentingEpicColor in fieldsJsonObject: 
                    jiraEpicColour = jsonResponse["fields"][self.jiraCustomFieldRepresentingEpicColor]
                    hexColour = self.jiraEpicColourToHexColour.get(jiraEpicColour, self.jiraEpicFallbackColour) 
                    self.jiraEpicColours[epicKey] =  hexColour
                    return hexColour

            print("Can't find customfield that represents epic colour: " + self.jiraCustomFieldRepresentingEpicColor)
            self.jiraEpicColours[epicKey] = self.jiraEpicFallbackColour
            return self.jiraEpicFallbackColour
