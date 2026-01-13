import os
from dotenv import load_dotenv
import requests

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = "https://bingo-bot-gwg6.onrender.com"  # Replace with your actual domain

def set_webhook():
    """Set up webhook for Telegram bot"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    payload = {
        "url": WEBHOOK_URL,
        "allowed_updates": ["message", "callback_query"]
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("✓ Webhook set successfully!")
        print(response.json())
    else:
        print("✗ Failed to set webhook")
        print(response.json())

def delete_webhook():
    """Delete webhook (useful for local testing)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    response = requests.post(url)
    
    if response.status_code == 200:
        print("✓ Webhook deleted successfully!")
    else:
        print("✗ Failed to delete webhook")

def get_bot_info():
    """Get bot information"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    response = requests.get(url)
    
    if response.status_code == 200:
        print("✓ Bot Info:")
        print(response.json())
    else:
        print("✗ Failed to get bot info")

if __name__ == "__main__":
    print("Telegram Bot Setup")
    print("=" * 40)
    
    # First, get bot info to verify token works
    get_bot_info()
    
    print("\nOptions:")
    print("1. Set webhook (for production)")
    print("2. Delete webhook (for local testing)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        webhook = input("Enter your webhook URL: ")
        WEBHOOK_URL = webhook
        set_webhook()
    elif choice == "2":
        delete_webhook()
    else:
        print("Exiting...")