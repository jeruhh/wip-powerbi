# Measure Reference

30 measures, all defined on the `_Measures` table (a measure-only table with no data columns).

## Index

**[1] Hours** — `Actual Hrs`, `Actual Hrs (excl Break)`, `Billable Hrs`, `Billable Hrs %`, `Duration (Hrs)`, `Excess/Requirement`, `Non Billable Hrs`, `Std Hrs`, `Std vs Billable Hrs`

**[2] Revenue** — `Rev/Hr`, `Xero Rev Per Team`, `Xero vs Fct Rev`

**[3] Time Details Analysis** — `Current Month (Actual Hrs - Excl. Break)`, `Current Month (Actual Hrs)`, `Current Month (Billable Hrs Copy)`, `Current Month (Billable Hrs)`, `Current Month (Billable vs Std Hrs)`, `Current Month (Non Billable Hrs)`, `Current Month (Productivity Rate)`, `Current Month (Std Hrs)`, `Current vs Previous Month (Billable Hrs %)`, `Current vs Previous Month (Billable Hrs)`, `Previous Month (Billable Hrs)`, `TDA Title`

**[9] Others** — `Blank Column`, `Productivity Rate`, `Release Notes Title`, `Show Filters`, `Show Filters Header`, `Yesterday`

---

## [1] Hours

### `Actual Hrs`

```dax
CALCULATE(
    [Duration (Hrs)],
    DATESBETWEEN(
        'dim_date'[Date],
        DATE(2025, 1, 1),
        [Yesterday]
    ),
    FILTER(
        'fact_activities',
        'fact_activities'[tcRef] <> "ADMIN - LUNCH" && 'fact_activities'[deliverableName] <> "LUNCH" &&
        'fact_activities'[tcRef] <> "Unchargeable Hrs" &&
        'fact_activities'[deliverableName] <> "TIME IN AND OUT" &&
        'fact_activities'[teamName] <> "ADMIN" //check this
    )
)
```

### `Actual Hrs (excl Break)`

```dax
CALCULATE(
    [Duration (Hrs)],
    DATESBETWEEN(
        'dim_date'[Date],
        DATE(2025, 1, 1),
        [Yesterday]
    ),
    FILTER(
        'fact_activities',
        'fact_activities'[tcRef] <> "Unchargeable Hrs" &&
        'fact_activities'[tcRef] <> "ADMIN - Break" &&
        'fact_activities'[tcRef] <> "ADMIN - LUNCH" && 'fact_activities'[deliverableName] <> "LUNCH" &&
        'fact_activities'[teamName] <> "ADMIN" //check this
    )
)
```

### `Billable Hrs`

```dax
CALCULATE(
    [Duration (Hrs)],
    DATESBETWEEN(
        'dim_date'[Date],
        DATE(2025, 1, 1),
        [Yesterday]
    ),
    FILTER(
        'fact_activities',
        'fact_activities'[sla] <> "Admin" &&
        'fact_activities'[sla] <> "Operations" &&
        'fact_activities'[sla] <> "Workforce Experience" &&
        'fact_activities'[sla] <> "AP Automation" &&
        'fact_activities'[sla] <> "Automation" &&
        'fact_activities'[deliverableName] <> "HOLIDAY" &&

        //Special Cases
        'fact_activities'[teamName] <> "ADMIN" //check this
    )
)
```

### `Billable Hrs %`

Format string: `0.00%;-0.00%;0.00%`

```dax
DIVIDE([Billable Hrs], [Actual Hrs], BLANK())
```

### `Duration (Hrs)`

```dax
SUMX(
    fact_activities,
    IF(
        ISBLANK(fact_activities[leaveHours]),
        -- Calculate time difference and handle midnight crossing
        IF(
            ISBLANK(fact_activities[hours]),
            MOD(fact_activities[endTime] - fact_activities[startTime], 1) * 24,
            fact_activities[hours]
        ),
        fact_activities[leaveHours]
    )
)
```

