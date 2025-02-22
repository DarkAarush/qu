import json
import random
import logging
from datetime import timedelta
from telegram import Update, Chat
from telegram.ext import (
    Application, CommandHandler, ContextTypes, PicklePersistence
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

QUIZ_DATA = [
    {
        "question": "What is the capital of France?",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_option_id": 2,
    },
    {
        "question": "Which planet is known as the Red Planet?",
        "options": ["Earth", "Mars", "Jupiter", "Saturn"],
        "correct_option_id": 1,
    },
    {
        "question": "What is the largest ocean on Earth?",
        "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
        "correct_option_id": 3,
    },
]

# Load & Save Chat Data
def load_chat_data():
    try:
        with open("chat_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_chat_data(chat_data):
    with open("chat_data.json", "w") as file:
        json.dump(chat_data, file)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register the group chat so that /gcquiz works"""
    chat = update.effective_chat  # This works for both groups and private chats
    chat_id = chat.id

    # Ensure it's a group
    if chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        await update.message.reply_text("This command must be used in a group.")
        return

    chat_data = load_chat_data()
    
    if chat_id not in chat_data:
        chat_data[chat_id] = {"interval": 3600}  # Default interval: 1 hour
        save_chat_data(chat_data)
    
    await update.message.reply_text("Bot registered for this group! Use /gcquiz to start receiving quizzes.")

async def gcquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start sending quizzes to group chats."""
    chat = update.effective_chat
    chat_id = chat.id

    chat_data = load_chat_data()

    if chat_id in chat_data:
        interval = chat_data[chat_id]["interval"]

        # Check if job already exists
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        if current_jobs:
            await update.message.reply_text("Quiz is already running in this group!")
            return

        context.job_queue.run_repeating(
            send_quiz_to_group,
            interval=timedelta(seconds=interval),
            first=0,
            chat_id=chat_id,
            name=str(chat_id),
        )
        await update.message.reply_text("Started sending quizzes to this group.")
    else:
        await update.message.reply_text("Chat ID not found. Use /start first in this group.")

async def send_quiz_to_group(context: ContextTypes.DEFAULT_TYPE):
    """Send a random quiz to a group."""
    job = context.job
    chat_id = job.chat_id
    quiz = random.choice(QUIZ_DATA)

    await context.bot.send_poll(
        chat_id=chat_id,
        question=quiz["question"],
        options=quiz["options"],
        type="quiz",
        correct_option_id=quiz["correct_option_id"],
    )

def main():
    persistence = PicklePersistence(filepath="bot_persistence")
    app = Application.builder().token("7733999154:AAGofQ1u3J28cZ1u1q5TjKQ8_vvL1LcPxPc").persistence(persistence).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gcquiz", gcquiz))

    app.run_polling()

if __name__ == "__main__":
    main()
