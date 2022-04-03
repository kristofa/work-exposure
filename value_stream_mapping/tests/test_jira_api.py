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

    def test_getIssue_no_parent_with_labels(self):
        with open(os.path.join(self.directoryCurrentFile, 'jira_get_issue_no_parent_with_labels.json')) as file:
            with responses.RequestsMock() as rsps:
                rsps.add(
                    method=responses.GET,
                    url='https://jira.com/rest/api/3/issue/40054',
                    json=json.load(file),
                    status=200)

                api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd')
                jiraIssue = api.getIssue(issueId='40054')
                self.assertEqual(jiraIssue.issueId, '40054')
                self.assertEqual(jiraIssue.issueKey, 'CP-6384')
                self.assertEqual(jiraIssue.epic, None)
                self.assertEqual(jiraIssue.labels, ['ANALYSES', '2ndlabel'])

    def test_getIssue_with_parent_no_labels(self):
        with open(os.path.join(self.directoryCurrentFile, 'jira_get_issue_with_parent_no_labels.json')) as file:
            with responses.RequestsMock() as rsps:
                rsps.add(
                    method=responses.GET,
                    url='https://jira.com/rest/api/3/issue/40576',
                    json=json.load(file),
                    status=200)

                api = jira_api.JiraApi(baseUrl='https://jira.com/', user='aUser', password='aPwd')
                jiraIssue = api.getIssue(issueId='40576')
                self.assertEqual(jiraIssue.issueId, '40576')
                self.assertEqual(jiraIssue.issueKey, 'CP-6615')
                self.assertEqual(jiraIssue.epic.key, 'CP-6495')
                self.assertEqual(jiraIssue.epic.description, 'Pilot developments')
                self.assertEqual(jiraIssue.labels, [])


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