### `Excess/Requirement`

```dax
[Actual Hrs] - [Std Hrs]
```

### `Non Billable Hrs`

```dax
CALCULATE(
    [Duration (Hrs)],
    DATESBETWEEN(
        'dim_date'[Date],
        DATE(2025, 1, 1),
        [Yesterday]
    ),
    FILTER(
        'fact_activities',
        'fact_activities'[sla] = "Admin" ||
        'fact_activities'[sla] = "Operations" ||
        'fact_activities'[sla] = "Workforce Experience" ||
        'fact_activities'[sla] = "AP Automation" ||
        'fact_activities'[deliverableName] = "HOLIDAY"
    ),
     FILTER(
        'fact_activities',
        'fact_activities'[tcRef] <> "Unchargeable Hrs" &&
        'fact_activities'[tcRef] <> "ADMIN - LUNCH" && 'fact_activities'[deliverableName] <> "LUNCH" &&
        'fact_activities'[deliverableName] <> "TIME IN AND OUT" &&
        'fact_activities'[teamName] <> "ADMIN" //check this
    )
)
```

### `Std Hrs`

```dax
 SUM('fact_client_data'[Standard Hours])
```

### `Std vs Billable Hrs`

Format string: `#,0.00`

```dax
VAR stdHrs = [Std Hrs]
VAR billableHrs = [Billable Hrs]

RETURN
stdHrs - billableHrs
```

## [2] Revenue

### `Rev/Hr`

```dax
[Xero Rev Per Team]/[Billable Hrs]
```

### `Xero Rev Per Team`

Format string: `\$#,0.00;(\$#,0.00);\$#,0.00`

```dax
// VAR CurrentTeamHours =
//     CALCULATE(
//         [Billable Hrs]
//         // Keep the 'TEAM' filter active for the numerator
//         // REMOVEFILTERS('fact_activities')
//     )

// VAR TotalClientHours =
//     CALCULATE(
//         [Billable Hrs],
//         // 1. Remove Team filter so the denominator represents ALL teams
//         REMOVEFILTERS('fact_activities'[teamName])
//     )

// VAR TotalClientRevenue =
//     CALCULATE(
//         SUM('fact_client_data'[Xero Revenue]),
//         // CRITICAL FIX: Ensure the Revenue ignores the Team slicer selection
//         REMOVEFILTERS('fact_activities'[teamName])
//     )

// VAR AllocatedRevenue =
//     DIVIDE(CurrentTeamHours, TotalClientHours, 0) * TotalClientRevenue

// RETURN
//     IF(
//         // Condition: Are there ZERO hours across the entire company?
//         ISBLANK(TotalClientHours) || TotalClientHours = 0,

//         // If true, check if we are on an individual team row
//         IF(
//             ISINSCOPE('fact_activities'[teamName]),
//             BLANK(),             // Hide it for individual teams so they don't duplicate
//             TotalClientRevenue   // Show the full revenue in the Total rows
//         ),

//         // Condition False: Hours exist, so allocate normally
//         AllocatedRevenue
//     )

//------------------------------------------------------------------------------------------------------------------------------------
VAR CurrentTeamHours =
    CALCULATE(
        [Billable Hrs]
        // Keep the 'TEAM' filter active for the numerator
    )

VAR TotalClientHours =
    CALCULATE(
        [Billable Hrs],
        REMOVEFILTERS('fact_activities'[teamName])
    )

VAR TotalClientRevenue =
    CALCULATE(
        SUM('fact_client_data'[Xero Revenue]),
        REMOVEFILTERS('fact_activities'[teamName])
    )

VAR AllocatedRevenue =
    DIVIDE(CurrentTeamHours, TotalClientHours, 0) * TotalClientRevenue

RETURN
    IF(
        // teamName is filtered (any source) AND that filter yields no billable hours -> blank
        ISFILTERED('fact_activities'[teamName]) && (ISBLANK(CurrentTeamHours) || CurrentTeamHours = 0),
        BLANK(),

        IF(
            ISBLANK(TotalClientHours) || TotalClientHours = 0,
            IF(
                ISFILTERED('fact_activities'[teamName]),
                BLANK(),
                TotalClientRevenue
            ),
            AllocatedRevenue
        )
    )
```

