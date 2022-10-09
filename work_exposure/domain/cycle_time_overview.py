from datetime import date, timedelta
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

    def __init__(self, itemKey: str, itemDescription: str, itemColour: str):
        self.itemKey = itemKey
        self.itemDescription = itemDescription
        self.itemColour = itemColour
        self.inProgress: List[ItemInProgress] = []
        self.totalTimeLoggedInSeconds = 0

    def getsInProgressOrdered(self) -> List[ItemInProgress]:
        return sorted(self.inProgress)

    def flowEfficiency(self) -> float:
        sortedItems = sorted(self.inProgress)
        if (len(sortedItems) == 0):
            return 0
        elif (len(sortedItems) == 1):
            return 1
        else:
            firstItem = sortedItems[0]
            lastItem = sortedItems[len(sortedItems)-1]
            datesInRange = (firstItem.start + timedelta(idx + 1)
                for idx in range((lastItem.end - firstItem.start).days))
            weekdaysInRange = sum(1 for day in datesInRange if day.weekday() < 5) + 1
            weekdaysLogged = self._secondsToWorkDays(self.totalTimeLoggedInSeconds)
            return round(weekdaysLogged / weekdaysInRange, 2)

    def _secondsToWorkDays(self, seconds):
        return round(seconds / 60 / 60 / 8, 1)