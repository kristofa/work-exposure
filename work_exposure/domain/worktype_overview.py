from datetime import datetime
from typing import List
from typing import Dict


class WorkTypeOverview:

    def __init__(self, since:datetime):
        self.since = since
        self.totalSecondsSpent = 0
        self.totalSecondsSpentOnItemsWithWorkType = 0
        self.ticketsWithoutWorkType: List[Issue] = []
        self.overviewByWorkType: List[TimeByWorkType] = []


class TimeByWorkType:

    def __init__(self, workType:str):
        self.workType = workType
        self.totalSecondsSpent = 0
        self.totalSecondsByPerson: Dict[str, int] = {}
        self.totalSecondsByIssue: Dict[str, int] = {}

class Issue:

    def __init__(self, issueKey:str, issueDescription:str):
        self.issueKey = issueKey
        self.description = issueDescription
