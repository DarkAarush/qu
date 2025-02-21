import logging
from telegram import Update, Poll, Bot
from telegram.ext import Updater, CommandHandler, PollHandler, CallbackContext, MessageHandler, Filters
import json
import os
from datetime import timedelta

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# File to store chat IDs and intervals
CHAT_IDS_FILE = 'chat_ids.json'
PERSONAL_CHAT_IDS_FILE = 'personal_chat_ids.json'

# List of predefined quizzes with correct answers
quizzes = [
    {
        "question": "Fill in the blank with suitable preposition: He is suffering ___ fever.",
        "options": ["from", "with", "by", "in"],
        "answer": "from",
        "subject": "English",
        "difficulty": "easy"
    },
    {
        "question": "What is the area of a rectangle with length 10 cm and width 5 cm?",
        "options": ["15 sq cm", "20 sq cm", "25 sq cm", "50 sq cm"],
        "answer": "50 sq cm",
        "subject": "Math",
        "difficulty": "easy"
    },
    {
        "question": "'हाथ मलना' मुहावरे का अर्थ क्या है?",
        "options": ["खुश होना", "दुखी होना", "पछताना", "क्रोध करना"],
        "answer": "पछताना",
        "subject": "Hindi",
        "difficulty": "easy"
    },
    {
        "question": "The first Indian woman to climb Mount Everest was:",
        "options": ["Arunima Sinha", "Bachendri Pal", "Santosh Yadav", "Premlata Agarwal"],
        "answer": "Bachendri Pal",
        "subject": "GK/GS",
        "difficulty": "easy"
    },
    {
        "question": "Select the correct sentence:",
        "options": ["She is more taller than her sister.", "She is taller than her sister.", "She is more tall than her sister.", "She is tall than her sister."],
        "answer": "She is taller than her sister.",
        "subject": "English",
        "difficulty": "easy"
    },
]

def load_chat_data():
    if os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, 'r') as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
    return {}

def load_personal_chat_ids():
    if os.path.exists(PERSONAL_CHAT_IDS_FILE):
        with open(PERSONAL_CHAT_IDS_FILE, 'r') as file:
            data = json.load(file)
            if isinstance(data, dict):
                return data
    return {}

def save_chat_data(chat_data):
    with open(CHAT_IDS_FILE, 'w') as file:
        json.dump(chat_data, file)

def save_personal_chat_ids(chat_data):
    with open(PERSONAL_CHAT_IDS_FILE, 'w') as file:
        json.dump(chat_data, file)

def add_chat_id(chat_id, bot: Bot):
    chat_data = load_chat_data()
    if chat_id not in chat_data:
        try:
            # Check if the bot is an admin in the group or channel
            chat_admins = bot.get_chat_administrators(chat_id)
            for admin in chat_admins:
                if admin.user.id == bot.id:
                    chat_data[chat_id] = {"interval": 300}
                    save_chat_data(chat_data)
                    break
        except Exception as e:
            logger.error(f"Error checking admin status for chat {chat_id}: {e}")

def add_personal_chat_id(chat_id):
    chat_data = load_personal_chat_ids()
    if chat_id not in chat_data:
        chat_data[chat_id] = {"interval": 30}
        save_personal_chat_ids(chat_data)

def set_interval(update: Update, context: CallbackContext) -> None:
    """Set custom interval for sending quizzes."""
    chat_id = update.message.chat_id
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text('Usage: /setinterval <seconds>')
        return

    interval = int(context.args[0])
    if update.message.chat.type == "private":
        chat_data = load_personal_chat_ids()
    else:
        chat_data = load_chat_data()

    if chat_id in chat_data:
        chat_data[chat_id]["interval"] = interval
        if update.message.chat.type == "private":
            save_personal_chat_ids(chat_data)
        else:
            save_chat_data(chat_data)
        update.message.reply_text(f'Interval set to {interval} seconds.')
    else:
        update.message.reply_text('Chat ID not found. Please start the bot using /start.')

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    chat_id = update.message.chat_id
    if update.message.chat.type == "private":
        add_personal_chat_id(chat_id)
    else:
        add_chat_id(chat_id, context.bot)
    update.message.reply_text('Hi! Use /gcquiz to start sending quizzes in group chats, /prequiz to start sending quizzes in personal chats, and /setinterval <seconds> to set a custom interval. Use /stop to stop sending quizzes.')

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help! Use /gcquiz to start sending quizzes in group chats, /prequiz to start sending quizzes in personal chats, and /setinterval <seconds> to set a custom interval. Use /stop to stop sending quizzes.')

