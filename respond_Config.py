# main.py
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == "private":
        # Individual user: use first + last name
        first_name = user.first_name or ""
        last_name = user.last_name or ""
        display_name = f"{first_name} {last_name}".strip() or "there"
        greeting = f"👋 Hello {display_name}!"
    else:
        # Group/supergroup: use group title
        group_name = chat.title or "this group"
        greeting = f"👋 Hello members of <b>{group_name}</b>!"
    
    await update.message.reply_text(
        f"{greeting}\n\n"
        f"Your Chat ID: <code>{chat.id}</code>\n"
        f"Type: <code>{chat.type}</code>",
        parse_mode="HTML"
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("✅ Bot started. Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()