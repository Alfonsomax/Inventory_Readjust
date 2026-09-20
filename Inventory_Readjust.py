# -*- coding: utf-8 -*-
import sys
import os
import pandas as pd
import numpy as np
import time
import pathlib
from datetime import datetime


main_path = pathlib.Path(__file__).parent.resolve()
os.chdir(main_path)

##########################################################################################
# Auxiliary Modules Main Path
##########################################################################################

aux_func_path = os.path.join(main_path, "aux_func")
if aux_func_path not in sys.path:
    sys.path.append(aux_func_path)
inputs_path = os.path.join(main_path, "inputs")

from df_creator_module import df_creator
from df_creator_module import df_creator_str


if "db_creator" not in globals():
    from db_creator_reader_module import db_creator
if "db_reader" not in globals():
    from db_creator_reader_module import db_reader

##########################################################################################

t000 = time.time()

pd.set_option('display.max_colwidth', 300)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 200)
pd.set_option('display.width', 1000)


###############################################################################
#%% Control Inputs
###############################################################################

# Current date
today = datetime.today()
today_str = today.strftime('%Y%m%d')
date_day = pd.Timestamp.today().normalize()

flags_path = os.path.join(main_path, "flags")

# Variable to activate debug mode. When debug mode is enabled, it generates intermediate process files and warning messages.
DEBUG_MODE_ON = True



###############################################################################
# Hypotheses, internal variables, and paths
###############################################################################

def load_flags(flag_file):

    flags = {
        'INVENTORY': None
    }

    if not os.path.exists(flag_file):
        return flags

    with open(flag_file, 'r') as f:
        for line in f:
            if '=' in line:
                key, val = line.strip().split('=', 1)
                flags[key] = val

    return flags


def save_flags(flag_file, flags):

    with open(flag_file, 'w') as f:
        for key, val in flags.items():
            if val:
                f.write(f"{key}={val}\n")


flag_file = os.path.join(flags_path, "last_execution_date.txt")
flags = load_flags(flag_file)

inventory_executed_today = (flags['INVENTORY'] == today_str)


try:
    base_path = r"\\server\rute"
    available_folders = [
        f for f in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, f))
    ]
    available_dates = []
    for f in available_folders:
        try:
            d = datetime.strptime(f, '%Y-%m-%d')
            available_dates.append(d)
        except:
            continue

    valid_dates = [d for d in available_dates if d <= today]
    if not valid_dates:
        raise Exception("No valid folders found")

    selected_date = max(valid_dates)
    DATE_INPUT = selected_date.strftime('%Y-%m-%d')
    FILE_DATE_INPUT = selected_date.strftime('%Y%m%d')

    input_path_inventory_raw = os.path.join(
        base_path,
        DATE_INPUT,
        f"Inventory_raw_{FILE_DATE_INPUT}.xlsx"
    )

    db_inventory_raw_path = os.path.join(main_path, "sqlite3", "INPUT_Inventory_raw_" + FILE_DATE_INPUT + ".db")

    if not inventory_executed_today:
        df_inventory_raw = df_creator_str(input_path_inventory_raw, "latin1", "Inventory_raw")
        db_creator(db_inventory_raw_path, "df_inventory_raw", df_inventory_raw)

        flags['INVENTORY'] = today_str
        save_flags(flag_file, flags)

        inventory_executed_today = True
    else:
        df_inventory_raw = db_reader(db_inventory_raw_path, "df_inventory_raw")

except Exception as e:
    print(f"Error in read_inventory/demand: {str(e)}")