def gcquiz(update: Update, context: CallbackContext) -> None:
    """Start sending quizzes to group chats."""
    chat_id = update.message.chat_id
    chat_data = load_chat_data()
    if chat_id in chat_data:
        context.job_queue.run_repeating(send_quiz_to_group, interval=timedelta(seconds=chat_data[chat_id]["interval"]), first=0, context=chat_id, name=str(chat_id))
    else:
        update.message.reply_text('Chat ID not found. Please start the bot using /start.')

def prequiz(update: Update, context: CallbackContext) -> None:
    """Start sending quizzes to personal chats."""
    chat_id = update.message.chat_id
    personal_chat_data = load_personal_chat_ids()
    if chat_id in personal_chat_data:
        context.job_queue.run_repeating(send_quiz_to_personal, interval=timedelta(seconds=personal_chat_data[chat_id]["interval"]), first=0, context=chat_id, name=str(chat_id))
    else:
        update.message.reply_text('Chat ID not found. Please start the bot using /start.')

def stop(update: Update, context: CallbackContext) -> None:
    """Stop sending quizzes."""
    chat_id = update.message.chat_id
    jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in jobs:
        job.schedule_removal()
    update.message.reply_text('Stopped sending quizzes.')

def receive_quiz_answer(update: Update, context: CallbackContext) -> None:
    """Summarize a user's quiz vote"""
    answer = update.poll_answer
    if answer is None:
        logger.error("Received poll answer is None")
        return

    poll_id = answer.poll_id
    selected_option = answer.option_ids[0]

    questions = context.bot_data[poll_id]["questions"]
    selected_option_str = questions[selected_option]

    context.bot_data[poll_id]["answers"] += 1
    total_answers = context.bot_data[poll_id]["answers"]

    update.effective_message.reply_text(
        f"User {update.effective_user.first_name} voted for {selected_option_str}. Total votes: {total_answers}."
    )

def send_quiz_to_group(context: CallbackContext) -> None:
    """Send a specific predefined quiz to a group chat."""
    job = context.job
    chat_id = job.context
    chat_data = load_chat_data()
    if chat_id not in chat_data:
        return

    quiz_index = context.chat_data.get('quiz_index', 0)
    quiz_data = quizzes[quiz_index]

    try:
        correct_option_id = quiz_data["options"].index(quiz_data["answer"])
        message = context.bot.send_poll(
            chat_id=chat_id,
            question=quiz_data["question"],
            options=quiz_data["options"],
            type=Poll.QUIZ,
            correct_option_id=correct_option_id,
            is_anonymous=False,  # Change to True if you want anonymous quizzes
        )
        # Save some info about the quiz the bot just sent in case it's needed
        payload = {
            message.poll.id: {
                "questions": quiz_data["options"],
                "message_id": message.message_id,
                "chat_id": chat_id,
                "answers": 0,
            }
        }
        context.bot_data.update(payload)
    except Exception as e:
        logger.error(f"Error sending quiz to chat {chat_id}: {e}")

    # Schedule the next quiz to be sent after the custom interval
    quiz_index = (quiz_index + 1) % len(quizzes)
    context.chat_data['quiz_index'] = quiz_index

def send_quiz_to_personal(context: CallbackContext) -> None:
    """Send a specific predefined quiz to a personal chat."""
    job = context.job
    chat_id = job.context
    personal_chat_data = load_personal_chat_ids()
    if chat_id not in personal_chat_data:
        return

    quiz_index = context.chat_data.get('quiz_index', 0)
    quiz_data = quizzes[quiz_index]

    try:
        correct_option_id = quiz_data["options"].index(quiz_data["answer"])
        message = context.bot.send_poll(
            chat_id=chat_id,
            question=quiz_data["question"],
            options=quiz_data["options"],
            type=Poll.QUIZ,
            correct_option_id=correct_option_id,
            is_anonymous=False,
        )
        payload = {
            message.poll.id: {
                "questions": quiz_data["options"],
                "message_id": message.message_id,
                "chat_id": chat_id,
                "answers": 0,
            }
        }
        context.bot_data.update(payload)
    except Exception as e:
        logger.error(f"Error sending quiz to personal chat {chat_id}: {e}")

    # Schedule the next quiz to be sent after the custom interval
    quiz_index = (quiz_index + 1) % len(quizzes)
    context.chat_data['quiz_index'] = quiz_index

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("5503691929:AAHruRPFP3998zJCM4PGHOnmltkFYyeu8zk")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("gcquiz", gcquiz))
    dispatcher.add_handler(CommandHandler("prequiz", prequiz))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("setinterval", set_interval))

    # Add handler to save chat IDs when a message is received
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, start))

    # on noncommand i.e. message - echo the message on Telegram
    dispatcher.add_handler(PollHandler(receive_quiz_answer))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__name__':
    main()
