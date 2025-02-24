import logging
import json
import os
import random
from telegram import Update, Poll
from telegram.ext import (Updater, CommandHandler, CallbackContext, MessageHandler, Filters, JobQueue)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

CHAT_IDS_FILE = 'chat_ids.json'
QUIZ_INTERVAL = 30  # Interval in seconds between quizzes

TOKEN = "5554891157:AAFG4gZzQ26-ynwQVEnyv1NlZ9Dx0Sx42Hg"

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
    {"question": "Which element has the chemical symbol 'O'?", "options": ["Gold", "Oxygen", "Silver", "Iron"], "answer": "Oxygen"},
    {"question": "How many continents are there on Earth?", "options": ["5", "6", "7", "8"], "answer": "7"},
    {"question": "What is the square root of 81?", "options": ["7", "8", "9", "10"], "answer": "9"},
    {"question": "Who wrote 'Hamlet'?", "options": ["Charles Dickens", "William Shakespeare", "Leo Tolstoy", "Mark Twain"], "answer": "William Shakespeare"},
    {"question": "Which planet is known as the Red Planet?", "options": ["Earth", "Mars", "Jupiter", "Venus"], "answer": "Mars"},
    {"question": "What is the boiling point of water at sea level?", "options": ["90°C", "100°C", "110°C", "120°C"], "answer": "100°C"},
    {"question": "What is the largest mammal in the world?", "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"], "answer": "Blue Whale"},
    {"question": "Which is the tallest mountain in the world?", "options": ["K2", "Kilimanjaro", "Mount Everest", "Denali"], "answer": "Mount Everest"},
    {"question": "Who painted the ceiling of the Sistine Chapel?", "options": ["Michelangelo", "Leonardo da Vinci", "Raphael", "Donatello"], "answer": "Michelangelo"}
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
    
    context.job_queue.run_repeating(send_quiz, interval=QUIZ_INTERVAL, first=0, context={"chat_id": chat_id, "used_questions": []})

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