### `Xero vs Fct Rev`

Format string: `\$#,0.00;(\$#,0.00);\$#,0.00`

```dax
VAR fctRev = SUM('fact_client_data'[Forecasted Revenue])
VAR xeroRev = [Xero Rev Per Team]

RETURN
xeroRev - fctRev
```

## [3] Time Details Analysis

### `Current Month (Actual Hrs - Excl. Break)`

```dax
//Exclude break and unchargeable hours
VAR MinSel =
    CALCULATE( MIN('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MaxSel =
    CALCULATE( MAX('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MinAll =
    CALCULATE( MIN('Dim_Date'[Date]), ALL('Dim_Date') )
VAR MaxAll =
    CALCULATE( MAX('Dim_Date'[Date]), ALL('Dim_Date') )

-- If the selected range equals the full calendar, treat it as "no filter"
VAR HasDateSelection =
    NOT ( MinSel = MinAll && MaxSel = MaxAll )

VAR AnchorDate =
    IF( HasDateSelection, MinSel, TODAY() )

VAR StartDate =
    DATE( YEAR(AnchorDate), MONTH(AnchorDate), 1 )

VAR EndDate =
    EOMONTH( AnchorDate, 0 )

RETURN
CALCULATE(
    [Actual Hrs (excl Break)],
    // FILTER(
    //     'fact_activities',
    //     'fact_activities'[TCRef] <> "ADMIN - Break"
    // ),
    DATESBETWEEN('Dim_Date'[Date], StartDate, EndDate)
)
```

### `Current Month (Actual Hrs)`

```dax
VAR MinSel =
    CALCULATE( MIN('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MaxSel =
    CALCULATE( MAX('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MinAll =
    CALCULATE( MIN('Dim_Date'[Date]), ALL('Dim_Date') )
VAR MaxAll =
    CALCULATE( MAX('Dim_Date'[Date]), ALL('Dim_Date') )

-- If selected range = full calendar, then "no filter"
VAR HasDateSelection =
    NOT ( MinSel = MinAll && MaxSel = MaxAll )

VAR AnchorDate =
    IF( HasDateSelection, MinSel, TODAY() )

VAR StartDate =
    DATE( YEAR(AnchorDate), MONTH(AnchorDate), 1 )

VAR EndDate =
    EOMONTH( AnchorDate, 0 )

RETURN
CALCULATE(
    [Actual Hrs],
    DATESBETWEEN('Dim_Date'[Date], StartDate, EndDate)
)
```

### `Current Month (Billable Hrs Copy)`

```dax
[Current Month (Billable Hrs)]
```

### `Current Month (Billable Hrs)`

```dax
VAR MinSel =
    CALCULATE( MIN('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MaxSel =
    CALCULATE( MAX('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MinAll =
    CALCULATE( MIN('Dim_Date'[Date]), ALL('Dim_Date') )
VAR MaxAll =
    CALCULATE( MAX('Dim_Date'[Date]), ALL('Dim_Date') )

-- If the selected range equals the full calendar, we consider it "no date filter"
VAR HasDateSelection =
    NOT ( MinSel = MinAll && MaxSel = MaxAll )

VAR AnchorDate =
    IF( HasDateSelection, MinSel, TODAY() )

VAR StartDate =
    DATE( YEAR(AnchorDate), MONTH(AnchorDate), 1 )

VAR EndDate =
    EOMONTH( AnchorDate, 0 )

RETURN
CALCULATE(
    [Billable Hrs],
    DATESBETWEEN('Dim_Date'[Date], StartDate, EndDate)
)
```

