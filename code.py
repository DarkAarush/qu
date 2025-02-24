import logging
import json
import os
from telegram import Update, Poll
from telegram.ext import (Updater, CommandHandler, CallbackContext, MessageHandler, Filters, JobQueue)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

CHAT_IDS_FILE = 'chat_ids.json'
QUIZ_INTERVAL = 30  # Interval in seconds between quizzes

def load_chat_data():
    if os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, 'r') as file:
            try:
                data = json.load(file)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                return {}
    return {}

def save_chat_data(chat_data):
    with open(CHAT_IDS_FILE, 'w') as file:
        json.dump(chat_data, file)

quizzes = [
    {"question": "What is the capital of France?", "options": ["Berlin", "Madrid", "Paris", "Rome"], "answer": "Paris"},
    {"question": "What is 5 + 7?", "options": ["10", "11", "12", "13"], "answer": "12"}
]

def send_quiz(context: CallbackContext):
    job = context.job
    chat_id = job.context
    chat_data = load_chat_data()
    if str(chat_id) not in chat_data:
        return  # Stop sending quizzes if the chat is removed
    
    quiz = quizzes[0]  # Can be randomized or rotated
    try:
        context.bot.send_poll(
            chat_id=chat_id,
            question=quiz["question"],
            options=quiz["options"],
            type=Poll.QUIZ,
            correct_option_id=quiz["options"].index(quiz["answer"])
        )
    except Exception as e:
        logger.error(f"Failed to send quiz to {chat_id}: {e}")

def start_quiz(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    chat_data = load_chat_data()
    chat_data[str(chat_id)] = {"active": True}
    save_chat_data(chat_data)
    update.message.reply_text("Quiz started!")
    
    context.job_queue.run_repeating(send_quiz, interval=QUIZ_INTERVAL, first=0, context=chat_id)

def stop_quiz(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    chat_data = load_chat_data()
    if str(chat_id) in chat_data:
        del chat_data[str(chat_id)]
        save_chat_data(chat_data)
        update.message.reply_text("Quiz stopped.")
    else:
        update.message.reply_text("No active quiz found.")

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

def gcquiz(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    send_quiz(context)

def broadcast(update: Update, context: CallbackContext):
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

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /sendgroup to start a quiz in a group or /prequiz to start a quiz personally.")

def main():
    TOKEN = "5554891157:AAFG4gZzQ26-ynwQVEnyv1NlZ9Dx0Sx42Hg"
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("sendgroup", sendgroup))
    dp.add_handler(CommandHandler("prequiz", prequiz))
    dp.add_handler(CommandHandler("stopquiz", stop_quiz))
    dp.add_handler(CommandHandler("gcquiz", gcquiz))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
