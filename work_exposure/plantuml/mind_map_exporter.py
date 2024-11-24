from typing import List
from typing import Dict
from functools import total_ordering

@total_ordering
class IssueWithClassification:
    def __init__(self, key:str, description: str, loggedTimeMinutes: int, classification: str ):
        self.key = key
        self.description = description
        self.loggedTimeMinutes = loggedTimeMinutes
        self.classification = classification

    def __lt__(self, obj):
        return ((self.loggedTimeMinutes) < (obj.loggedTimeMinutes))
    
    def __eq__(self, obj):
        return (self.loggedTimeMinutes == obj.loggedTimeMinutes)
        

@total_ordering
class Classification:
    def __init__(self, classification: str):
        self.classification = classification
        self.totalMinutesLogged = 0
        self.issues: List[IssueWithClassification] = []

    def add(self, issue: IssueWithClassification):
        self.issues.append(issue)
        self.issues = sorted(self.issues, reverse=True)
        self.totalMinutesLogged += issue.loggedTimeMinutes


    def __lt__(self, obj):
        return ((self.totalMinutesLogged) < (obj.totalMinutesLogged))
    
    def __eq__(self, obj):
        if (obj == None):
            return False
        return (self.totalMinutesLogged == obj.totalMinutesLogged)


class MindMapExporter:

    def __init__(self, fileNameIncludingIssues: str, fileNameNotIncludingIssues, title: str):
        self.fileNameIncludingIssues = fileNameIncludingIssues
        self.fileNameNotIncludingIssues = fileNameNotIncludingIssues
        self.title = title
        self.classifications: Dict[str, Classification] = {}        

    def export(self, issuesWithClassification: List[IssueWithClassification]):
        
        totalNrOfIssues = 0
        totalNrOfMinutes = 0
        for issue in issuesWithClassification:
            classification = self.classifications.get(issue.classification)
            if classification == None:
                classification = Classification(issue.classification)
                self.classifications[issue.classification] = classification
            classification.add(issue)
            totalNrOfIssues += 1
            totalNrOfMinutes += issue.loggedTimeMinutes
        
        orderedListOfClassifications = sorted(list(self.classifications.values()), reverse=True)
        totalNrOfDays = round(totalNrOfMinutes / 60 / 8)
        centerNodeText = ':{0}\nissues={1} - logged days={2};'.format(self.title, totalNrOfIssues, totalNrOfDays)

        leftClassifications = []
        rightClassifications = []

        left = True
        for classification in orderedListOfClassifications:
            if (left == True):
                leftClassifications.append(classification)
            else:
                rightClassifications.append(classification)

            if left == True:
                left = False
            else:
                left = True

        self._writeFileNotIncludingIssues(centerNodeText, rightClassifications, leftClassifications)
        self._writeFileIncludingIssues(centerNodeText, rightClassifications, leftClassifications)



    def _writeFileNotIncludingIssues(self, centerNodeText: str, rightClassifications: List[Classification], leftClassifications: List[Classification]):
        with open(self.fileNameNotIncludingIssues, 'w') as mindMapFile:
            mindMapFile.write('@startmindmap\n')
            mindMapFile.write('*{0}\n'.format(centerNodeText))

            for classification in rightClassifications:
                self._writeClassification(mindMapFile, classification, False)

            mindMapFile.write('\n\nleft side\n\n')

            for classification in leftClassifications:
                self._writeClassification(mindMapFile, classification, False)

            mindMapFile.write('@endmindmap\n')


    def _writeFileIncludingIssues(self, centerNodeText: str, rightClassifications: List[Classification], leftClassifications: List[Classification]):
        with open(self.fileNameIncludingIssues, 'w') as mindMapFile:
            mindMapFile.write('@startmindmap\n')
            mindMapFile.write('*{0}\n'.format(centerNodeText))

            for classification in rightClassifications:
                self._writeClassification(mindMapFile, classification, True)

            mindMapFile.write('\n\nleft side\n\n')

            for classification in leftClassifications:
                self._writeClassification(mindMapFile, classification, True)

            mindMapFile.write('@endmindmap\n')


    def _writeClassification(self, file, classification: Classification, issueDetails: bool):
        if (classification.totalMinutesLogged >= (60*8)):
            file.write('**:{0}\nissues={1} - logged days={2};\n'.format(classification.classification, len(classification.issues), round(classification.totalMinutesLogged / (60 * 8), 1)))
        elif (classification.totalMinutesLogged >= 60):
            file.write('**:{0}\nissues={1} - logged hours={2};\n'.format(classification.classification, len(classification.issues), round(classification.totalMinutesLogged / 60, 1)))
        else:
            file.write('**:{0}\nissues={1} - logged minutes={2};\n'.format(classification.classification, len(classification.issues), classification.totalMinutesLogged))

        if (issueDetails == True):
            for issue in classification.issues:
                file.write('***:{0} - {1}\nlogged hours={2};\n'.format(issue.key, issue.description, round(issue.loggedTimeMinutes / 60, 2)))
                   
    

