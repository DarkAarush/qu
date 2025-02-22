from telegram import Update
from telegram.ext import CallbackContext, Updater, CommandHandler
from datetime import timedelta
import json
import random

def load_chat_data():
    try:
        with open("chat_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_chat_data(chat_data):
    with open("chat_data.json", "w") as file:
        json.dump(chat_data, file)

def gcquiz(update: Update, context: CallbackContext) -> None:
    """Start sending quizzes to group chats."""
    chat_id = update.message.chat_id
    chat_data = load_chat_data()
    if chat_id in chat_data:
        context.job_queue.run_repeating(send_quiz_to_group, interval=timedelta(seconds=chat_data[chat_id]["interval"]), first=0, context=chat_id, name=str(chat_id))
        update.message.reply_text('Started sending quizzes to group chat.')
    else:
        update.message.reply_text('Chat ID not found. Please start the bot using /start.')

def send_quiz_to_group(context: CallbackContext) -> None:
    chat_id = context.job.context
    quiz = get_random_quiz()
    question = quiz['question']
    options = quiz['options']
    context.bot.send_poll(chat_id=chat_id, question=question, options=options, type='quiz', correct_option_id=quiz['correct_option_id'])

def get_random_quiz():
    quizzes = [
        {
            "question": "What is the capital of France?",
            "options": ["Berlin", "Madrid", "Paris", "Rome"],
            "correct_option_id": 2
        },
        {
            "question": "Which planet is known as the Red Planet?",
            "options": ["Earth", "Mars", "Jupiter", "Saturn"],
            "correct_option_id": 1
        },
        {
            "question": "What is the largest ocean on Earth?",
            "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
            "correct_option_id": 3
        }
        # Add more quizzes as needed
    ]
    return random.choice(quizzes)

def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    chat_data = load_chat_data()
    chat_data[chat_id] = {"interval": 10}  # Set default interval to 1 hour
    save_chat_data(chat_data)
    update.message.reply_text('Bot started! Use /gcquiz to start receiving quizzes.')

def main():
    updater = Updater("5503691929:AAHruRPFP3998zJCM4PGHOnmltkFYyeu8zk", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("gcquiz", gcquiz))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
