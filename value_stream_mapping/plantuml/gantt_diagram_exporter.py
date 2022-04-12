from typing import List
from datetime import datetime
from value_stream_mapping.domain import cycle_time_overview

class GanttDiagramExporter:

    colors = ['AntiqueWhite', 'Aqua', 'BlueViolet', 'Coral', 'CornflowerBlue', 'Crimson', 'DarkKhaki', 'DarkGreen', 'Yellow', 'SpringGreen', 'Silver', 'SaddleBrown', 'RosyBrown', 'Salmon', 'RebeccaPurple', 'Plum', 'Pink']

    def __init__(self, title:str, fromDate: datetime, toDate: datetime):
        self.title = title
        self.fromDate = fromDate
        self.toDate = toDate

    def _getPlantUMLFilename(self, baseFilename: str):
        return baseFilename + '_from_'+self.fromDate.date().isoformat()+'_until_'+self.toDate.date().isoformat()+'.pu'

    def export(self, items: List[cycle_time_overview.ItemCycletimeOverview], outputFileName: str):
        with open(self._getPlantUMLFilename('epic_overview_summary'), 'w') as plantUMLFile:
            plantUMLFile.write('@startuml\n')
            plantUMLFile.write('Project starts {0}\n'.format(self.fromDate.date().isoformat()))
            plantUMLFile.write('saturday are closed\n')
            plantUMLFile.write('sunday are closed\n')

            epicCounter = 0
            for item in items:
                key = item.itemKey
                description = item.itemDescription
                inProgressCounter = 0
                nameOfFirstItemForEpic = description
                for inProgress in item.getsInProgressOrdered():
                    name = ''
                    if (inProgressCounter > 0):
                        name = str(epicCounter) + '_' + str(inProgressCounter)
                    else:
                        name = nameOfFirstItemForEpic
                    fromDateAsString = inProgress.start.isoformat()
                    toDateAsString = inProgress.end.isoformat()
                    plantUMLFile.write('[{0}] starts {1} and ends {2}\n'.format(name, fromDateAsString, toDateAsString))
                    plantUMLFile.write('[{0}] is colored in {1}\n'.format(name, self.colors[epicCounter]))
                    if (inProgressCounter > 0):
                        plantUMLFile.write('[{0}] displays on same row as [{1}]\n'.format(name, nameOfFirstItemForEpic ))
                    plantUMLFile.write('\n')
                    inProgressCounter += 1
                
                epicCounter += 1
            plantUMLFile.write('@enduml\n')    