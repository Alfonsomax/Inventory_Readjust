# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 16:57:13 2019

@author: C09755
"""

import pandas as pd
#import time
import re
import ntpath
import os.path

#Auxilizary function designed to return the closest ascii character to the str character found
def unicode_utf8(string):
    #If the input string is not str, it is casted as str object
    if type(string) is not str:
        string = str(string, encoding='utf-8')
    
    #str characters are transformed into the closest utf8 character
    string = re.sub(u"[àáâãäå]", 'a', string)
    string = re.sub(u"[èéêë]", 'e', string)
    string = re.sub(u"[ìíîï]", 'i', string)
    string = re.sub(u"[òóôõö]", 'o', string)
    string = re.sub(u"[ùúûü]", 'u', string)
    string = re.sub(u"[ýÿ]", 'y', string)
    string = re.sub(u"[ñ]", 'n', string)
    string = re.sub(u"[ç]", 'c', string)
    string = re.sub(u"[ÀÁÂÃÄÅ]", 'A', string)
    string = re.sub(u"[ÈÉÊË]", 'E', string)
    string = re.sub(u"[ÌÍÎÏ]", 'I', string)
    string = re.sub(u"[ÒÓÔÕÖ]", 'O', string)
    string = re.sub(u"[ÙÚÛÜ]", 'U', string)
    string = re.sub(u"[Ý]", 'Y', string)
    string = re.sub(u"[Ñ]", 'N', string)
    string = re.sub(u"[Ç]", 'C', string)
    string = re.sub(u"[º]", '', string)

    #The final string is encoded in utf8 in order to avoid problems
    return string

def df_creator(file_path, encoding_type, sheet_in = 0, sep_in = ";", header_in=0):
    print("Reading " + ntpath.basename(file_path))
    file_type = os.path.splitext(file_path)[1].lower()
    if file_type == ".xls" or file_type == ".xlsx" or file_type == ".xlsm" or file_type == ".xlsb":
        if file_type == ".xls":
            df_aux = pd.read_excel(file_path, sheet_name=sheet_in, header=header_in)
        elif file_type == ".xlsx" or file_type == ".xlsm":
            df_aux = pd.read_excel(file_path, sheet_name=sheet_in, header=header_in, engine='openpyxl')
        elif file_type == ".xlsb":
            df_aux = pd.read_excel(file_path, sheet_name=sheet_in, header=header_in, engine='pyxlsb')
    elif file_type == ".csv":
        #df_aux = pd.read_csv(file_path, sep=sep_in, skiprows = header_in, error_bad_lines=False)
        print(encoding_type)
        df_aux = pd.read_csv(file_path, sep=sep_in, skiprows = header_in, on_bad_lines='skip', encoding = encoding_type)
    cols = df_aux.columns
    cols = cols.map(lambda x: unicode_utf8(x) if isinstance(x, str) else x)
    cols = cols.map(lambda x: x.replace('.', '') if isinstance(x, str) else x)
    cols = cols.map(lambda x: x.replace(' ', '_') if isinstance(x, str) else x)
    df_aux.columns = cols
    return df_aux


def df_creator_str(file_path, encoding_type, sheet_in = 0, sep_in = ";", header_in=0):
    print("Reading " + ntpath.basename(file_path))
    file_type = os.path.splitext(file_path)[1].lower()
    if file_type == ".xls" or file_type == ".xlsx" or file_type == ".xlsm" or file_type == ".xlsb":
        if file_type == ".xls":
            df_aux = pd.read_excel(file_path, sheet_name=sheet_in, header=header_in, dtype=str).fillna('')
        elif file_type == ".xlsx" or file_type == ".xlsm":
            df_aux = pd.read_excel(file_path, sheet_name=sheet_in, header=header_in, engine='openpyxl', dtype=str).fillna('')
        elif file_type == ".xlsb":
            df_aux = pd.read_excel(file_path, sheet_name=sheet_in, header=header_in, engine='pyxlsb', dtype=str).fillna('')
    elif file_type == ".csv":
        #df_aux = pd.read_csv(file_path, sep=sep_in, skiprows = header_in, error_bad_lines=False)
        print(encoding_type)
        df_aux = pd.read_csv(file_path, sep=sep_in, skiprows = header_in, on_bad_lines='skip', encoding = encoding_type, dtype=str).fillna('')
    cols = df_aux.columns
    cols = cols.map(lambda x: unicode_utf8(x) if isinstance(x, str) else x)
    cols = cols.map(lambda x: x.replace('.', '') if isinstance(x, str) else x)
    cols = cols.map(lambda x: x.replace(' ', '_') if isinstance(x, str) else x)
    df_aux.columns = cols
    return df_aux