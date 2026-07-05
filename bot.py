import discord
import os
import asyncio
from dotenv import load_dotenv
from database import init_db, save_message, get_user_messages, search_messages
import logging
from datetime import datetime
import sys

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.dm_messages = True
intents.members = True

class MessageLoggerBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False
        self.logging = True

    async def on_ready(self):
        logger.info(f"Bot logged in as {self.user}")
        logger.info(f"Watching {len(self.guilds)} servers")
        self.logging = True

    async def on_message(self, message):
        if not self.logging:
            return

        # Skip bot messages
        if message.author.bot:
            return

        try:
            # Determine if it's a DM or server message
            is_dm = isinstance(message.channel, discord.DMChannel)
            channel_id = message.channel.id
            server_id = message.guild.id if message.guild else None
            server_name = message.guild.name if message.guild else "Direct Messages"

            # Save to database
            await save_message(
                user_id=message.author.id,
                username=message.author.name,
                display_name=message.author.display_name,
                content=message.content,
                channel_id=channel_id,
                channel_name=message.channel.name if hasattr(message.channel, 'name') else "DM",
                server_id=server_id,
                server_name=server_name,
                timestamp=datetime.utcnow(),
                is_dm=is_dm
            )
            logger.info(f"Logged message from {message.author} in {server_name}")

        except Exception as e:
            logger.error(f"Error logging message: {e}")

    async def on_command_error(self, ctx, error):
        logger.error(f"Command error: {error}")

async def start_bot():
    bot = MessageLoggerBot()
    token = os.getenv('DISCORD_USER_TOKEN')
    if not token:
        logger.error("DISCORD_USER_TOKEN not set!")
        sys.exit(1)
    
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Start bot
    asyncio.run(start_bot())
