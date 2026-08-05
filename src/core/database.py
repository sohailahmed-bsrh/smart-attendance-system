import os
import pandas as pd
from openpyxl import Workbook
from src.utils.helpers import BASE_DIR, get_current_date, get_current_time, get_timestamp

ATTENDANCE_FILE = os.path.join(BASE_DIR, "outputs", "attendance.csv")

def ensure_csv():
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=["Name", "Date", "Time"])
        df.to_csv(ATTENDANCE_FILE, index=False)

def mark_attendance(name):
    """Marks attendance. Returns 'marked', 'already_marked', or 'error'."""
    ensure_csv()
    try:
        df = pd.read_csv(ATTENDANCE_FILE)
    except Exception as e:
        print(f"[DB] Error reading CSV: {e}")
        return "error"

    today = get_current_date()
    now_time = get_current_time()

    # Check for duplicate today
    already_marked = not df[(df["Name"] == name) & (df["Date"] == today)].empty
    if already_marked:
        return "already_marked"

    # Append
    df.loc[len(df)] = [name, today, now_time]
    try:
        df.to_csv(ATTENDANCE_FILE, index=False)
        return "marked"
    except Exception as e:
        print(f"[DB] Error writing CSV: {e}")
        return "error"

def get_attendance_data():
    """Returns the dataframe of all attendance records."""
    ensure_csv()
    try:
        return pd.read_csv(ATTENDANCE_FILE)
    except:
        return pd.DataFrame(columns=["Name", "Date", "Time"])

def export_to_excel():
    """Exports CSV to a timestamped Excel file."""
    df = get_attendance_data()
    if df.empty:
        return False, "No data to export."
        
    exports_dir = os.path.join(BASE_DIR, "outputs", "exports")
    os.makedirs(exports_dir, exist_ok=True)
    
    filename = f"Attendance_Export_{get_timestamp()}.xlsx"
    filepath = os.path.join(exports_dir, filename)
    
    try:
        df.to_excel(filepath, index=False, engine='openpyxl')
        return True, filepath
    except Exception as e:
        return False, str(e)

def delete_attendance(names, dates):
    """Deletes specific attendance records."""
    ensure_csv()
    try:
        df = pd.read_csv(ATTENDANCE_FILE)
        initial_len = len(df)
        
        # Zip names and dates to delete matching pairs
        for name, date in zip(names, dates):
            df = df[~((df['Name'] == name) & (df['Date'] == date))]
            
        df.to_csv(ATTENDANCE_FILE, index=False)
        return True, f"Deleted {initial_len - len(df)} records."
    except Exception as e:
        return False, str(e)