### `Current Month (Billable vs Std Hrs)`

```dax
VAR billableHrs = [Current Month (Billable Hrs)]
VAR standardHrs = [Current Month (Std Hrs)]
RETURN
standardHrs - billableHrs
```

### `Current Month (Non Billable Hrs)`

```dax
VAR MinSel =
    CALCULATE( MIN('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MaxSel =
    CALCULATE( MAX('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MinAll =
    CALCULATE( MIN('Dim_Date'[Date]), ALL('Dim_Date') )
VAR MaxAll =
    CALCULATE( MAX('Dim_Date'[Date]), ALL('Dim_Date') )

-- If selected range = full calendar, then "no filter"
VAR HasDateSelection =
    NOT ( MinSel = MinAll && MaxSel = MaxAll )

VAR AnchorDate =
    IF( HasDateSelection, MinSel, TODAY() )

VAR StartDate =
    DATE( YEAR(AnchorDate), MONTH(AnchorDate), 1 )

VAR EndDate =
    EOMONTH( AnchorDate, 0 )

RETURN
CALCULATE(
    [Non Billable Hrs],
    DATESBETWEEN('Dim_Date'[Date], StartDate, EndDate)
)
```

### `Current Month (Productivity Rate)`

Format string: `0.00%;-0.00%;0.00%`

```dax
[Current Month (Billable Hrs)] / [Current Month (Actual Hrs - Excl. Break)]
```

### `Current Month (Std Hrs)`

```dax
VAR MinSel =
    CALCULATE( MIN('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MaxSel =
    CALCULATE( MAX('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MinAll =
    CALCULATE( MIN('Dim_Date'[Date]), ALL('Dim_Date') )
VAR MaxAll =
    CALCULATE( MAX('Dim_Date'[Date]), ALL('Dim_Date') )

-- Detect if a real selection exists
VAR HasDateSelection =
    NOT ( MinSel = MinAll && MaxSel = MaxAll )

VAR AnchorDate =
    IF( HasDateSelection, MinSel, TODAY() )

VAR StartDate =
    DATE( YEAR(AnchorDate), MONTH(AnchorDate), 1 )

VAR EndDate =
    EOMONTH( AnchorDate, 0 )

RETURN
CALCULATE(
    [Std Hrs],
    DATESBETWEEN('Dim_Date'[Date], StartDate, EndDate)
)
```

### `Current vs Previous Month (Billable Hrs %)`

Format string: `0.0%;-0.0%;0.0%`

```dax
VAR quotient =
DIVIDE(
    [Current Month (Billable Hrs)],
    [Previous Month (Billable Hrs)],
    BLANK()
)
RETURN
IF(
    NOT ISBLANK([Current vs Previous Month (Billable Hrs)]),
    quotient - 1,
    BLANK()
)
```

### `Current vs Previous Month (Billable Hrs)`

```dax
[Current Month (Billable Hrs)] - [Previous Month (Billable Hrs)]
```

### `Previous Month (Billable Hrs)`

```dax
VAR MinSel =
    CALCULATE( MIN('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MaxSel =
    CALCULATE( MAX('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MinAll =
    CALCULATE( MIN('Dim_Date'[Date]), ALL('Dim_Date') )
VAR MaxAll =
    CALCULATE( MAX('Dim_Date'[Date]), ALL('Dim_Date') )

-- Check if a real filter exists
VAR HasDateSelection =
    NOT ( MinSel = MinAll && MaxSel = MaxAll )

VAR AnchorDate =
    IF( HasDateSelection, MinSel, TODAY() )

-- Shift AnchorDate back one month
VAR StartDate =
    DATE( YEAR(AnchorDate), MONTH(AnchorDate) - 1, 1 )

VAR EndDate =
    EOMONTH( AnchorDate, -1 )

RETURN
CALCULATE(
    [Billable Hrs],
    DATESBETWEEN('Dim_Date'[Date], StartDate, EndDate)
)
```

