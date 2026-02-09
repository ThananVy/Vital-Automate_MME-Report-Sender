# main.py
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    
    # Combine names: "First Last" if both exist, else just "First"
    display_name = f"{first_name} {last_name}".strip() or "there"
    
    await update.message.reply_text(
        f"👋 Hello {display_name}!\n\n"
        f"Your User ID: <code>{user.id}</code>",
        parse_mode="HTML"
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    print("✅ Bot started. Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()