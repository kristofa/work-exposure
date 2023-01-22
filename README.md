# work exposure

Exposes a team's work by exporting data from [JIRA](https://www.atlassian.com/software/jira).

*I realize that I didn't use the Python naming conventions when it comes variable and function names... sorry about that...*

## Exporters

**Currently all the exporters are based on JIRA worklogs. If you don't log work using the JIRA worklogs functionality you won't get any useful data out of it.**

As input the exporters takes a 'from' and 'to' date, the range between which data should be exported. 

The exports are CSV files and also a [PlantUML](https://plantuml.com) file that can be used to visualize the work.

### Time by epic

This exporter exports 4 files all related to the time spent on epics.

#### epic overview summary

Exports a CSV file with a single record with structure:

```
from|to|total_workdays_logged_on_epics|total_workdays_logged
```

It exports the total amount of logged workdays (1 workday = 8 hours) on epics and the total amount of workdays logged on JIRA issues not linked to any epic.

#### epic overview

Exports per epic the total workdays logged. Structure of CSV file:

```
epicKey|epicName|total_workdays_logged
```

#### epic overview by person

Exports by epic and person the total number of workdays logged.

```
epicKey|epicName|person|total_workdays_logged
```

#### issues without epic assigned

Exports the Jira issues on which time is logged but which have no epic assigned. Purpose of this is to spot if there are issues which should have been assigned to an epic but they are not.

Structure of CSV:

```
issueKey|description
```

### Time by work type

This exporter supports exporting time spent per type of work. The different types of work can be defined by adding labels to the JIRA issues that look like this: `worktype:<name>`.

We for example have defined following work types:

   * `worktype:software_development`
   * `worktype:operational_support`
   * `worktype:project_management`
   * ...

This can be useful to for example find out how much time was spent on planned vs unplanned work.

#### work type overview summary

Exports a CSV file with a single record with structure:

```
from|to|total_workdays_logged_items_with_worktype|total_workdays_logged
```

It shows the total workdays logged and the total workdays logged on jira issues which have a worktype label.
If you expect that every issue has a 'work type' defined this shows you for which percentage of the logged time a work type is missing.

#### work type overview

Exports a CSV with the total workdays logged per work type. Structure:

```
worktype|total_workdays_logged
```

#### work type overview per person

Exports a CSV file with the time spent per work type per person.

Structure of the CSV file:

```
worktype|person|total_workdays_logged
```

#### issues without work type assigned

Exports a CSV file with the JIRA issues on which time is logged but which don't have a work type assigned.
This allows you to add a work type to these issues so you can generate more accurate results.


```
issueKey|description
```

### Flow efficiency by epic

This exporter calculates the flow efficiency per epic and also exports a PlantUML Gantt chart which shows how time was spent on epics.


#### 'Work in progress' overview Gantt chart

We create a [PlantUML Gantt chart file](https://plantuml.com/gantt-diagram) (extension .pu) that visualizes how time was spent on an epic.
When time was logged for a particular day, the day will be coloured on the Gantt chart. The days for which no time was logged remain blank.
In this way it becomes visually clear if we continuously worked on a specific epic and probably have a high flow efficiency or if there were a lot of breaks and gaps in the chart.

![epic_work_in_progress_overview_from_2022-01-01_until_2022-04-15](https://user-images.githubusercontent.com/2221492/191255729-59564eac-950d-47a5-b89a-a7223739ee6f.png)

#### Flow efficiency be epic

For each of the epics we calculate the flow efficiency.

To calculate the flow efficiency per epic we take the first and last worklog for the epic within our time range and we calculate the number of workdays between both dates (we only take monday - friday into account). 
This is considered total time. 

Next we calculate the actual time logged in the same period. This is considered active time.

We calculate flow efficiency by: active time / total time = flow efficiency

The CSV export format looks like this:


```
epicKey|epicName|flow_efficiency
```


## Python - set up

You'll need Python 3.9 or higher.

Set-up you virtual env for the project:

```
python3 -m venv venv
```

Run `source venv/bin/activate` to set up the python environment

Install dependencies as specified in `requirements.txt`: `pip install -r requirements.txt`

## Python - running tests

Run all unit tests: `python -m unittest`
Run individual unit test: `python -m work_exposure.tests.test_jira_api`


## Generating the exports

Before you generate the exports you have to generate a config file named `worklog_based_export.ini` in the main directory of this repository.
The file looks like this:

```
[DEFAULT]
# The dates in between to export metrics.
fromDate = 2022-04-15 00:00:00.000+02:00
toDate = 2022-10-07 00:00:00.000+02:00

[jira]
# Jira api details. We don't support storing the password (api token) in the config file. You will be asked to provide it at runtime.
jiraBaseUrl = https://company.atlassian.net/
jiraUser = first.lastname@company.com
```

The password (API token) for the user isn't in the config file and will be asked when you start to script:

```
python3 worklog_based_export.py
```


