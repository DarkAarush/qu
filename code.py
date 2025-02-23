from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = '5571306374:AAGsEQK3y5Qw8OzRcNLKxlxNAlbo1hoFykI'

def delete_messages(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    user = update.message.from_user
    
    if not user or not user.id:
        return
    
    # Ensure the bot is an admin
    chat_member = context.bot.get_chat_member(chat_id, context.bot.id)
    if not chat_member.can_delete_messages:
        update.message.reply_text("I need 'Delete Messages' permission to delete messages!")
        return
    
    # Fetch recent messages and delete them
    for message_id in range(update.message.message_id, update.message.message_id - 100, -1):
        try:
            context.bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"Could not delete message {message_id}: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("clear", delete_messages))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, delete_messages))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
