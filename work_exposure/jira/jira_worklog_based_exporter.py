from . import jira_api

class JiraExporter:

    def process(self, worklogItem: jira_api.JiraWorklogItem, issue: jira_api.JiraIssue):
        """Processes a JIRA worklogItem and corresponding Jira issue"""
        pass

    def exportToFiles(self):
        """After processing the worklogItems, write out the summary to output fules"""
        pass