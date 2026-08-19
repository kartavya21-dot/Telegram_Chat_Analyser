"""
Telegram Client - Listens to all messages and prints to console
No backend needed - just logs everything
"""

import os
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Telegram API credentials (get from my.telegram.org)
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# Check if credentials are set
if not API_ID or not API_HASH or not PHONE_NUMBER:
    print("❌ Missing credentials!")
    print("Please create .env.client with:")
    print("  API_ID=your_api_id")
    print("  API_HASH=your_api_hash")
    print("  PHONE_NUMBER=+91XXXXXXXXXX")
    exit(1)

# Create client
client = TelegramClient('session', API_ID, API_HASH)


@client.on(events.NewMessage)
async def handle_new_message(event):
    """Listen to all new messages and print to console"""
    
    try:
        # Get sender info
        sender = await event.get_sender()
        
        if not sender:
            return
        
        # Get sender details
        sender_username = sender.username or "No Username"
        sender_name = sender.first_name or "Unknown"
        sender_id = sender.id
        
        # Get message text
        message_text = event.text
        
        # Get timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if message_text:
            # Print to console in a nice format
            print(f"\n{'='*70}")
            print(f"📨 NEW MESSAGE RECEIVED!")
            print(f"{'='*70}")
            print(f"⏰ Time: {timestamp}")
            print(f"👤 From: {sender_name} (@{sender_username})")
            print(f"🆔 User ID: {sender_id}")
            print(f"💬 Message: {message_text}")
            print(f"{'='*70}\n")
    
    except Exception as e:
        print(f"❌ Error handling message: {e}")


async def main():
    """Start the Telegram client"""
    
    print(f"\n{'='*70}")
    print(f"🚀 TELEGRAM MESSAGE LISTENER")
    print(f"{'='*70}")
    print(f"📱 API_ID: {API_ID[:10]}..." if API_ID else "❌ API_ID not set")
    print(f"🔐 API_HASH: {API_HASH[:10]}..." if API_HASH else "❌ API_HASH not set")
    print(f"📞 Phone: {PHONE_NUMBER}")
    print(f"{'='*70}\n")
    
    try:
        # Start the client
        print("🔄 Connecting to Telegram...")
        await client.start(phone=PHONE_NUMBER)
        
        print("✅ Connected successfully!")
        print("👂 Listening for all incoming messages...")
        print("⏹️  Press CTRL+C to stop\n")
        
        # Keep running
        await client.run_until_disconnected()
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Listener stopped by user")