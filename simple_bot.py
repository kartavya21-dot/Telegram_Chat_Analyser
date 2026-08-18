import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx

load_dotenv()

app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BOT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


# Simple models to parse incoming messages
class User(BaseModel):
    id: int
    first_name: str
    username: str | None = None


class Chat(BaseModel):
    id: int
    type: str


class Message(BaseModel):
    message_id: int
    chat: Chat
    text: str | None = None
    from_user: dict | None = None
    
    class Config:
        populate_by_name = True


class Update(BaseModel):
    update_id: int
    message: Message | None = None


@app.get("/")
async def root():
    return {"status": "ok", "message": "Telegram bot is running"}


@app.get("/register-webhook")
async def register_webhook():
    """Register the webhook with Telegram"""
    try:
        webhook_url = f"{WEBHOOK_URL}/telegram/webhook"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BOT_URL}/setWebhook",
                json={"url": webhook_url}
            )
            
            result = response.json()
            
            if result.get("ok"):
                return {
                    "status": "success",
                    "message": f"Webhook registered at {webhook_url}",
                    "webhook_url": webhook_url
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("description", "Unknown error")
                }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/webhook-status")
async def webhook_status():
    """Check webhook status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BOT_URL}/getWebhookInfo"
            )
            
            result = response.json()
            
            if result.get("ok"):
                return {
                    "status": "ok",
                    "webhook_info": result.get("result")
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("description")
                }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/telegram/webhook")
async def webhook(update: Update):
    """Receive messages from Telegram and print to console"""
    
    try:
        if update.message and update.message.text:
            msg = update.message
            user_id = msg.from_user.get("id") if msg.from_user else "unknown"
            username = msg.from_user.get("username") if msg.from_user else "unknown"
            first_name = msg.from_user.get("first_name") if msg.from_user else "unknown"
            text = msg.text
            chat_id = msg.chat.id
            
            # Print to console
            print(f"\n{'='*60}")
            print(f"📨 New Message Received!")
            print(f"{'='*60}")
            print(f"From: {first_name} (@{username}) - ID: {user_id}")
            print(f"Chat ID: {chat_id}")
            print(f"Message: {text}")
            print(f"{'='*60}\n")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Always return 200
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    print(f"\n🚀 Starting bot on port {port}")
    print(f"\n📋 Available Endpoints:")
    print(f"   • Register Webhook: http://localhost:{port}/register-webhook")
    print(f"   • Check Status: http://localhost:{port}/webhook-status")
    print(f"   • Docs: http://localhost:{port}/docs")
    print(f"   • ReDoc: http://localhost:{port}/redoc")
    print(f"\n✅ Open http://localhost:{port}/register-webhook in your browser to register!\n")
    uvicorn.run("simple_bot:app", host="0.0.0.0", port=port, reload=True)