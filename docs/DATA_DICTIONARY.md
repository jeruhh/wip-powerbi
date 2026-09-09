# Data Dictionary

Generated from the TMDL definition. `calc` marks a DAX calculated column.

## `fact_activities`

Activity log — one row per timesheet entry. Grain: user x client x deliverable x date x time block. 

| Column | Type | Kind | Format | Folder |
|---|---|---|---|---|
| `createdAt` | dateTime | source | `General Date` | Columns |
| `updatedAt` | dateTime | source | `General Date` | Columns |
| `userName` | string | source | `` | Columns |
| `clientName` | string | source | `` | Columns |
| `deliverableName` | string | source | `` | Columns |
| `date` | dateTime | source | `Short Date` | Columns |
| `startTime` | dateTime | source | `Long Time` | Columns |
| `endTime` | dateTime | source | `Long Time` | Columns |
| `isOT` | boolean | source | `"""TRUE"";""TRUE"";""FALSE"""` | Columns |
| `leaveHours` | double | source | `` | Columns |
| `userId` | string | source | `` | Columns |
| `sla` | string | source | `` | Columns |
| `hours` | double | source | `` | Columns |
| `cleanLogName` | string | source | `` | Columns |
| `Xero Name` | string | source | `` | Columns |
| `Category for Productivity Page` | inferred | **calc** | `` | Calculated Columns |
| `history` | string | source | `` | Columns |
| `teamName` | string | source | `` | Columns |
| `holidayType` | string | source | `` | Columns |
| `ColumnsMatch` | inferred | **calc** | `"""TRUE"";""TRUE"";""FALSE"""` | Calculated Columns |
| `stlName` | string | source | `` | Columns |
| `remarks` | string | source | `` | Columns |
| `tcRef` | string | source | `` | Columns |
| `logName` | inferred | **calc** | `` | Calculated Columns |

## `fact_client_data`

Weekly client snapshot — one row per client + business stream per Friday. Grain: `tcref_bs_id` x Date. 

| Column | Type | Kind | Format | Folder |
|---|---|---|---|---|
| `Name of Clients (TC Reference)` | string | source | `` | Columns |
| `Xero Name` | string | source | `` | Columns |
| `Business Stream` | string | source | `` | Columns |
| `Date` | dateTime | source | `Long Date` | Columns |
| `tcref_bs_id` | string | source | `` | Columns |
| `Rates` | double | source | `` | Columns |
| `Forecasted Revenue` | double | source | `\$#,0.00;(\$#,0.00);\$#,0.00` | Columns |
| `Standard Hours` | double | source | `` | Columns |
| `Xero Revenue` | double | source | `\$#,0.00;(\$#,0.00);\$#,0.00` | Columns |

## `dim_clients`

Client master. Grain: `tcref_bs_id` (client + business stream). Includes four internal non-billable codes. 

| Column | Type | Kind | Format | Folder |
|---|---|---|---|---|
| `Source.Name` | string | source | `` | Columns |
| `Client Group` | string | source | `` | Columns |
| `Status` | string | source | `` | Columns |
| `Type` | string | source | `` | Columns |
| `FTE Count/Rate` | double | source | `` | Columns |
| `Remarks` | string | source | `` | Columns |
| `tcref_bs_id` | string | source | `` | Columns |
| `TC Reference*` | string | source | `` | Columns |
| `Xero Name*` | string | source | `` | Columns |
| `Business Stream*` | string | source | `` | Columns |
| `Principal*` | string | source | `` | Columns |
| `Assigned Team Lead*` | string | source | `` | Columns |
| `Responsible*` | string | source | `` | Columns |
| `Date Added` | string | source | `` | Columns |
| `Added By` | string | source | `` | Columns |

## `dim_date`

Calculated date dimension. `CALENDARAUTO()` filtered from 2025-01-01, with a July–June fiscal year. 

| Column | Type | Kind | Format | Folder |
|---|---|---|---|---|
| `Date` | inferred | source | `Short Date` | Columns |
| `Year` | inferred | source | `0` | Columns |
| `Month Number` | inferred | source | `0` | Columns |
| `Month Name` | inferred | source | `` | Columns |
| `Quarter` | inferred | source | `` | Columns |
| `Month-Year Sort` | inferred | source | `` | Columns |
| `Day Name` | inferred | source | `` | Columns |
| `Day Number` | inferred | source | `0` | Columns |
| `Fiscal Year` | inferred | source | `` | Columns |
| `Fiscal Year Month Sort` | inferred | source | `0` | Columns |
| `Month Tag` | inferred | source | `` | Columns |
| `Month-Year` | inferred | source | `` | Columns |
| `Date Filter` | inferred | **calc** | `"""TRUE"";""TRUE"";""FALSE"""` | Calculated Columns |
| `Week` | inferred | source | `` | Columns |
| `Is Last 3 Months` | inferred | **calc** | `0` | Calculated Columns |

## `release_notes`

Changelog feed rendered on the What's New page. 

| Column | Type | Kind | Format | Folder |
|---|---|---|---|---|
| `Date` | dateTime | source | `Long Date` | Columns |
| `Version` | string | source | `` | Columns |
| `Type` | string | source | `` | Columns |
| `Description` | string | source | `` | Columns |
| `TypeSort` | int64 | source | `0` | Columns |
| `Date Display` | string | source | `` | Columns |
| `Page` | string | source | `` | Columns |

## `yesterday`

Single-value helper table holding yesterday 23:59 local time (UTC+8). 

| Column | Type | Kind | Format | Folder |
|---|---|---|---|---|
| `yesterday` | dateTime | source | `General Date` |  |