###############################################################################
#%% INV_RAW Process
###############################################################################
def inventory_raw_normalize_process(df_inventory_raw):

    if DEBUG_MODE_ON:
        print("\n DEBUG ** INV_RAW_init Process")

    main_cols = ['ELEMENT', 'N_A', 'Tp', 'Material', 'Material_number', 'Lote', 'Pedido', 'Position', 'Provider', 'Indicator_1', 'STOCK_TYPE_1', 'STOCK_STATE_2', 'PROGRAMME', 'STOCKING_POLICY_1', 'STOCKING_POLICY_2', 'Average_Variable_Price', 'QTY_1', 'QTY_2', 'QTY_3', 'QTY_4', 'COST_1']
    df_inventory_raw = df_inventory_raw[main_cols]

    # Filter normalization
    df_inventory_raw['ELEMENT'] = df_inventory_raw['ELEMENT'].astype(str).str.strip()
    df_inventory_raw['Material'] = df_inventory_raw['Material'].astype(str).str.strip()
    df_inventory_raw['N_A'] = df_inventory_raw['N_A'].astype(str).str.strip()
    df_inventory_raw['STOCK_TYPE_1'] = df_inventory_raw['STOCK_TYPE_1'].astype(str).str.strip()
    df_inventory_raw['STOCK_STATE_2'] = df_inventory_raw['STOCK_STATE_2'].astype(str).str.strip()
    df_inventory_raw['STOCK_STATE_2'] = df_inventory_raw['STOCK_STATE_2'].str.replace(" ", "")
    df_inventory_raw['Indicator_1'] = df_inventory_raw['Indicator_1'].astype(str).str.strip()
    df_inventory_raw['Indicator_1'] = df_inventory_raw['Indicator_1'].apply(lambda x: 'N' if x == 'nan' else x)
    df_inventory_raw['QTY_1'] = pd.to_numeric(df_inventory_raw['QTY_1'], errors='coerce')
    df_inventory_raw['QTY_2'] = pd.to_numeric(df_inventory_raw['QTY_2'], errors='coerce')
    df_inventory_raw['QTY_3'] = pd.to_numeric(df_inventory_raw['QTY_3'], errors='coerce')
    df_inventory_raw['QTY_4'] = pd.to_numeric(df_inventory_raw['QTY_4'], errors='coerce')
    df_inventory_raw['Average_Variable_Price'] = pd.to_numeric(df_inventory_raw['Average_Variable_Price'], errors='coerce')

    # Filters
    df_inventory_raw = df_inventory_raw[df_inventory_raw['N_A'].isin(['A', 'B', 'C'])]

    if DEBUG_MODE_ON:
        print(f"number of rows df_inventory_raw: {df_inventory_raw.shape[0]}")
        print(f"number of columns df_inventory_raw: {df_inventory_raw.shape[1]}")

    return df_inventory_raw


# Sorting by subgroups according to Material, N_A and STOCK_STATE_2
def sort_process(df_inventory_raw):

    status_order = ['NEW', 'NEW+USED', 'USED']

    df_inventory_raw['STOCK_TYPE_cat'] = pd.Categorical(
        df_inventory_raw['STOCK_STATE_2'],
        categories=status_order,
        ordered=True
    )

    df_inventory_sorted = df_inventory_raw.sort_values(
        by=['Material', 'STOCK_TYPE_cat', 'N_A']
    ).drop(columns=['STOCK_TYPE_cat'])

    if DEBUG_MODE_ON:
        print(f"number of rows df_inventory_sorted: {df_inventory_sorted.shape[0]}")
        print(f"number of columns df_inventory_sorted: {df_inventory_sorted.shape[1]}")

    return df_inventory_sorted


requirements = [{'A', 'C'}, {'A', 'B'}]


def contains_required_element(group, required_set):
    return set(group['N_A']).issuperset(required_set)


def filter_process(df_inventory_sorted):

    filtered_dfs = []
    for req in requirements:
        filtered_df = df_inventory_sorted.groupby('Material').filter(lambda x: contains_required_element(x, req))
        filtered_dfs.append(filtered_df)

    df_filtered = pd.concat(filtered_dfs).drop_duplicates().reset_index(drop=True)

    df_filtered['NEW_QTY_1'] = 0.0
    df_filtered['NEW_QTY_2'] = 0.0
    df_filtered['CANCELABLE'] = ''

    if DEBUG_MODE_ON:
        print(f"number of rows df_filtered: {df_filtered.shape[0]}")
        print(f"number of columns df_filtered: {df_filtered.shape[1]}")

    return df_filtered


