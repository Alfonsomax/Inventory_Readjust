# Inventory Adjustment Script

## Overview

This script automates the review and correction of inventory quantities for a given reporting date. Its purpose is to identify stock groups that have available supply and a corresponding demand, redistribute quantities according to a defined priority logic, and generate an Excel file with the adjusted results.

The process is designed for operational inventory analysis, especially when a raw inventory export must be normalized, filtered, and rebalanced before further review or downstream reporting.

## What the script does

The workflow is composed of the following stages:

1. Reads the most recent available inventory raw file from a shared folder.
2. Stores the raw dataset in SQLite to avoid re-reading and reprocessing the same source unnecessarily.
3. Normalizes the raw inventory columns and data types.
4. Keeps only relevant inventory categories and valid records.
5. Groups stock by material and status.
6. Removes unusable groups when the material has no valid supply or no demand.
7. Applies a supply-demand allocation algorithm.
8. Flags rows as blocked, fully adjusted, partially adjusted, or requiring review.
9. Produces an Excel output with the final adjusted result set.

## Main objective

The script focuses on balancing inventory according to the following logic:

- It selects data from a historical inventory source located in the network path:
  \\gfa60005\Spotfire\GSS Business Data\03_INVENTORY REPORT
- It identifies raw inventory records by material and stock state.
- It determines which items are eligible to be reassigned.
- It allocates available stock from the relevant supply category to demand rows using priority rules.
- It calculates new quantities and associated costs after the redistribution.
- It marks records that should be considered non-adjustable or physically blocked.

## Input source

The script looks for the most recent valid folder under the inventory base path, using the corresponding date folder and searches for a file with the pattern:

- Inventory_raw_YYYYMMDD.xlsx

Once a valid date is found, the script reads the raw Excel file and converts it into a pandas DataFrame.

## Internal cache and execution control

The script stores the raw DataFrame in SQLite under the `sqlite3` folder. It also keeps a flag file in `flags/last_execution_date.txt` to avoid reprocessing the same inventory date again on the same day.

This avoids redundant execution when the script is run repeatedly.

## Data normalization

Before the allocation logic runs, the script applies several cleanup steps:

- Keeps only the columns needed for the inventory adjustment.
- Removes leading/trailing spaces from text fields.
- Converts relevant numeric columns to numeric data types.
- Eliminates invalid or irrelevant `N_A` categories.
- Normalizes stock state values and strips blank spaces.
- Replaces invalid indicator values such as `nan` with `N` for stability.

This step is critical because the logic depends on consistent categories and numeric values.

## Filtering logic

The script only keeps material groups that contain the necessary inventory categories to support a real adjustment. It evaluates combinations such as:

- supply + demand grouping
- valid stock-state presence
- grouped materials with relevant `N_A` categories

Material groups that do not have both supply and demand are considered unusable and are removed from further processing.

## Sorting and grouping

The script sorts the normalized inventory by:

- Material
- Stock state ordering
- `N_A`

This ordering is important because the reallocation logic relies on consistent row sequencing within each group.

## Allocation algorithm

The main business logic is implemented in `process_group()`.

The script identifies blocked rows by looking for values such as:

- simulator-related codes
- `AOG` records
- `ELEMENTPEPNOTRECOGNIZED` cases

These are marked as blocked and excluded from the redistribution logic.

Then it calculates available inventory from rows tagged as source stock and redistributes it across demand rows following a priority order. In the script, the priority logic is defined by the order:

- `PRT`
- `PRD`

or, in the variable naming used inside the script, the equivalent category sequence.

The allocation goes through several passes:

1. Allocation to new stock rows
2. Allocation to new+used stock rows
3. Rebalancing of remaining inventory
4. Validation of completed or partial adjustments
5. Marking of rows with status such as `YES`, `PARTIAL`, or `ADJUST`

## Output fields and status flags

The final result DataFrame includes the original inventory fields plus several derived columns, including:

- `NEW_QTY_WITHOUT_DEMAND`
- `NEW_QTY_WITH_DEMAND_Direct`
- `NEW_COST_WITHOUT_DEMAND`
- `CANCELABLE`

The `CANCELABLE` column can take values such as:

- `YES`
- `PARTIAL`
- `ADJUST`
- `SIM`
- `AOG`
- `ERROR`

Rows matching blocked or non-adjustable states are then formatted to avoid misleading output values in the Excel file.

## Excel output

At the end of execution, the script creates an Excel file in the `output` folder with a name in the format:

- PRUEBA_Reajuste_Inventario_YYYYMMDD.xlsx

The file is written as a spreadsheet named:

- Inventory

This file contains the final adjusted inventory table with all original fields and calculated adjustment columns.

## Script structure

The script is organized into the following sections:

- Path setup and imports
- Control inputs and date logic
- Loading/saving execution flags
- Inventory source detection
- SQLite caching
- Raw inventory normalization
- Sorting
- Group filtering
- Unusable-group removal
- Group processing and adjustment algorithm
- Final results generation
- Excel output export

## Required dependencies

This project relies on the following Python packages:

- pandas
- numpy
- openpyxl
- sqlite3 (standard library)

It also depends on custom internal modules located in the `aux_func` folder, including:

- `df_creator_module`
- `db_creator_reader_module`

These helpers are used to read Excel files and manage SQLite storage.

## Execution

Run the script directly with Python:

```bash
python Inventory_Readjust.py
```

The script will:

- locate the latest relevant inventory file,
- cache the raw data if not already processed,
- normalize and process it,
- generate the final Excel workbook.

## Technical notes

- `DEBUG_MODE_ON` is enabled by default and prints intermediate processing information to the console.
- The script assumes access to a shared network location for the source inventory files.
- Output generation depends on the existence of the `output` folder and the required local folders (`sqlite3`, `flags`, and `aux_func`).
- The process is intentionally designed around internal business rules for specific inventory categories and status values.

## Summary

This script is an inventory reallocation and adjustment utility. It takes a raw inventory export, cleans and standardizes it, applies a business-rule-based redistribution process across materials and stock states, and delivers a final adjusted result in Excel format for review and operational decision-making.

It is especially useful when the goal is to identify the amount of available stock that can be reallocated to demand positions while preserving valid inventory logic and highlighting exceptions or blocked items.
