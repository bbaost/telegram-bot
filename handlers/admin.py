import os

from telegram import Update
from telegram.ext import ContextTypes

from services.sheets import get_recent_rows, get_stats


def _is_admin(user_id: int) -> bool:
    raw = os.getenv("ADMIN_IDS", "")
    return str(user_id) in [x.strip() for x in raw.split(",")]


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return
    count = await get_stats()
    await update.message.reply_text(f"Total submissions: {count}")


async def admin_recent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return
    rows = await get_recent_rows(5)
    if not rows:
        await update.message.reply_text("No submissions yet.")
        return
    lines = ["Last submissions:\n"]
    for r in rows:
        lines.append(f"• {r.get('Name', '?')} ({r.get('Country', '?')}) — {r.get('Email', '?')}")
    await update.message.reply_text("\n".join(lines))


async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return
    sheet_id = os.getenv("SHEET_ID", "")
    await update.message.reply_text(
        f"Google Sheet:\nhttps://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    )
