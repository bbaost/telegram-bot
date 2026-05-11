import asyncio
import logging
import os
from datetime import datetime
from functools import partial

import gspread

log = logging.getLogger(__name__)

HEADERS = [
    "Timestamp", "Telegram ID", "Language", "Name", "Age", "Country",
    "Education", "Field of Study", "Planned Arrival", "Monthly Budget", "Contact Type", "Contact"
]


def _client():
    return gspread.service_account(filename=os.getenv("CREDENTIALS_FILE", "credentials.json"))


def _get_sheet():
    gc = _client()
    sheet = gc.open_by_key(os.getenv("SHEET_ID")).sheet1
    rows = [r for r in sheet.get_all_values() if any(cell.strip() for cell in r)]
    if not rows:
        sheet.clear()
        sheet.append_row(HEADERS)
    return sheet


def _build_row(headers: list[str], data: dict) -> list[str]:
    row_map = {
        "Timestamp":          datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Telegram ID":        str(data.get("telegram_id", "")),
        "Language":           data.get("lang", ""),
        "Name":               data.get("name", ""),
        "Age":                str(data.get("age", "")),
        "Country":            data.get("country", ""),
        "Education":          data.get("education", ""),
        "Field of Study":     data.get("field", ""),
        "Planned Arrival":    data.get("arrival", ""),
        "Monthly Budget":     data.get("budget", ""),
        "Contact Type":       data.get("preferences", ""),
        "Contact":            data.get("contact", ""),
    }
    return [row_map.get(h, "") for h in headers]


def _save_or_update_sync(data: dict) -> str:
    """Append a new row or update an existing one. Returns 'created' or 'updated'."""
    sheet = _get_sheet()
    values = [r for r in sheet.get_all_values() if any(cell.strip() for cell in r)]
    headers = values[0] if values else HEADERS
    row = _build_row(headers, data)

    telegram_id = str(data.get("telegram_id", ""))
    existing_row_num = None

    if telegram_id and "Telegram ID" in headers:
        col_idx = headers.index("Telegram ID")
        for i, r in enumerate(values[1:], start=2):
            if len(r) > col_idx and r[col_idx] == telegram_id:
                existing_row_num = i
                break

    if existing_row_num:
        col_end = chr(ord("A") + len(headers) - 1)
        log.info("[sheets] updating row %d for telegram_id %s", existing_row_num, telegram_id)
        sheet.update(f"A{existing_row_num}:{col_end}{existing_row_num}", [row])
        return "updated"

    log.info("[sheets] appending new row for telegram_id %s", telegram_id)
    sheet.append_row(row)
    return "created"


def _stats_sync() -> int:
    sheet = _get_sheet()
    return max(0, len(sheet.get_all_values()) - 1)


def _recent_sync(n: int) -> list[dict]:
    sheet = _get_sheet()
    values = sheet.get_all_values()
    if len(values) <= 1:
        return []
    headers = values[0]
    return [dict(zip(headers, row)) for row in values[1:][-n:]]


async def save_response(data: dict) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_save_or_update_sync, data))


async def get_stats() -> int:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _stats_sync)


async def get_recent_rows(n: int) -> list[dict]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_recent_sync, n))
