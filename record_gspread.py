import gspread
from google.oauth2.service_account import Credentials
import datetime
import json
from config import TEMP_DATA_FILE, CREDENTIALS_FILE, SPREADSHEET_KEY, WORKSHEET_NAME

def col_to_letter(n: int) -> str:
    """
    1-index の列番号を A, B, ..., AA のような文字に変換
    """
    result = ''
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result

def record_gspread():
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
    worksheet  = spreadsheet.worksheet(WORKSHEET_NAME)

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

if __name__ == '__main__':
    record_gspread()