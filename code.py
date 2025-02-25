
import logging
import json
import os
import random
from telegram import Update, Poll
from telegram.ext import (
    Updater, CommandHandler, CallbackContext, MessageHandler, 
    PollAnswerHandler, JobQueue, Filters
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

CHAT_IDS_FILE = 'chat_ids.json'
TOKEN = "5554891157:AAFG4gZzQ26-ynwQVEnyv1NlZ9Dx0Sx42Hg"

# Load chat data
def load_chat_data():
    if os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, 'r') as file:
            try:
                data = json.load(file)
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                return {}
    return {}

# Save chat data
def save_chat_data(chat_data):
    with open(CHAT_IDS_FILE, 'w') as file:
        json.dump(chat_data, file)

quizzes = [
    {"question": "What is the capital of France?", "options": ["Berlin", "Madrid", "Paris", "Rome"], "answer": "Paris"},
    {"question": "Which element has the chemical symbol 'O'?", "options": ["Gold", "Oxygen", "Silver", "Iron"], "answer": "Oxygen"},
    {"question": "How many continents are there on Earth?", "options": ["5", "6", "7", "8"], "answer": "7"},
    {"question": "What is the square root of 81?", "options": ["7", "8", "9", "10"], "answer": "9"},
]

random.shuffle(quizzes)

def send_quiz(context: CallbackContext):
    job = context.job
    chat_id = job.context["chat_id"]
    used_questions = job.context["used_questions"]

    available_quizzes = [q for q in quizzes if q not in used_questions]
    if not available_quizzes:
        job.schedule_removal()
        return
    
    quiz = random.choice(available_quizzes)
    used_questions.append(quiz)

    try:
        context.bot.send_poll(
            chat_id=chat_id,
            question=quiz["question"],
            options=quiz["options"],
            type=Poll.QUIZ,
            correct_option_id=quiz["options"].index(quiz["answer"]),
            is_anonymous=False
        )
    except Exception as e:
        logger.error(f"Failed to send quiz to {chat_id}: {e}")

# Start Quiz with Duplicate Prevention
def start_quiz(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    chat_data = load_chat_data()

    # Prevent duplicate quizzes
    if chat_id in chat_data and chat_data[chat_id].get("active", False):
        update.message.reply_text("A quiz is already running in this chat!")
        return

    interval = chat_data.get(chat_id, {}).get("interval", 30)
    chat_data[chat_id] = {"active": True, "interval": interval}
    save_chat_data(chat_data)

    update.message.reply_text(f"Quiz started! Interval: {interval} seconds.")
    context.job_queue.run_repeating(send_quiz, interval=interval, first=0, context={"chat_id": chat_id, "used_questions": []})

def sendgroup(update: Update, context: CallbackContext):
    if update.effective_chat.type in ["group", "supergroup"]:
        start_quiz(update, context)
    else:
        update.message.reply_text("This command can only be used in a group chat.")

def prequiz(update: Update, context: CallbackContext):
    if update.effective_chat.type == "private":
        start_quiz(update, context)
    else:
        update.message.reply_text("This command can only be used in a private chat.")

# Stop Quiz
def stop_quiz(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)
    chat_data = load_chat_data()

    if chat_id in chat_data:
        del chat_data[chat_id]
        save_chat_data(chat_data)

        # Stop running job
        jobs = context.job_queue.jobs()
        for job in jobs:
            if job.context and job.context["chat_id"] == chat_id:
                job.schedule_removal()

        update.message.reply_text("Quiz stopped successfully.")
    else:
        update.message.reply_text("No active quiz to stop.")

# Set Quiz Interval
def set_interval(update: Update, context: CallbackContext):
    chat_id = str(update.effective_chat.id)

    if not context.args or not context.args[0].isdigit():
        update.message.reply_text("Usage: /setinterval <seconds>")
        return
    
    interval = int(context.args[0])
    if interval < 10:
        update.message.reply_text("Interval must be at least 10 seconds.")
        return

    chat_data = load_chat_data()
    if chat_id not in chat_data:
        update.message.reply_text("No active quiz. Interval saved for future quizzes.")
        chat_data[chat_id] = {"active": False, "interval": interval}
        save_chat_data(chat_data)
        return

    chat_data[chat_id]["interval"] = interval
    save_chat_data(chat_data)

    jobs = context.job_queue.jobs()
    for job in jobs:
        if job.context and job.context["chat_id"] == chat_id:
            job.schedule_removal()

    update.message.reply_text(f"Quiz interval updated to {interval} seconds. Restarting quiz...")
    context.job_queue.run_repeating(send_quiz, interval=interval, first=0, context={"chat_id": chat_id, "used_questions": []})



LEADERBOARD_FILE = 'leaderboard.json'

def load_leaderboard():
    """Loads leaderboard data from file."""
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def save_leaderboard(data):
    """Saves leaderboard data to file."""
    with open(LEADERBOARD_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def handle_poll_answer(update: Update, context: CallbackContext):
    """Updates leaderboard when a user answers correctly."""
    poll_answer = update.poll_answer
    user_id = str(poll_answer.user.id)
    selected_option = poll_answer.option_ids[0] if poll_answer.option_ids else None
    leaderboard = load_leaderboard()

    for quiz in quizzes:
        correct_option = quiz["options"].index(quiz["answer"])
        if selected_option == correct_option:
            leaderboard[user_id] = leaderboard.get(user_id, 0) + 1
            save_leaderboard(leaderboard)
            return

def show_leaderboard(update: Update, context: CallbackContext):
    """Displays the top 10 users in the leaderboard with proper usernames."""
    leaderboard = load_leaderboard()

    if not leaderboard:
        update.message.reply_text("🏆 No scores yet! Start playing to appear on the leaderboard.")
        return

    sorted_scores = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    message = "🏆 *Quiz Leaderboard* 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for rank, (user_id, score) in enumerate(sorted_scores[:10], start=1):
        try:
            user = context.bot.get_chat(int(user_id))
            username = f"@{user.username}" if user.username else f"{user.first_name} {user.last_name or ''}"
        except Exception:
            username = f"User {user_id}"

        rank_display = medals[rank - 1] if rank <= 3 else f"#{rank}"
        message += f"{rank_display} *{username}* - {score} points\n"

    update.message.reply_text(message, parse_mode="Markdown")


# Broadcast with Admin Check
ADMIN_ID = 5050578106  # Replace with your actual Telegram user ID

def broadcast(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("You are not authorized to use this command.")
        return

    message = ' '.join(context.args)
    if not message:
        update.message.reply_text("Usage: /broadcast <message>")
        return

    chat_data = load_chat_data()
    for chat_id in chat_data.keys():
        try:
            context.bot.send_message(chat_id=int(chat_id), text=message)
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")

    update.message.reply_text("Broadcast sent.")

# Start Bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Welcome! Use /sendgroup to start a quiz in a group or /prequiz to start a quiz personally.")))
    dp.add_handler(CommandHandler("sendgroup", sendgroup))
    dp.add_handler(CommandHandler("prequiz", prequiz))
    dp.add_handler(CommandHandler("stopquiz", stop_quiz))
    dp.add_handler(CommandHandler("setinterval", set_interval))
    dp.add_handler(PollAnswerHandler(handle_poll_answer))
    dp.add_handler(CommandHandler("leaderboard", show_leaderboard))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

