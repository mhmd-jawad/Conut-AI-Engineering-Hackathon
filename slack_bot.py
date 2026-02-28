"""
Slack Bot — Conut Chief of Operations Agent
Forwards user messages to POST /chat and returns the formatted answer.

Works identically to the Telegram bot — same backend, same responses.

Usage:
    1. pip install slack-bolt
    2. Start the FastAPI server:  python main.py
    3. Run:  python slack_bot.py

Slack App Setup:
    1. Go to https://api.slack.com/apps and create a new app
    2. Under "OAuth & Permissions", add these Bot Token Scopes:
       - chat:write
       - app_mentions:read
       - im:history
       - im:read
       - im:write
       - channels:history  (if you want the bot in public channels)
    3. Under "Event Subscriptions", enable events and subscribe to:
       - message.im         (direct messages)
       - app_mention         (@ mentions in channels)
    4. Install the app to your workspace
    5. Copy the Bot User OAuth Token (xoxb-...) into BOT_TOKEN below
    6. Copy the Signing Secret into SIGNING_SECRET below (or set env vars)
"""

import json
import logging
import os
import re
import urllib.request

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── Configuration ───────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")  # xapp-... for Socket Mode
SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Slack App ───────────────────────────────────────────────────────────

app = App(token=BOT_TOKEN, signing_secret=SIGNING_SECRET or "not-used-in-socket-mode")

# ── API helpers (same as Telegram bot) ──────────────────────────────────


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


# ── Formatting helpers ──────────────────────────────────────────────────

def _telegram_to_slack(text: str) -> str:
    """
    Convert Telegram Markdown to Slack mrkdwn.
    Telegram uses *bold* and _italic_, Slack uses *bold* and _italic_ too,
    but we need to clean up any MarkdownV2 escapes.
    """
    if not text:
        return text
    # Remove MarkdownV2 backslash escapes  (\. \! \- etc.)
    text = re.sub(r"\\([_*\[\]()~`>#+\-=|{}.!])", r"\1", text)
    return text


# ── Welcome message ─────────────────────────────────────────────────────

WELCOME = (
    ":doughnut: *Conut Chief of Operations Agent*\n\n"
    "I'm your AI Operations Assistant for Conut bakery & café chain.\n"
    "Just type a question in plain English and I'll analyze the data for you!\n\n"
    "*What I can do:*\n"
    "1. :shopping_trolley: *Combo Optimization* — best product bundles\n"
    "2. :chart_with_upwards_trend: *Demand Forecasting* — predict future sales\n"
    "3. :busts_in_silhouette: *Staffing Estimation* — staff needs per shift\n"
    "4. :globe_with_meridians: *Expansion Feasibility* — should we open a new branch?\n"
    "5. :coffee: *Coffee & Milkshake Growth* — beverage strategies\n\n"
    "*Commands:*\n"
    "`help` — Show this welcome message\n"
    "`branches` — List available branches & shifts\n"
    "`health` — Check if the backend is running\n\n"
    "Just type your question below! :point_down:"
)


# ── Command handlers ────────────────────────────────────────────────────

def _handle_help(say):
    """Send the welcome / help message."""
    say(WELCOME)


def _handle_branches(say):
    """List available branches and shifts."""
    data = api_get("/branches")
    if "error" in data and "branches" not in data:
        say(":warning: Backend not reachable. Make sure the server is running.")
        return

    branches = data.get("branches", [])
    shifts = data.get("shifts", [])
    text = (
        ":convenience_store: *Available Branches:*\n"
        + "\n".join(f"  • {b}" for b in branches)
        + "\n\n:clock3: *Shifts:*\n"
        + "\n".join(f"  • {s}" for s in shifts)
    )
    say(text)


def _handle_health(say):
    """Check backend health."""
    data = api_get("/health")
    if data.get("status") == "ok":
        say(":white_check_mark: Backend is *running* and healthy!")
    else:
        say(f":warning: Backend issue: {data.get('error', 'unknown')}")


def _handle_question(question: str, say):
    """Forward a question to POST /chat and return the formatted answer."""
    result = api_post("/chat", {"question": question})

    error = result.get("error")
    answer = result.get("answer")

    if error and not answer:
        say(f":warning: Something went wrong:\n{error}\n\nPlease try rephrasing your question.")
        return

    # Convert any Telegram-style formatting to Slack mrkdwn
    answer_text = _telegram_to_slack(answer or "No response received.")

    # Add metadata footer (same as Telegram bot)
    intent = result.get("intent", "?")
    branch = result.get("branch") or "all"
    confidence = result.get("confidence", 0)
    elapsed = result.get("elapsed_ms", 0)

    footer = (
        f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
        f":mag: {intent}  |  :convenience_store: {branch}\n"
        f":dart: {confidence:.0%}  |  :stopwatch: {elapsed:.0f}ms"
    )

    full_reply = answer_text + footer

    # Slack has a 40,000 char limit per message (very generous)
    # but we chunk at 3,900 to stay safe with Block Kit overhead
    MAX_LEN = 3900
    if len(full_reply) <= MAX_LEN:
        say(full_reply)
    else:
        chunks = [full_reply[i : i + MAX_LEN] for i in range(0, len(full_reply), MAX_LEN)]
        for chunk in chunks:
            say(chunk)


# ── Slack event listeners ───────────────────────────────────────────────

@app.event("message")
def handle_dm(event, say):
    """Handle direct messages to the bot."""
    # Ignore bot's own messages, message_changed events, etc.
    if event.get("subtype"):
        return

    text = (event.get("text") or "").strip()
    if not text:
        return

    logger.info("DM from %s: %s", event.get("user"), text)

    # Simple command routing (no slash needed in DMs)
    lower = text.lower()
    if lower in ("help", "start", "/help", "/start"):
        _handle_help(say)
    elif lower in ("branches", "/branches"):
        _handle_branches(say)
    elif lower in ("health", "/health"):
        _handle_health(say)
    else:
        _handle_question(text, say)


@app.event("app_mention")
def handle_mention(event, say):
    """Handle @bot mentions in channels."""
    raw = (event.get("text") or "").strip()
    # Strip the bot mention (<@U12345>) from the beginning
    text = re.sub(r"<@[A-Z0-9]+>\s*", "", raw).strip()

    if not text:
        _handle_help(say)
        return

    logger.info("Mention from %s: %s", event.get("user"), text)

    lower = text.lower()
    if lower in ("help", "start"):
        _handle_help(say)
    elif lower in ("branches",):
        _handle_branches(say)
    elif lower in ("health",):
        _handle_health(say)
    else:
        _handle_question(text, say)


# ── Main ────────────────────────────────────────────────────────────────


def main():
    """Start the Slack bot."""
    logger.info("Starting Conut Operations Slack Bot...")

    if APP_TOKEN:
        # Socket Mode — no public URL needed (ideal for development)
        logger.info("Using Socket Mode (SLACK_APP_TOKEN is set)")
        handler = SocketModeHandler(app, APP_TOKEN)
        handler.start()
    else:
        # HTTP mode — Slack sends events to a public URL
        # You'll need to expose port 3000 (e.g., via ngrok)
        logger.info("Using HTTP mode on port 3000 (set SLACK_APP_TOKEN for Socket Mode)")
        app.start(port=3000)


if __name__ == "__main__":
    main()
