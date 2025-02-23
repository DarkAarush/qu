import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor

API_TOKEN = "5571306374:AAGsEQK3y5Qw8OzRcNLKxlxNAlbo1hoFykI"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: Message):
    await message.reply("Hello! I'm a bot that can delete messages in this group. Make sure I'm an admin!")

@dp.message_handler(commands=["delete"], is_chat_admin=True)
async def delete_message_command(message: Message):
    if message.reply_to_message:
        try:
            await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
            await message.reply("Message deleted successfully.")
        except Exception as e:
            logging.error(f"Failed to delete message: {e}")
            await message.reply("Failed to delete the message.")
    else:
        await message.reply("Please reply to the message you want to delete using /delete.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
