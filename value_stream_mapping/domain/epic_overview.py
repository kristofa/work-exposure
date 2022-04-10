from datetime import datetime
from typing import List
from typing import Dict

class EpicOverview:

    def __init__(self, since:datetime):
        self.since = since
        self.totalSecondsSpent = 0
        self.totalSecondsSpentOnEpics = 0
        self.ticketsWithoutEpic:List[Issue] = []
        self.overviewByEpic:List[TimeByEpic] = []


class TimeByEpic:

    def __init__(self, epicKey:str, epicName:str):
        self.epicKey = epicKey
        self.epicName = epicName
        self.totalSecondsSpent = 0
        self.totalSecondsByPerson:Dict[str, int] = {}

class Issue:

    def __init__(self, issueKey:str, issueDescription:str):
        self.issueKey = issueKey
        self.description = issueDescription

