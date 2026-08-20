"""
Telegram StringSession Generator
Run this script LOCALLY on your computer once to generate a TELEGRAM_SESSION_STRING.
You can then paste this string into Render's Environment Variables.
"""

import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")


async def main():
    print("\n" + "=" * 70)
    print("🔑 TELEGRAM STRING SESSION GENERATOR FOR CLOUD / RENDER")
    print("=" * 70)

    if not API_ID or not API_HASH:
        print("❌ Error: API_ID and API_HASH must be configured in your .env file!")
        return

    print("Connecting to Telegram to generate a portable session string...")
    print("If prompted, enter your Phone Number and the OTP code sent to Telegram.\n")

    # Connect with an empty StringSession
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        session_string = client.session.save()

        print("\n" + "=" * 70)
        print("✅ SUCCESS! HERE IS YOUR TELEGRAM_SESSION_STRING:")
        print("=" * 70 + "\n")
        print(session_string)
        print("\n" + "=" * 70)
        print("📋 HOW TO USE ON RENDER:")
        print("1. Copy the long session string above.")
        print("2. In your Render Dashboard ➔ Environment Variables, add:")
        print("   Key:   TELEGRAM_SESSION_STRING")
        print("   Value: (paste your copied string)")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