def remove_unusable_groups(group):

    supply = group[group['N_A'] == 'A']['QTY_1'].sum()
    demand = group[group['N_A'].isin(['B', 'C'])]['QTY_2'].sum()

    if supply == 0 or demand == 0:
        return pd.DataFrame()   # return empty = remove
    else:
        return group


def process_group(group):

    simulator = group['ELEMENT'].isin(['ELEMNT_1', 'ELEMNT_2', 'ELEMNT_3'])

    aog = group['STOCK_STATE_2'] == 'AOG'

    error_state = group['STOCK_STATE_2'] == 'ELEMENTPEPNOTRECOGNIZED'

    group.loc[simulator, 'CANCELABLE'] = 'SIM'
    group.loc[aog, 'CANCELABLE'] = 'AOG'
    group.loc[error_state, 'CANCELABLE'] = 'ERROR'

    blocked = simulator | aog | error_state
    usable = group[~blocked]

    new = group[(group['N_A'] == 'A') & (group['Indicator_1'] == 'Y') & (~blocked)]['QTY_1'].sum()
    newused = group[(group['N_A'] == 'A') & (~group['Indicator_1'] == 'Y') & (~blocked)]['QTY_1'].sum()

    pool_new = new

    priority_order = ['C', 'B']

    pool_new_left = pool_new

    for value in priority_order:
        if pool_new <= 0:
            break

        for idx, row in group[(group['N_A'] == value) & (group['STOCK_STATE_2'] == 'NEW') & (~blocked)].iterrows():
            if pool_new <= 0:
                break

            if pool_new >= row['QTY_2']:
                group.at[idx, 'NEW_QTY_1'] = float(row['QTY_1'] + row['QTY_2'])
                group.at[idx, 'NEW_QTY_2'] = 0.0
                pool_new -= row['QTY_2']
            else:
                group.at[idx, 'NEW_QTY_1'] = float(row['QTY_1'] + pool_new)
                group.at[idx, 'NEW_QTY_2'] = float(row['QTY_2'] - pool_new)
                pool_new = 0

        pool_new_left = pool_new

    pool_newused = pool_new_left + newused

    for value in priority_order:
        if pool_newused <= 0:
            break

        for idx, row in group[(group['N_A'] == value) & (group['STOCK_STATE_2'] == 'NEW+USED') & (~blocked)].iterrows():
            if pool_newused <= 0:
                break

            if pool_newused >= row['QTY_2']:
                group.at[idx, 'NEW_QTY_1'] = float(row['QTY_1'] + row['QTY_2'])
                group.at[idx, 'NEW_QTY_2'] = 0.0
                pool_newused -= row['QTY_2']
            else:
                group.at[idx, 'NEW_QTY_1'] = float(row['QTY_1'] + pool_newused)
                group.at[idx, 'NEW_QTY_2'] = float(row['QTY_2'] - pool_newused)
                pool_newused = 0

    mask_usable = (~blocked) & (group['N_A'].isin(['B', 'C']))
    S2 = (
        group.loc[mask_usable, 'NEW_QTY_1'] -
        group.loc[mask_usable, 'QTY_1']
    ).sum()

    pool2 = S2

    for idx, row in group[(group['N_A'] == 'A') & (~blocked)].iterrows():

        if pool2 <= 0:
            break

        if pool2 >= row['QTY_1']:
            group.at[idx, 'NEW_QTY_1'] = 0.0
            group.at[idx, 'NEW_QTY_2'] = float(row['QTY_2'] + row['QTY_1'])
            pool2 -= row['QTY_1']
        else:
            group.at[idx, 'NEW_QTY_1'] = float(row['QTY_1'] - pool2)
            group.at[idx, 'NEW_QTY_2'] = float(row['QTY_2'] + pool2)
            pool2 = 0

    for idx, row in group[group['N_A'].isin(['B', 'C'])].iterrows():

        if blocked.loc[idx]:
            continue

        if row['QTY_2'] > 0 and \
        row['NEW_QTY_1'] == (row['QTY_1'] + row['QTY_2']) and \
        row['NEW_QTY_2'] == 0:
            group.at[idx, 'CANCELABLE'] = 'YES'

        elif row['QTY_2'] > 0 and \
        (0 < row['NEW_QTY_2'] < row['QTY_2']):
            group.at[idx, 'CANCELABLE'] = 'PARTIAL'

    for idx, row in group[group['N_A'] == 'A'].iterrows():

        if blocked.loc[idx]:
            continue

        if row['QTY_1'] > 0 and \
        row['NEW_QTY_2'] > 0 and \
        (row['NEW_QTY_2'] > row['QTY_2']) and \
        (row['NEW_QTY_1'] < row['QTY_1']):
            group.at[idx, 'CANCELABLE'] = 'ADJUST'

    return group


