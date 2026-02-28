"""
Telegram Bot — Conut Chief of Operations Agent
Forwards user messages to POST /chat and returns the formatted answer.

Usage:
    1. pip install python-telegram-bot
    2. Start the FastAPI server:  uvicorn main:app --host 127.0.0.1 --port 8000
    3. Run:  python telegram_bot.py
"""

import json
import logging
import urllib.request
from textwrap import dedent

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ── Configuration ───────────────────────────────────────────────────────

BOT_TOKEN = "8700050723:AAGOuMqG6RjeEimBiuGIPDJpFwVra2SC8m0"
API_BASE = "http://127.0.0.1:8000"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── API helpers ─────────────────────────────────────────────────────────


def api_post(path: str, body: dict) -> dict:
    """POST JSON to the FastAPI backend and return parsed response."""
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as exc:
        return {"error": str(exc), "answer": None}


def api_get(path: str) -> dict:
    """GET from the FastAPI backend."""
    try:
        resp = urllib.request.urlopen(f"{API_BASE}{path}", timeout=10)
        return json.loads(resp.read())
    except Exception as exc:
        return {"error": str(exc)}


# ── Bot handlers ────────────────────────────────────────────────────────


WELCOME = dedent("""\
    🍩 *Conut Chief of Operations Agent*

    I'm your AI Operations Assistant for Conut bakery & café chain\\.
    Just type a question in plain English and I'll analyze the data for you\\!

    *What I can do:*
    1\\. 🛒 *Combo Optimization* — best product bundles
    2\\. 📈 *Demand Forecasting* — predict future sales
    3\\. 👥 *Staffing Estimation* — staff needs per shift
    4\\. 🏗 *Expansion Feasibility* — should we open a new branch?
    5\\. ☕ *Coffee & Milkshake Growth* — beverage strategies

    *Example questions:*
    • _What are the top combos for Conut Jnah?_
    • _Forecast demand for Conut \\- Tyre next 4 months_
    • _How many staff for the evening shift?_
    • _Should we expand? Where?_
    • _Coffee growth strategy for Main Street Coffee_

    *Commands:*
    /start — Show this welcome message
    /branches — List available branches & shifts
    /health — Check if the backend is running

    Just type your question below\\! 👇
""")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(WELCOME, parse_mode="MarkdownV2")


async def cmd_branches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /branches command."""
    data = api_get("/branches")
    if "error" in data and "branches" not in data:
        await update.message.reply_text(
            "⚠ Backend not reachable. Make sure the server is running."
        )
        return

    branches = data.get("branches", [])
    shifts = data.get("shifts", [])
    text = (
        "🏪 *Available Branches:*\n"
        + "\n".join(f"  • {b}" for b in branches)
        + "\n\n⏰ *Shifts:*\n"
        + "\n".join(f"  • {s}" for s in shifts)
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /health command."""
    data = api_get("/health")
    if data.get("status") == "ok":
        await update.message.reply_text(
            "✅ Backend is *running* and healthy\\!",
            parse_mode="MarkdownV2",
        )
    else:
        await update.message.reply_text(
            f"⚠ Backend issue: {data.get('error', 'unknown')}"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward any text message to POST /chat and return the answer."""
    question = update.message.text.strip()
    if not question:
        return

    # Show "typing..." while processing
    await update.message.chat.send_action("typing")

    logger.info("Question from %s: %s", update.effective_user.first_name, question)

    result = api_post("/chat", {"question": question})

    error = result.get("error")
    answer = result.get("answer")

    if error and not answer:
        await update.message.reply_text(
            f"⚠ Something went wrong:\n{error}\n\nPlease try rephrasing your question."
        )
        return

    # Add metadata footer
    intent = result.get("intent", "?")
    branch = result.get("branch") or "all"
    confidence = result.get("confidence", 0)
    elapsed = result.get("elapsed_ms", 0)

    footer = f"\n\n━━━━━━━━━━━━━━━━━━━━\n🔎 {intent}  |  🏪 {branch}\n🎯 {confidence:.0%}  |  ⏱ {elapsed:.0f}ms"

    full_reply = (answer or "No response received.") + footer

    # Telegram has a 4096 char limit — split if needed
    if len(full_reply) <= 4096:
        try:
            await update.message.reply_text(full_reply, parse_mode="Markdown")
        except Exception:
            # Fallback: send without Markdown if formatting fails
            await update.message.reply_text(full_reply)
    else:
        # Split into chunks
        chunks = [full_reply[i:i + 4096] for i in range(0, len(full_reply), 4096)]
        for chunk in chunks:
            try:
                await update.message.reply_text(chunk, parse_mode="Markdown")
            except Exception:
                await update.message.reply_text(chunk)


# ── Main ────────────────────────────────────────────────────────────────


def main():
    """Start the Telegram bot."""
    logger.info("Starting Conut Operations Telegram Bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("branches", cmd_branches))
    app.add_handler(CommandHandler("health", cmd_health))

    # All other text messages → send to /chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is polling... (Press Ctrl+C to stop)")
    app.run_polling()


if __name__ == "__main__":
    main()
