from datetime import date
from typing import List
import functools
from functools import total_ordering

@total_ordering
class ItemInProgress:

    def __init__(self, start: date, end: date):
        self.start = start
        self.end = end

    def __lt__(self, obj):
        return ((self.start) < (obj.start))
    
    def __eq__(self, obj):
        return (self.start == obj.start)

class ItemCycletimeOverview:

    def __init__(self, itemKey: str, itemDescription: str):
        self.itemKey = itemKey
        self.itemDescription = itemDescription
        self.inProgress: List[ItemInProgress] = []

    def getsInProgressOrdered(self):
        return sorted(self.inProgress)

    