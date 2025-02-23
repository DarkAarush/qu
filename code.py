import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

API_TOKEN = "5571306374:AAGsEQK3y5Qw8OzRcNLKxlxNAlbo1hoFykI"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot with updated syntax
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.reply("Hello! I'm a bot that can delete messages in this group. Make sure I'm an admin!")

@dp.message(Command("delete"))
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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
