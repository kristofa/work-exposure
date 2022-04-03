from datetime import datetime
from value_stream_mapping.jira import jira_api
import unittest
import responses
import json
import os
import sys
from dateutil.parser import parse
from responses import matchers

class TestJiraApi(unittest.TestCase):

    directoryCurrentFile = os.path.dirname(os.path.realpath(__file__))

    """
    Tests retrieving issues in case retrieving all available issues are returned in the first request.
    Tests support for status changes, indicating if issue is part of sprint and indicating if issue was
    flagged / blocked.
    """
    def test_getIssuesFor_singleCall(self):
        with open(os.path.join(self.directoryCurrentFile, 'jira_search_all_issues_single_response.json')) as file:
            with responses.RequestsMock() as rsps:
                rsps.add(
                    method=responses.GET,
                    url='https://jira.com/rest/api/2/search?jql=project=PROJECTKEY&startAt=0&maxResults=25&fields=key,issuetype&expand=changelog',
                    json=json.load(file),
                    status=200)

                api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd')
                issues = api.getIssuesFor(projectKey="PROJECTKEY")
                self._validate_getIssuesFor_response(issues)


    """
    Tests retrieving issues in case not all available issues are returned in the first request but split
    across two requests
    """
    def test_getIssuesFor_multipleCalls(self):
        with open(os.path.join(self.directoryCurrentFile, 'jira_search_all_issues_multiple_responses_part1.json')) as file1:
            with open(os.path.join(self.directoryCurrentFile, 'jira_search_all_issues_multiple_responses_part2.json')) as file2:
                with responses.RequestsMock() as rsps:
                    rsps.add(
                        method=responses.GET,
                        url='https://jira.com/rest/api/2/search?jql=project=PROJECTKEY&startAt=0&maxResults=2&fields=key,issuetype&expand=changelog',
                        json=json.load(file1),
                        status=200)
                    rsps.add(
                        method=responses.GET,
                        url='https://jira.com/rest/api/2/search?jql=project=PROJECTKEY&startAt=2&maxResults=2&fields=key,issuetype&expand=changelog',
                        json=json.load(file2),
                        status=200)

                    api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd', maxResultsPerRequest=2)
                    issues = api.getIssuesFor(projectKey="PROJECTKEY")
                    self._validate_getIssuesFor_response(issues)
        

    def _validate_getIssuesFor_response(self, issues):
        self.assertEqual(len(issues), 3)
                
        firstIssue = issues[0]
        self.assertEqual(firstIssue.issueKey, 'PROJECTKEY-459')
        self.assertEqual(firstIssue.issueType, 'Bug')
        self.assertEqual(firstIssue.hasBeenBlocked, False)
        self.assertEqual(firstIssue.hasBeenPartOfSprint, False)
        self.assertEqual(len(firstIssue.changes), 0)

        secondIssue = issues[1]
        self.assertEqual(secondIssue.issueKey, 'PROJECTKEY-456')
        self.assertEqual(secondIssue.issueType, 'Story')
        self.assertEqual(secondIssue.hasBeenBlocked, True)
        self.assertEqual(secondIssue.hasBeenPartOfSprint, True)
        self.assertEqual(len(secondIssue.changes), 2)

        secondIssueFirstChange = secondIssue.changes[0]
        self.assertEqual(secondIssueFirstChange.date, parse('2021-05-11T14:07:51.000+0200'))
        self.assertEqual(secondIssueFirstChange.fromStatus, 'Open')
        self.assertEqual(secondIssueFirstChange.toStatus, 'In Progress')

        secondIssueSecondChange = secondIssue.changes[1]
        self.assertEqual(secondIssueSecondChange.date, parse('2021-05-11T14:20:45.000+0200'))
        self.assertEqual(secondIssueSecondChange.fromStatus, 'In Progress')
        self.assertEqual(secondIssueSecondChange.toStatus, 'In Review')

        thirdIssue = issues[2]
        self.assertEqual(thirdIssue.issueKey, 'PROJECTKEY-458')
        self.assertEqual(thirdIssue.issueType, 'Story')
        self.assertEqual(thirdIssue.hasBeenBlocked, False)
        self.assertEqual(thirdIssue.hasBeenPartOfSprint, False)
        self.assertEqual(len(thirdIssue.changes), 1)

        thirdIssueFirstChange = thirdIssue.changes[0]
        self.assertEqual(thirdIssueFirstChange.date, parse('2021-05-12T11:31:39.000+0200'))
        self.assertEqual(thirdIssueFirstChange.fromStatus, 'Open')
        self.assertEqual(thirdIssueFirstChange.toStatus, 'In Progress')


    """
    Tests retrieving worklog ids that have been updated since a given datetime.
    """
    def test_getUpdatedWorklogIdsSince_singleCall(self):
        since = datetime.fromisoformat('2022-01-01')
        sinceUnixTimeStampMs = int(since.timestamp() * 1000)
        with open(os.path.join(self.directoryCurrentFile, 'jira_get_updated_worklog_ids_single_response.json')) as file:
            with responses.RequestsMock() as rsps:
                rsps.add(
                    method=responses.GET,
                    url='https://jira.com/rest/api/3/worklog/updated?since=' + str(sinceUnixTimeStampMs),
                    json=json.load(file),
                    status=200)

                api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd')
                workLogIds = api.getUpdatedWorklogIdsSince(since=since)
                self.assertEqual(workLogIds, [40029, 40030, 40031, 40032, 40744])
    
    """
    Tests retrieving worklog ids that have been updated since a given datetime but when
    not all worklogs fit in the first request.
    """
    def test_getUpdatedWorklogIdsSince_multipleCalls(self):
        since = datetime.fromisoformat('2022-01-01')
        sinceUnixTimeStampMs = int(since.timestamp() * 1000)
        with open(os.path.join(self.directoryCurrentFile, 'jira_get_updated_worklog_ids_multiple_responses_part1.json')) as file1:
            with open(os.path.join(self.directoryCurrentFile, 'jira_get_updated_worklog_ids_multiple_responses_part2.json')) as file2:
                with responses.RequestsMock() as rsps:
                    rsps.add(
                        method=responses.GET,
                        url='https://jira.com/rest/api/3/worklog/updated?since=' + str(sinceUnixTimeStampMs),
                        json=json.load(file1),
                        status=200)
                    rsps.add(
                        method=responses.GET,
                        url='https://jira.com/rest/api/3/worklog/updated?since=1641214457686',
                        json=json.load(file2),
                        status=200)

                    api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd')
                    workLogIds = api.getUpdatedWorklogIdsSince(since=since)
                    self.assertEqual(workLogIds, [40029, 40030, 40031, 40032, 40744])

    """
    Tests retrieving worklog items based on worklog item ids.
    """
    def test_getWorkLogItems_singleCall(self):
        with open(os.path.join(self.directoryCurrentFile, 'jira_get_worklog_items_single_response.json')) as file:
            with responses.RequestsMock() as rsps:
                rsps.add(
                    method=responses.POST,
                    url='https://jira.com/rest/api/3/worklog/list',
                    match=[matchers.json_params_matcher({"ids": [40031, 40032, 40744]})],
                    json=json.load(file),
                    status=200)

                api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd')
                worklogItems = api.getWorkLogItems(worklogItemIds=[40031, 40032, 40744])
                self._validate_getWorklogItems_response(worklogItems)

    """
    Tests retrieving worklog items based on worklog item ids when needing more than 1 call
    """
    def test_getWorkLogItems_TwoCalls(self):
        with open(os.path.join(self.directoryCurrentFile, 'jira_get_worklog_items_two_responses_part1.json')) as file1:
            with open(os.path.join(self.directoryCurrentFile, 'jira_get_worklog_items_two_responses_part2.json')) as file2:
                with responses.RequestsMock() as rsps:
                    rsps.add(
                        method=responses.POST,
                        url='https://jira.com/rest/api/3/worklog/list',
                        match=[matchers.json_params_matcher({"ids": [40031, 40032]})],
                        json=json.load(file1),
                        status=200)
                    rsps.add(
                        method=responses.POST,
                        url='https://jira.com/rest/api/3/worklog/list',
                        match=[matchers.json_params_matcher({"ids": [40744]})],
                        json=json.load(file2),
                        status=200)

                    api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd')
                    worklogItems = api.getWorkLogItems(worklogItemIds=[40031, 40032, 40744], maxNrWorklogItemsInSingleRequest=2)
                    self._validate_getWorklogItems_response(worklogItems)

    """
    Tests retrieving worklog items based on worklog item ids when needing 3 calls
    """
    def test_getWorkLogItems_ThreeCalls(self):
        with open(os.path.join(self.directoryCurrentFile, 'jira_get_worklog_items_three_responses_part1.json')) as file1:
            with open(os.path.join(self.directoryCurrentFile, 'jira_get_worklog_items_three_responses_part2.json')) as file2:
                with open(os.path.join(self.directoryCurrentFile, 'jira_get_worklog_items_three_responses_part3.json')) as file3:
                    with responses.RequestsMock() as rsps:
                        rsps.add(
                            method=responses.POST,
                            url='https://jira.com/rest/api/3/worklog/list',
                            match=[matchers.json_params_matcher({"ids": [40031]})],
                            json=json.load(file1),
                            status=200)
                        rsps.add(
                            method=responses.POST,
                            url='https://jira.com/rest/api/3/worklog/list',
                            match=[matchers.json_params_matcher({"ids": [40032]})],
                            json=json.load(file2),
                            status=200)
                        rsps.add(
                            method=responses.POST,
                            url='https://jira.com/rest/api/3/worklog/list',
                            match=[matchers.json_params_matcher({"ids": [40744]})],
                            json=json.load(file3),
                            status=200)

                        api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd')
                        worklogItems = api.getWorkLogItems(worklogItemIds=[40031, 40032, 40744], maxNrWorklogItemsInSingleRequest=1)
                        self._validate_getWorklogItems_response(worklogItems)


    def _validate_getWorklogItems_response(self, worklogItems):
        self.assertEqual(len(worklogItems), 3)

        firstWorklogItem = worklogItems[0]
        self.assertEqual(firstWorklogItem.issueId, '39895')
        self.assertEqual(firstWorklogItem.author, 'John Doe')
        self.assertEqual(firstWorklogItem.date, parse('2022-01-03T09:53:42.724+0100'))
        self.assertEqual(firstWorklogItem.timeSpentSeconds, 14400)

        secondWorklogItem = worklogItems[1]
        self.assertEqual(secondWorklogItem.issueId, '40011')
        self.assertEqual(secondWorklogItem.author, 'Peter Selie')
        self.assertEqual(secondWorklogItem.date, parse('2022-01-03T15:30:09.333+0100'))
        self.assertEqual(secondWorklogItem.timeSpentSeconds, 3600)

        thirdWorklogItem = worklogItems[2]
        self.assertEqual(thirdWorklogItem.issueId, '40054')
        self.assertEqual(thirdWorklogItem.author, 'Maria Sharapova')
        self.assertEqual(thirdWorklogItem.date, parse('2022-03-29T00:00:00.000+0200'))
        self.assertEqual(thirdWorklogItem.timeSpentSeconds, 18000)


if __name__ == '__main__':
    unittest.main()
