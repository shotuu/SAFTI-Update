from telethon import TelegramClient, events
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')

client = TelegramClient('simple_receiver', api_id, api_hash)

@client.on(events.NewMessage())
async def handler(event):
    """Event handler for incoming messages."""
    try:
        message_content = event.message.text
        chat_id = event.chat_id
        logger.info(f"Received message from chat_id {chat_id}: {message_content}")
    except Exception as e:
        logger.error(f"Error handling message: {e}")

with client:
    logger.info("Starting client to listen to all channels...")
    client.run_until_disconnected()
    logger.info("Client stopped.")
