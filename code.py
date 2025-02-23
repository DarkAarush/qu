from telethon import TelegramClient, events from telethon.tl.functions.channels import EditBannedRequest from telethon.tl.types import ChatBannedRights import asyncio

Replace with your own values

API_ID = '25638120' API_HASH = '3b702ecd94ca01b76c1b78451a33833c' BOT_TOKEN = '7439280676:AAGx7Awfc7YqtVpyDVe-JjD7oaO9wTwHfeQ'

Initialize bot client

bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

Define ban rights

BAN_RIGHTS = ChatBannedRights( until_date=None,  # Permanent ban view_messages=True  # Restricts user from viewing messages (ban effect) )

@bot.on(events.NewMessage(pattern='/banall')) async def ban_all_users(event): if not event.is_group: await event.reply("This command can only be used in groups.") return

# Check if the sender is an admin
chat = await event.get_chat()
sender = await event.get_sender()
admins = await bot.get_participants(chat, filter=telethon.tl.types.ChannelParticipantsAdmins)

if sender.id not in [admin.id for admin in admins]:
    await event.reply("You must be an admin to use this command.")
    return

members = await bot.get_participants(chat)

await event.reply("Banning all members...")

for member in members:
    if member.id not in [admin.id for admin in admins]:  # Avoid banning admins
        try:
            await bot(EditBannedRequest(chat, member.id, BAN_RIGHTS))
            await asyncio.sleep(0.5)  # Short delay to avoid flood limits
        except Exception as e:
            await event.reply(f"Failed to ban {member.id}: {str(e)}")

await event.reply("All non-admin members have been banned.")

print("Bot is running...") bot.run_until_disconnected()