### `TDA Title`

```dax
VAR MinSel =
    CALCULATE( MIN('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MaxSel =
    CALCULATE( MAX('Dim_Date'[Date]), ALLSELECTED('Dim_Date') )
VAR MinAll =
    CALCULATE( MIN('Dim_Date'[Date]), ALL('Dim_Date') )
VAR MaxAll =
    CALCULATE( MAX('Dim_Date'[Date]), ALL('Dim_Date') )

-- Check if a real filter exists
VAR HasDateSelection =
    NOT ( MinSel = MinAll && MaxSel = MaxAll )

VAR AnchorDate =
    IF( HasDateSelection, MinSel, TODAY() )

RETURN
"TDA (" &
    FORMAT( AnchorDate, "MMMM YYYY") &
")"
```

## [9] Others

### `Blank Column`

Format string: `0`

```dax
 BLANK()
```

### `Productivity Rate`

Format string: `0.0%;-0.0%;0.0%`

```dax
VAR netBillableHrs = [Billable Hrs]
VAR actualHrs = [Actual Hrs (excl Break)]
VAR actualHrsYTD =
    CALCULATE(
        [Actual Hrs],
        REMOVEFILTERS('Dim_Date')
    )
RETURN
    netBillableHrs / actualHrs
```

### `Release Notes Title`

```dax
"Release Notes — " &
FORMAT(SELECTEDVALUE('release_notes'[Date]), "mmmm, dd, yyyy")
```

### `Show Filters`

```dax
----DATE FILTERS----
--Month Tag Fiscal Year
IF(
    ISFILTERED('Dim_Date'[Month Tag]),
    VAR SelectedMonths = VALUES('Dim_Date'[Fiscal Year])
    VAR itemsCombined = CONCATENATEX(SelectedMonths, 'Dim_Date'[Fiscal Year], ", ")
    RETURN itemsCombined & UNICHAR(10)
)&
--Month Tag Month
IF(
    ISFILTERED('Dim_Date'[Month Tag]),
    VAR SelectedMonths = VALUES('Dim_Date'[Month Name])
    VAR itemsCombined = CONCATENATEX(SelectedMonths, 'Dim_Date'[Month Name], ", ")
    RETURN itemsCombined & UNICHAR(10)
)&

--Fiscal Year
IF(
    ISFILTERED('Dim_Date'[Fiscal Year]),
    VAR items = VALUES('Dim_Date'[Fiscal Year])
    VAR itemsCombined = CONCATENATEX(items, 'Dim_Date'[Fiscal Year], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&
--Month
IF(
    ISFILTERED('Dim_Date'[Month Name]),
    VAR items = VALUES('Dim_Date'[Month Name])
    VAR itemsCombined = CONCATENATEX(items, 'Dim_Date'[Month Name], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&

----OTHER FILTERS----
--Principal
IF(
    ISFILTERED('dim_clients'[Principal*]),
    VAR items = VALUES('dim_clients'[Principal*])
    VAR itemsCombined = CONCATENATEX(items, 'dim_clients'[Principal*], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&
--Business Stream
IF(
    ISFILTERED('dim_clients'[Business Stream*]),
    VAR items = VALUES('dim_clients'[Business Stream*])
    VAR itemsCombined = CONCATENATEX(items, 'dim_clients'[Business Stream*], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&
--Client Group
IF(
    ISFILTERED('dim_clients'[Client Group]),
    VAR items = VALUES('dim_clients'[Client Group])
    VAR itemsCombined = CONCATENATEX(items, 'dim_clients'[Client Group], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&
--Client
IF(
    ISFILTERED('dim_clients'[Xero Name*]),
    VAR items = VALUES('dim_clients'[Xero Name*])
    VAR itemsCombined = CONCATENATEX(items, 'dim_clients'[Xero Name*], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&
--Operational Delivery
IF(
    ISFILTERED('fact_activities'[teamName]),
    VAR items = VALUES('fact_activities'[teamName])
    VAR itemsCombined = CONCATENATEX(items, 'fact_activities'[teamName], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&
--Employee
IF(
    ISFILTERED('fact_activities'[userName]),
    VAR items = VALUES('fact_activities'[userName])
    VAR itemsCombined = CONCATENATEX(items, 'fact_activities'[userName], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&
--SLA
IF(
    ISFILTERED('fact_activities'[sla]),
    VAR items = VALUES('fact_activities'[sla])
    VAR itemsCombined = CONCATENATEX(items, 'fact_activities'[sla], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)&
--Deliverable
IF(
    ISFILTERED('fact_activities'[deliverableName]),
    VAR items = VALUES('fact_activities'[deliverableName])
    VAR itemsCombined = CONCATENATEX(items, 'fact_activities'[deliverableName], UNICHAR(10))
    RETURN itemsCombined & UNICHAR(10)
)
```

