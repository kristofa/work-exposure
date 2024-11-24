import sys
import csv
from typing import List
from work_exposure.plantuml import mind_map_exporter

if (len(sys.argv) != 2):
    print('Expect one command-line argument with the path to the CSV file name with JIRA issues and label to add to the issue')
    sys.exit(-1)

mindMapExporter = mind_map_exporter.MindMapExporter(fileNameIncludingIssues='mindmap_including_issues.pu', fileNameNotIncludingIssues='mindmap.pu', title='Unplanned work classification\n1st of Oct - 15th of Nov 2024')
issues : List[mind_map_exporter.IssueWithClassification] = []

with open(sys.argv[1], 'rt') as f:
    csv_reader = csv.reader(f, delimiter='|')
    header = True
    for row in csv_reader:
        if (header):
            if (len(row) != 5):
                print('Expected 5 header values. Expected: worktype|issue|description|total_minutes_logged|classification but got '+ '|'.join(row))
                sys.exit(-3)
            elif (row[0] != 'worktype' or row[1] != 'issue' or row[2] != 'description' or row[3] != 'total_minutes_logged' or row[4] != 'classification'):
                print('Unexpected header values. Expected: worktype|issue|description|total_minutes_logged|classification but got '+ '|'.join(row))
                sys.exit(-4)
            header = False
        else:
            if (len(row) != 5):
                print('Expected 5 values. Expected: worktype|issue|description|total_minutes_logged|classification but got '+ '|'.join(row))
                sys.exit(-5)
            loggedTimeAsInt = round(float(row[3]))
            issues.append(mind_map_exporter.IssueWithClassification(key=row[1], description=row[2], loggedTimeMinutes=loggedTimeAsInt, classification=row[4]))
            
    mindMapExporter.export(issues)
    