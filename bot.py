import logging
import os

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from handlers.admin import admin_export, admin_recent, admin_stats
from handlers.conversation import (
    AGE,
    ARRIVAL,
    BUDGET,
    CONFIRM,
    CONTACT,
    COUNTRY,
    EDUCATION,
    FIELD,
    LANGUAGE,
    NAME,
    PREFERENCES,
    cancel,
    choose_language,
    confirm,
    handle_age,
    handle_arrival,
    handle_budget,
    handle_contact,
    handle_country,
    handle_education,
    handle_field,
    handle_name,
    handle_preferences,
    start,
)

load_dotenv()
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    level=logging.INFO,
)

log = logging.getLogger(__name__)


def _admin_ids() -> list[int]:
    raw = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


async def _notify_admins(app: Application, text: str) -> None:
    for admin_id in _admin_ids():
        try:
            await app.bot.send_message(chat_id=admin_id, text=text)
        except Exception as e:
            log.warning("Could not notify admin %d: %s", admin_id, e)


async def on_startup(app: Application) -> None:
    log.info("Bot started.")
    await _notify_admins(app, "🟢 Bot is online and ready.")


async def on_shutdown(app: Application) -> None:
    log.info("Bot shutting down.")
    await _notify_admins(app, "🔴 Bot is shutting down (reboot or restart).")


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in .env")

    app = (
        Application.builder()
        .token(token)
        .post_init(on_startup)
        .post_stop(on_shutdown)
        .build()
    )

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        per_message=False,
        states={
            LANGUAGE:  [CallbackQueryHandler(choose_language)],
            NAME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            AGE:       [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age)],
            COUNTRY:   [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_country)],
            EDUCATION: [CallbackQueryHandler(handle_education)],
            FIELD:     [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_field)],
            ARRIVAL:   [CallbackQueryHandler(handle_arrival)],
            BUDGET:      [CallbackQueryHandler(handle_budget)],
            PREFERENCES: [CallbackQueryHandler(handle_preferences)],
            CONTACT:     [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_contact)],
            CONFIRM:   [CallbackQueryHandler(confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("admin_stats",  admin_stats))
    app.add_handler(CommandHandler("admin_recent", admin_recent))
    app.add_handler(CommandHandler("admin_export", admin_export))

    log.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
