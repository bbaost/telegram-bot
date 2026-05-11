import logging
import os
import yaml
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from services.sheets import save_response

log = logging.getLogger(__name__)

# Load all messages from config
_config_path = Path(__file__).parent.parent / "config" / "messages.yaml"
with open(_config_path, encoding="utf-8") as f:
    _CFG = yaml.safe_load(f)

# Conversation states
LANGUAGE, NAME, AGE, COUNTRY, EDUCATION, FIELD, ARRIVAL, BUDGET, PREFERENCES, CONTACT, CONFIRM = range(11)


def _msg(key: str, lang: str) -> str:
    return _CFG["messages"][key][lang]


def _options(section: str, lang: str) -> list[list[InlineKeyboardButton]]:
    return [
        [InlineKeyboardButton(translations[lang], callback_data=key)]
        for key, translations in _CFG[section].items()
    ]


def _language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="en")],
        [InlineKeyboardButton("🇰🇷 한국어", callback_data="ko")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="ru")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["telegram_id"] = update.effective_user.id
    await update.message.reply_text(
        "Welcome / 환영합니다 / Добро пожаловать\n\n"
        "Please choose your language / 언어를 선택해 주세요 / Выберите язык:",
        reply_markup=_language_keyboard(),
    )
    return LANGUAGE


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data
    context.user_data["lang"] = lang
    await query.edit_message_text(_msg("welcome", lang))
    await query.message.reply_text(_msg("ask_name", lang))
    return NAME


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data["lang"]
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text(_msg("invalid_name", lang))
        return NAME
    context.user_data["name"] = name
    await update.message.reply_text(_msg("ask_age", lang))
    return AGE


async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data["lang"]
    try:
        age = int(update.message.text.strip())
        if not 10 <= age <= 80:
            raise ValueError
    except ValueError:
        await update.message.reply_text(_msg("invalid_age", lang))
        return AGE
    context.user_data["age"] = age
    await update.message.reply_text(_msg("ask_country", lang))
    return COUNTRY


async def handle_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data["lang"]
    country = update.message.text.strip()
    if len(country) < 2:
        await update.message.reply_text(_msg("invalid_country", lang))
        return COUNTRY
    context.user_data["country"] = country
    await update.message.reply_text(
        _msg("ask_education", lang),
        reply_markup=InlineKeyboardMarkup(_options("education_options", lang)),
    )
    return EDUCATION


async def handle_education(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data["lang"]
    key = query.data
    context.user_data["education"] = _CFG["education_options"][key][lang]

    await query.edit_message_text(
        f"{_msg('ask_education', lang)}\n✅ {context.user_data['education']}"
    )
    await query.message.reply_text(_msg("ask_field", lang))
    return FIELD


async def handle_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data["lang"]
    context.user_data["field"] = update.message.text.strip()
    await update.message.reply_text(
        _msg("ask_arrival", lang),
        reply_markup=InlineKeyboardMarkup(_options("arrival_options", lang)),
    )
    return ARRIVAL


async def handle_arrival(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data["lang"]
    key = query.data
    context.user_data["arrival"] = _CFG["arrival_options"][key][lang]

    await query.edit_message_text(
        f"{_msg('ask_arrival', lang)}\n✅ {context.user_data['arrival']}"
    )
    await query.message.reply_text(
        _msg("ask_budget", lang),
        reply_markup=InlineKeyboardMarkup(_options("budget_options", lang)),
    )
    return BUDGET

async def handle_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data["lang"]
    key = query.data
    context.user_data["budget"] = _CFG["budget_options"][key][lang]

    await query.edit_message_text(
        f"{_msg('ask_budget', lang)}\n✅ {context.user_data['budget']}"
    )
    await query.message.reply_text(
        _msg("ask_preferences", lang),
        reply_markup=InlineKeyboardMarkup(_options("preferences_options", lang)),
    )
    return PREFERENCES

async def handle_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data["lang"]
    key = query.data
    context.user_data["preferences"] = _CFG["preferences_options"][key][lang]
    await query.edit_message_text(
        f"{_msg('ask_preferences', lang)}\n✅ {context.user_data['preferences']}"
    )
    await query.message.reply_text(_CFG["messages"]["ask_contact"][key][lang])
    return CONTACT


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data["lang"]
    contact = update.message.text.strip()
    if len(contact) < 2:
        await update.message.reply_text(_msg("invalid_contact", lang))
        return CONTACT
    context.user_data["contact"] = contact

    data = context.user_data
    labels = _CFG["summary_labels"]
    summary = _msg("summary_header", lang) + "\n\n"
    summary += f"👤 {labels['name'][lang]}: {data['name']}\n"
    summary += f"🎂 {labels['age'][lang]}: {data['age']}\n"
    summary += f"🌍 {labels['country'][lang]}: {data['country']}\n"
    summary += f"🎓 {labels['education'][lang]}: {data['education']}\n"
    summary += f"📚 {labels['field'][lang]}: {data['field']}\n"
    summary += f"✈️ {labels['arrival'][lang]}: {data['arrival']}\n"
    summary += f"💰 {labels['budget'][lang]}: {data['budget']}\n"
    summary += f"📱 {labels['contact_type'][lang]}: {data['preferences']}\n"
    summary += f"💬 {labels['contact'][lang]}: {data['contact']}\n"

    btns = _CFG["confirm_buttons"]
    keyboard = [[
        InlineKeyboardButton(btns["confirm"][lang], callback_data="confirm_yes"),
        InlineKeyboardButton(btns["cancel"][lang], callback_data="confirm_no"),
    ]]
    await update.message.reply_text(summary, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data["lang"]

    if query.data == "confirm_no":
        await query.edit_message_text(_msg("cancelled", lang))
        return ConversationHandler.END

    log.info("[confirm] reached — user_data keys: %s", list(context.user_data.keys()))
    action = "created"
    try:
        action = await save_response(context.user_data)
        log.info("[sheets] response %s successfully", action)
    except Exception as e:
        log.exception("[sheets] ERROR saving response: %s", e)

    # Notify admins
    data = context.user_data
    icon = "🔄" if action == "updated" else "🆕"
    label = "Profile updated" if action == "updated" else "New student submission"
    notification = (
        f"{icon} {label}!\n\n"
        f"👤 {data.get('name')} — {data.get('country')}\n"
        f"🎓 {data.get('education')} · {data.get('field')}\n"
        f"✈️ {data.get('arrival')} · 💰 {data.get('budget')}\n"
        f"📱 {data.get('preferences')}: {data.get('contact')}"
    )
    for admin_id in _admin_ids():
        try:
            await context.bot.send_message(chat_id=admin_id, text=notification)
        except Exception:
            pass

    await query.edit_message_text(_msg("thank_you", lang))
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "en")
    await update.message.reply_text(_msg("cancelled", lang))
    return ConversationHandler.END


def _admin_ids() -> list[int]:
    raw = os.getenv("ADMIN_IDS", "")
    return [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
