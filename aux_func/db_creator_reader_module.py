if "pd" not in globals():
    import pandas as pd
if "np" not in globals():
    import numpy as np
if "dt" not in globals():
    import datetime as dt
if "curve_fit" not in globals():
    from scipy.optimize import curve_fit
if "relativedelta" not in globals():
    from dateutil.relativedelta import relativedelta
if "sq" not in globals():
    import sqlite3 as sq
if "st" not in globals():
    import scipy.stats as st
if "re" not in globals():
    import re
if "sys" not in globals():
    import sys
if "os" not in globals():
    import os
if "ntpath" not in globals():
    import ntpath

###############################################################################

def db_explorer(db_path,export_list=False):
        
    # Se crea la conexión 'conn'. Si la base de datos no existe se crea
    conn = sq.connect(db_path)    
    
    # Se muestran todas las tablas que existen en la base de datos
    res = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    
    out_list = []
    
    for name in res:
        print(name[0])
        out_list.append(name[0])
        
    conn.commit()
    conn.close()
    
    if export_list == True:
        return out_list

###############################################################################

def db_creator(db_path, df_name, df_in):        
    
    for col in df_in.columns:
        if str(df_in[col].dtypes).startswith("datetime"):
            df_in[col] = df_in[col].astype(str).replace("NaT", None)
    try:
        # Se crea la conexión 'conn'. Si la base de datos no existe se crea
        conn = sq.connect(db_path)
        
        # El cursor sirve para ejecutar sentencias SQL
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS " + df_name)
        
        # Se guarda el DataFrame en la base de datos
        df_in.to_sql(df_name, conn, if_exists='replace')
#        print('SQLITE3: ' + df_name + ' stored in ' + db_path)            
        conn.commit()
        conn.close()
#    except AssertionError as error:
    except (sq.Error, sq.Warning, sq.OperationalError) as error:
        print("!!!!!!!!")
        print("SQLITE3 ERROR: "+df_name)
        print(error)
        print(df_name.info())

###############################################################################
    
def db_reader(db_path, df_name):  

    print("### db_reader ###")
    print("db_path: "+db_path)
    print("df_name: "+df_name)      
    print("#################")
        
    import numpy as np

    # Se crea la conexión 'conn'. Si la base de datos no existe se crea
    conn = sq.connect(db_path)    
    
    # Se importa la tabla de la base de datos en un dataframe
    df_out = pd.read_sql('select * from ' + df_name, conn)
    df_out.fillna(value=np.nan, inplace=True)
    df_out.set_index(df_out.columns[0], inplace=True)
        
    conn.commit()
    conn.close()
    
    return df_out
    
###############################################################################