def result_process(df_filtered):

    df_filtered['NEW_COST_1'] = df_filtered['NEW_QTY_1'] * df_filtered['Average_Variable_Price']
    #df_filtered = df_filtered[df_filtered['NEW_COST_1'] > 2000]
    

    mask = df_filtered['CANCELABLE'].isin(['SIM', 'AOG', 'ERROR', 'ELEMENTPEPNOTRECOGNIZED', '', ' '])
    df_filtered.loc[mask, 'NEW_QTY_1'] = '-'
    df_filtered.loc[mask, 'NEW_QTY_2'] = '-'
    df_filtered.loc[mask, 'NEW_COST_1'] = '-'

    df_filtered['Indicator_1'] = df_filtered['Indicator_1'].replace(['', 'nan', 'N'], '')

    main_cols = ['ELEMENT', 'N_A', 'Tp', 'Material', 'Material_number', 'Lote', 'Pedido', 'Position', 'Provider', 'Indicator_1', 'STOCK_TYPE_1', 'STOCK_STATE_2', 'PROGRAMME', 'STOCKING_POLICY_1', 'STOCKING_POLICY_2', 'Average_Variable_Price', 'QTY_1', 'QTY_2', 'NEW_QTY_1', 'NEW_QTY_2', 'CANCELABLE', 'QTY_3', 'QTY_4', 'COST_1', 'NEW_COST_1']
    df_results = df_filtered[main_cols]

    if DEBUG_MODE_ON:
        print(f"number of rows df_results: {df_results.shape[0]}")
        print(f"number of columns df_results: {df_results.shape[1]}")

    return df_results



###############################################################################
#%% Main Body
###############################################################################

df_inventory_raw = inventory_raw_normalize_process(df_inventory_raw)
df_inventory_sorted = sort_process(df_inventory_raw)
df_filtered = filter_process(df_inventory_sorted)

if DEBUG_MODE_ON:
    print("\n DEBUG ** Unusable groups Process")
df_filtered = df_filtered.groupby('Material').apply(remove_unusable_groups).reset_index(drop=True)
if DEBUG_MODE_ON:
    print(f"number of rows df_filtered: {df_filtered.shape[0]}")
    print(f"number of columns df_filtered: {df_filtered.shape[1]}")

if DEBUG_MODE_ON:
    print("\n DEBUG ** Groups Process")
df_filtered = df_filtered.groupby('Material').apply(process_group).reset_index(drop=True)
df_results = result_process(df_filtered)


# Create the Excel file with the final dataframe data
output_file = os.path.join(main_path, 'output', 'PRUEBA_Reajuste_Inventario_' + FILE_DATE_INPUT + '.xlsx')

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df_results.to_excel(writer, sheet_name='Inventory', index=False)

print('Excel Spreadsheet for Calculating Inventory Adjustments '+DATE_INPUT+' generated')



##############################################################################################################################################################################
##############################################################################################################################################################################


t001 = time.time()
  
print("Readjust Inventory processed in " + str(int((t001 - t000))) + " s")

