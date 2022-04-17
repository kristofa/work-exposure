import unittest
from datetime import date
from value_stream_mapping.domain import cycle_time_overview 

class TestCycletimeOverview(unittest.TestCase):

    def test_flowefficiency_no_items(self):
        overview = cycle_time_overview.ItemCycletimeOverview(itemKey="KEY", itemDescription="DESCRIPTION")
        self.assertEqual(overview.flowEfficiency(), 0)
    
    def test_flowefficiency_single_item(self):
        overview = cycle_time_overview.ItemCycletimeOverview(itemKey="KEY", itemDescription="DESCRIPTION")
        overview.inProgress.append(cycle_time_overview.ItemInProgress(start=date.fromisoformat('2022-04-15'), end=date.fromisoformat('2022-04-15')))
        self.assertEqual(overview.flowEfficiency(), 1)

    def test_flowefficiency_multiple_items(self):
        overview = cycle_time_overview.ItemCycletimeOverview(itemKey="KEY", itemDescription="DESCRIPTION")
        overview.inProgress.append(cycle_time_overview.ItemInProgress(start=date.fromisoformat('2022-04-15'), end=date.fromisoformat('2022-04-15')))
        overview.inProgress.append(cycle_time_overview.ItemInProgress(start=date.fromisoformat('2022-04-04'), end=date.fromisoformat('2022-04-04')))
        # 1 workday of total logged time
        overview.totalTimeLoggedInSeconds = (1 * 8 * 60 * 60)
        # 1 workday logged in a timeframe of 10 workdays = 0.1 flow efficiency
        self.assertEqual(overview.flowEfficiency(), 0.1)

    def test_flowefficiency_multiple_items_longer_timeframe(self):
        overview = cycle_time_overview.ItemCycletimeOverview(itemKey="KEY", itemDescription="DESCRIPTION")
        overview.inProgress.append(cycle_time_overview.ItemInProgress(start=date.fromisoformat('2022-04-15'), end=date.fromisoformat('2022-04-15')))
        overview.inProgress.append(cycle_time_overview.ItemInProgress(start=date.fromisoformat('2022-04-04'), end=date.fromisoformat('2022-04-04')))
        overview.inProgress.append(cycle_time_overview.ItemInProgress(start=date.fromisoformat('2022-03-22'), end=date.fromisoformat('2022-03-25')))
        # 3 workday of total logged time
        overview.totalTimeLoggedInSeconds = (3 * 8 * 60 * 60)
        # 3 workday logged in a timeframe of 19 workdays = 0.15 flow efficiency
        self.assertEqual(overview.flowEfficiency(), 0.16)