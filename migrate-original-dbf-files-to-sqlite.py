import os
import shutil
import argparse
import pandas as pd
import sqlite3
from dbfread import DBF
import glob


# Ovaj :
#   - kopira fajlove sa originalne putanje '/c/HramSP/dbf' u '/c/crkva/crkva/fixtures' gde se nalazi ova skripta
#
# example:
# python copy-original-dbf.py --src_dir "C:\OtherSource\dbf" --dest_dir "C:\OtherDest\fixtures"


def copy_dbf_files(src_dir, dest_dir):
    """Copy all .dbf files from source directory to destination directory."""
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)  # Create the destination directory if it doesn't exist

    for file_name in os.listdir(src_dir):
        if file_name.endswith('.dbf') or file_name.endswith('.DBF'):
            src_file = os.path.join(src_dir, file_name)
            dest_file = os.path.join(dest_dir, file_name)
            shutil.copy(src_file, dest_file)
            print(f"Copied: {file_name} to {dest_dir}")

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
    
    # Path for the .sqlite database
    sqlite_db_path = 'combined_original_hsp_database.sqlite'

    # Remove the existing .sqlite database file
    remove_matching_files(sqlite_db_path)

    # Convert each .dbf file to .sqlite
    for dbf_file, table_name in dbf_files.items():
        convert_dbf_to_sqlite(dbf_file, sqlite_db_path, table_name)
        print(f"Conversion {table_name} completed successfully.")

    print("All .dbf files have been converted to .sqlite format.")

    # remove all .dbf files
    remove_matching_files("*.dbf")
    remove_matching_files("*.DBF")
    
    #remove_matching_files("crkva\registar\migrations\0*")


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


def change_working_directory(new_dir):
    try:
        os.chdir(new_dir)  # Change the current working directory
        print(f"Changed working directory to: {os.getcwd()}")  # Print the new working directory
    except FileNotFoundError:
        print(f"Error: The directory '{new_dir}' does not exist.")
    except PermissionError:
        print(f"Error: Permission denied to change to '{new_dir}'.")

def remove_matching_files(pattern):
    # Use glob to find files matching the pattern
    files = glob.glob(pattern)
    for file in files:
        try:
            os.remove(file)  # Remove the file
            print(f"Removed file: {file}")
        except OSError as e:
            print(f"Error removing file {file}: {e}")

def main():
    # Define source and destination directories
    # src_dir = r"C:\HramSP\dbf"
    # dest_dir = r"C:\crkva\crkva\fixtures"

   
    # Set up argument parsing - my home setup
    # parser = argparse.ArgumentParser(description='Copy .dbf files from source to destination.')
    # parser.add_argument('--src_dir', type=str, default='e:\\projects\\hram-svete-petke\\resources\\dbf', help='Source directory containing .dbf files')
    # parser.add_argument('--dest_dir', type=str, default='e:\\projects\\hram-svete-petke\\crkva\\crkva\\fixtures', help='Destination directory to copy .dbf files to')

    # WSL setup (crkva)
    # parser = argparse.ArgumentParser(description='Copy .dbf files from source to destination.')
    # parser.add_argument('--src_dir', type=str, default='/mnt/c/HramSP/dbf', help='Source directory containing .dbf files')
    # parser.add_argument('--dest_dir', type=str, default='/mnt/c/crkva/crkva/fixtures', help='Destination directory to copy .dbf files to')

    
    # WSL setup (home)
    # parser = argparse.ArgumentParser(description='Copy .dbf files from source to destination.')
    # parser.add_argument('--src_dir', type=str, default='/mnt/e/projects/hram-svete-petke/resources/dbf', help='Source directory containing .dbf files')
    # parser.add_argument('--dest_dir', type=str, default='crkva/fixtures', help='Destination directory to copy .dbf files to')

    # Linux setup (home)
    parser = argparse.ArgumentParser(description='Copy .dbf files from source to destination.')
    parser.add_argument('--src_dir', type=str, default='../resources/dbf', help='Source directory containing .dbf files')
    parser.add_argument('--dest_dir', type=str, default='crkva/fixtures', help='Destination directory to copy .dbf files to')


    #parser = argparse.ArgumentParser(description='Copy .dbf files from source to destination.')
    #parser.add_argument('--src_dir', type=str, default='C:\\HramSP\\dbf', help='Source directory containing .dbf files')
    #parser.add_argument('--dest_dir', type=str, default='C:\\crkva\\crkva\\fixtures', help='Destination directory to copy .dbf files to')

    # Parse the arguments
    args = parser.parse_args()


    # Copy all .dbf files from the source directory to the destination directory
    copy_dbf_files(args.src_dir, args.dest_dir)

    home_dir = os.getcwd()
    print("Current working directory:", home_dir)
    
    # change directory to dest_dir
    change_working_directory(args.dest_dir)
    
    # migrate database 
    convert_all_hsp_dbf_files_to_sqlite()

    # change directory to home directory
    change_working_directory(home_dir)

if __name__ == "__main__":
    main()