### `Show Filters Header`

```dax
----DATE FILTERS----
--Fiscal Year
IF(
    ISFILTERED('Dim_Date'[Fiscal Year])  || ISFILTERED('Dim_Date'[Month Tag]),
    "Fiscal Year: " & REPT(UNICHAR(10), COUNTROWS(VALUES('Dim_Date'[Fiscal Year])))
)&
--Month
IF(
    ISFILTERED('Dim_Date'[Month Name]) || ISFILTERED('Dim_Date'[Month Tag]),
    "Month: " & REPT(UNICHAR(10), COUNTROWS(VALUES('Dim_Date'[Month Name])))
)&

----OTHER FILTERS----
--Principal
IF(
    ISFILTERED('dim_clients'[Principal*]),
    "Principal: " & REPT(UNICHAR(10), COUNTROWS(VALUES('dim_clients'[Principal*])))
)&
--Business Stream
IF(
    ISFILTERED('dim_clients'[Business Stream*]),
    "Business Stream: " & REPT(UNICHAR(10), COUNTROWS(VALUES('dim_clients'[Business Stream*])))
)&
--Client Group
IF(
    ISFILTERED('dim_clients'[Client Group]),
    "Client Group: " & REPT(UNICHAR(10), COUNTROWS(VALUES('dim_clients'[Client Group])))
)&
--Client
IF(
    ISFILTERED('dim_clients'[Xero Name*]),
    "Client: " & REPT(UNICHAR(10), COUNTROWS(VALUES('dim_clients'[Xero Name*])))
)&
--Operational Delivery
IF(
    ISFILTERED('fact_activities'[teamName]),
    "Operational Delivery: " & REPT(UNICHAR(10), COUNTROWS(VALUES('fact_activities'[teamName])))
)&
--Employee
IF(
    ISFILTERED('fact_activities'[userName]),
    "Employee: " & REPT(UNICHAR(10), COUNTROWS(VALUES('fact_activities'[userName])))
)&
--SLA
IF(
    ISFILTERED('fact_activities'[sla]),
    "SLA: " & REPT(UNICHAR(10), COUNTROWS(VALUES('fact_activities'[sla])))
)&
--Deliverable
IF(
    ISFILTERED('fact_activities'[deliverableName]),
    "Deliverable: " & REPT(UNICHAR(10), COUNTROWS(VALUES('fact_activities'[deliverableName])))
)
```

### `Yesterday`

Format string: `General Date`

```dax
VAR LocalNow = NOW() + TIME(10, 0, 0)
// INT() strips the time away, leaving just the Date at midnight.
// Subtracting 1 moves it back exactly 24 hours to Yesterday's date.
VAR YesterdayDate = INT(LocalNow) - 1
RETURN
    YesterdayDate + TIME(23, 59, 0)
```

