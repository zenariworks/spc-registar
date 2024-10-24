import pandas as pd
import sqlite3
from dbfread import DBF


# Originalni fajlovi (tabele) iz starog programa za hram sv.Petke 'hsp' su u .dbf formatu
# i nalaze se u folderu:
#   e:\projects\hram-svete-petke\resources\dbf
# Oni mogu da se konvertuju u '.csv' i '.sqlite' format koji se nalaze:
#   e:\projects\hram-svete-petke\resources\dbf2csv
#   e:\projects\hram-svete-petke\resources\dbf2sqlite
#
# Ovaj program kombinuje sve .dbf fajlove od interesa u jedinstvenu bazu 'combined_original_hsp_database.sqlite'
# koja sadrzi originalne tabele stare baze

def convert_all_hsp_dbf_files_to_sqlite():
    dbf_files = {
        'HSPDOMACINI.DBF': 'HSPDOMACINI',
        'HSPKRST.DBF': 'HSPKRST',
        'HSPSLAVE.DBF': 'HSPSLAVE',
        'HSPSVEST.DBF': 'HSPSVEST',
        'HSPUKUCANI.DBF': 'HSPUKUCANI',
        'HSPULICE.DBF': 'HSPULICE',
        'HSPVENC.DBF': 'HSPVENC'
    }
    
    sqlite_db_path = 'combined_original_hsp_database.sqlite'  # Path for the .sqlite database

    for dbf_file, table_name in dbf_files.items():
        convert_dbf_to_sqlite(dbf_file, sqlite_db_path, table_name)
        print(f"Conversion {table_name} completed successfully.")


# Konvertuje .dbf fajl u .sqlite 
def convert_dbf_to_sqlite(dbf_file, sqlite_db_file, table_name):
    # Read the DBF file
    dbf_data = DBF(dbf_file)
    
    # Convert DBF data to a pandas DataFrame
    df = pd.DataFrame(iter(dbf_data))

    # Connect to the SQLite database (it will create it if it doesn't exist)
    conn = sqlite3.connect(sqlite_db_file)

    # Write the DataFrame to the SQLite database
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    # Close the connection
    conn.close()

convert_all_hsp_dbf_files_to_sqlite()



# def create_combine_sqlite_db():
#     # Create or connect to the target database
#     target_db = 'combined_original_hsp_database.sqlite'
#     conn_target = sqlite3.connect(target_db)
#     cursor_target = conn_target.cursor()

#     # List of source databases
#     source_dbs = [
#         'HSPDOMACINI.sqlite',
#         'hsperror.sqlite',
#         'hspkartice.sqlite',
#         'HSPKRST.sqlite',
#         'hspmeni.sqlite',
#         'HSPPASS.sqlite',
#         'hspset.sqlite',
#         'hspslave.sqlite',
#         'HSPSVEST.sqlite',
#         'HSPUKUCANI.sqlite',
#         'HSPULICE.sqlite',
#         'HSPVENC.sqlite'
#     ]

#     for source_db in source_dbs:
#         # Connect to the source database
#         conn_source = sqlite3.connect(source_db)
#         cursor_source = conn_source.cursor()

#         # Get the list of tables in the source database
#         cursor_source.execute("SELECT name FROM sqlite_master WHERE type='table';")
#         tables = cursor_source.fetchall()

#         for table_name in tables:
#             table_name = table_name[0]
            
#             # Create the table in the target database
#             cursor_source.execute(f"SELECT * FROM {table_name};")
#             rows = cursor_source.fetchall()

#             # Get the column names
#             column_names = [description[0] for description in cursor_source.description]

#             # Create table in the target database
#             cursor_target.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_names)});")
            
#             # Insert rows into the target table
#             cursor_target.executemany(f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(['?'] * len(column_names))});", rows)

#         # Close the source database connection
#         conn_source.close()

#     # Commit changes and close the target database connection
#     conn_target.commit()
#     conn_target.close()
