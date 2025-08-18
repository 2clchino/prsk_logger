import gspread
from google.oauth2.service_account import Credentials
import datetime
import json
from config import TEMP_DATA_FILE, CREDENTIALS_FILE, SPREADSHEET_KEY
from typing import Dict

def col_to_letter(n: int) -> str:
    """
    1-index の列番号を A, B, ..., AA のような文字に変換
    """
    result = ''
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result
"""
def record_gspread(sheet_name=""):
    with open(TEMP_DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    keys = sorted(map(int, data.keys()))
    num_rows = len(keys)
    start_row = 3
    end_row = start_row + num_rows - 1

    scopes = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=scopes
    )
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(SPREADSHEET_KEY)
    worksheet  = spreadsheet.worksheet(sheet_name)

    key_cells = worksheet.range(f'A{start_row}:A{end_row}')
    if not any(cell.value for cell in key_cells):
        for idx, cell in enumerate(key_cells):
            cell.value = keys[idx]
        worksheet.update_cells(key_cells)

    col_idx = 1
    while worksheet.acell(f'{col_to_letter(col_idx)}{start_row}').value:
        col_idx += 1
    col_letter = col_to_letter(col_idx)

    now = datetime.datetime.now()
    timestamp = now.strftime('%Y/%m/%d %H 時')
    worksheet.update_acell(f'{col_letter}1', timestamp)

    value_cells = worksheet.range(f'{col_letter}{start_row}:{col_letter}{end_row}')
    for idx, cell in enumerate(value_cells):
        cell.value = data[str(keys[idx])]
    worksheet.update_cells(value_cells)
"""

def record_gspread(
    sheet_name: str,
    event_time: datetime.datetime
) -> None:
    with open(TEMP_DATA_FILE, 'r', encoding='utf-8') as f:
        data: Dict[str, int] = json.load(f)

    keys = [str(k) for k in sorted(map(int, data.keys()))]
    num_keys = len(keys)
    scopes = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(sheet_name)
    
    header = sheet.row_values(1)
    if len(header) < 3 + num_keys:
        new_header = ['日付', '時間', '経過時間（h）'] + keys
        sheet.delete_rows(1)
        sheet.insert_row(new_header, index=1)

    all_values = sheet.get_all_values()
    next_row_idx = len(all_values) + 1
    
    now = datetime.datetime.now()
    zero_time = now.replace(minute=0, second=0, microsecond=0)
    date_str = now.strftime('%Y/%m/%d')
    time_str = zero_time.strftime('%H:%M:%S')
    elapsed_hours = (zero_time - event_time).total_seconds() / 3600

    row = [
        date_str,
        time_str,
        f"{elapsed_hours:.3f}"
    ]
    for k in keys:
        row.append(data[k])
    sheet.insert_row(row, index=next_row_idx)

if __name__ == '__main__':
    print(CREDENTIALS_FILE)
    event_dt = datetime.datetime(2025, 5, 12, 20, 00)
    record_gspread("テスト", event_dt)