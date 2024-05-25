from telethon import TelegramClient, events
import re
import logging
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
wbgt_channel = int(os.getenv('WBGT_CHANNEL'))
cat_channel = int(os.getenv('CAT_CHANNEL'))
test_wbgt_channel = int(os.getenv('TEST_WBGT_CHANNEL'))
destination_channel = int(os.getenv('DESTINATION_CHANNEL'))

client = TelegramClient('new', api_id, api_hash)

SINGAPORE_TZ = pytz.timezone('Asia/Singapore')

class UpdateHandler:
    def __init__(self):
        self.track_wbgt = ''
        self.track_cat_status = 'No CAT 1 update as of now'
        self.last_message_id = None
        self.last_temp = None
        self.cat_timing = None

    def determine_wbgt(self, temperature):
        """Determine WBGT color code and emoji based on the temperature."""
        if temperature <= 29.9:
            return 'WHITE', '⚪️'
        elif temperature <= 30.9:
            return 'GREEN', '🟢'
        elif temperature <= 31.9:
            return 'YELLOW', '🟡'
        elif temperature <= 32.9:
            return 'RED', '🔴'
        else:
            return 'BLACK', '⚫️'

    def create_message(self):
        """Create the combined WBGT and CAT status message."""
        now = datetime.now(SINGAPORE_TZ)
        current_date = now.strftime('%d %b %Y')
        current_time = now.strftime('%H:%M')
        if self.last_temp is not None:
            wbgt_color, wbgt_emoji = self.determine_wbgt(self.last_temp)
            wbgt_status = f"{wbgt_emoji} {wbgt_color} {self.last_temp}℃"
        else:
            wbgt_status = "No WBGT update available"
        
        message = (
            f"**SAFTI-MI STATUS**\n"
            f"{current_date} {current_time}\n"
            f"================================\n"
            f"{wbgt_status}\n"
            f"{self.track_cat_status}\n"
            f"================================"
        )
        return message

    def update_cat_status(self, timing):
        """Update CAT status based on the timing and current time."""
        now = datetime.now(SINGAPORE_TZ)
        start_time, end_time = timing.split('-')
        start_time = datetime.strptime(start_time, '%H%M').replace(year=now.year, month=now.month, day=now.day, tzinfo=SINGAPORE_TZ)
        end_time = datetime.strptime(end_time, '%H%M').replace(year=now.year, month=now.month, day=now.day, tzinfo=SINGAPORE_TZ)

        if start_time <= now <= end_time:
            self.cat_timing = timing
            return f"CAT 1: {timing[:2]}:{timing[2:4]} - {timing[5:7]}:{timing[7:]}"
        else:
            self.cat_timing = None
            return 'No CAT 1 update as of now'

    async def handle_wbgt_message(self, message_content):
        """Handle WBGT messages and send updates to the destination channel."""
        logger.info("Handling WBGT message")
        safti_temp_match = re.search(r"SAFTI-MI, (\d+\.\d+)℃", message_content)
        if safti_temp_match:
            safti_temp = float(safti_temp_match.group(1))
            wbgt_color, wbgt_emoji = self.determine_wbgt(safti_temp)

            if self.track_wbgt != wbgt_color:
                self.track_wbgt = wbgt_color
                self.last_temp = safti_temp
                final_message = self.create_message()
                logger.info(f"Sending WBGT message: {final_message}")
                try:
                    sent_message = await client.send_message(destination_channel, final_message)
                    self.last_message_id = sent_message.id
                    logger.info(f"Message sent with ID: {self.last_message_id}")
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
            elif self.last_message_id:
                self.last_temp = safti_temp
                final_message = self.create_message()
                logger.info(f"Editing WBGT message to: {final_message}")
                try:
                    await client.edit_message(destination_channel, self.last_message_id, final_message)
                    logger.info("Message edited successfully")
                except Exception as e:
                    logger.error(f"Failed to edit message: {e}")
        else:
            logger.info("No match found for WBGT message")

    async def handle_cat_message(self, message_content):
        """Handle CAT messages and send alerts to the destination channel."""
        logger.info("Handling CAT message")
        if "02" in message_content and "CAT 1:" in message_content:
            timing_match = re.search(r"\((\d{4}-\d{4})\)\n(?:.*?,)*?02", message_content)
            if timing_match:
                timing = timing_match.group(1)
                cat_status = self.update_cat_status(timing)
                if self.track_cat_status != cat_status:
                    self.track_cat_status = cat_status
                    final_message = self.create_message()
                    logger.info(f"Sending CAT message: {final_message}")
                    try:
                        sent_message = await client.send_message(destination_channel, final_message)
                        self.last_message_id = sent_message.id
                        logger.info(f"Message sent with ID: {self.last_message_id}")
                    except Exception as e:
                        logger.error(f"Failed to send message: {e}")
            else:
                logger.info("No timing match found in CAT message")
        elif "All Sectors Clear" in message_content or "02" not in message_content:
            self.track_cat_status = 'No CAT 1 update as of now'
            final_message = self.create_message()
            logger.info(f"Sending CAT clear message: {final_message}")
            try:
                sent_message = await client.send_message(destination_channel, final_message)
                self.last_message_id = sent_message.id
                logger.info(f"Message sent with ID: {self.last_message_id}")
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
        else:
            logger.info("Message does not contain CAT 1 and sector 02")

    async def handler(self, event):
        """Main event handler for incoming messages."""
        try:
            message_content = event.message.text
            chat_id = event.chat_id
            logger.info(f"Received message from chat_id {chat_id}: {message_content}")

            if chat_id == wbgt_channel:
                logger.info("Message from WBGT channel")
                await self.handle_wbgt_message(message_content)
            elif chat_id == cat_channel:
                logger.info("Message from CAT channel")
                await self.handle_cat_message(message_content)
            elif chat_id == test_wbgt_channel:
                logger.info("Message from TEST WBGT channel")
                await self.handle_wbgt_message(message_content)
            else:
                logger.info(f"Message from unknown channel (chat_id: {chat_id})")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

update_handler = UpdateHandler()
client.on(events.NewMessage(chats=[wbgt_channel, cat_channel, test_wbgt_channel]))(update_handler.handler)

with client:
    logger.info("Starting client...")
    logger.info(f"WBGT CHANNEL ID: {wbgt_channel}")
    logger.info(f"CAT CHANNEL ID: {cat_channel}")
    logger.info(f"TEST WBGT CHANNEL ID: {test_wbgt_channel}")
    client.run_until_disconnected()
    logger.info("Client stopped.")
