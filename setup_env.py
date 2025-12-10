#!/usr/bin/env python3
"""
Helper script to create .env file with user input.
"""
import os
from pathlib import Path

def create_env_file():
    """Create .env file with user input."""
    env_path = Path(__file__).parent / ".env"
    
    if env_path.exists():
        print(f"⚠️  .env file already exists at {env_path}")
        response = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if response != 'y':
            print("Keeping existing .env file.")
            return
    
    print("\n🔧 Setting up .env file for AI Receptionist")
    print("=" * 50)
    
    # Get Twilio credentials
    print("\n📞 Twilio Configuration (Required for phone calls)")
    print("Get these from: https://console.twilio.com")
    twilio_account_sid = input("Twilio Account SID: ").strip()
    twilio_auth_token = input("Twilio Auth Token: ").strip()
    twilio_phone = input("Twilio Phone Number (e.g., +17142783407): ").strip()
    
    # Get OpenAI key
    print("\n🤖 OpenAI Configuration (Required for AI responses)")
    print("Get from: https://platform.openai.com/api-keys")
    openai_key = input("OpenAI API Key: ").strip()
    
    # Optional Stripe
    print("\n💳 Stripe Configuration (Optional - for Phase 6)")
    use_stripe = input("Set up Stripe? (y/n): ").strip().lower() == 'y'
    stripe_secret = ""
    stripe_publishable = ""
    if use_stripe:
        stripe_secret = input("Stripe Secret Key: ").strip()
        stripe_publishable = input("Stripe Publishable Key: ").strip()
    
    # Create .env content
    env_content = f"""# Twilio Credentials (REQUIRED for phone calls)
TWILIO_ACCOUNT_SID={twilio_account_sid}
TWILIO_AUTH_TOKEN={twilio_auth_token}
TWILIO_PHONE_NUMBER={twilio_phone}

# OpenAI API Key (REQUIRED for RAG responses)
OPENAI_API_KEY={openai_key}

# Database
CHROMA_DB_PATH=./chroma_db

# Stripe (Optional)
STRIPE_SECRET_KEY={stripe_secret if stripe_secret else 'sk_test_your_stripe_secret_key'}
STRIPE_PUBLISHABLE_KEY={stripe_publishable if stripe_publishable else 'pk_test_your_stripe_publishable_key'}

# Application Settings
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
LOG_LEVEL=INFO
DEFAULT_BUSINESS_ID=restaurant_001
"""
    
    # Write .env file
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"\n✅ .env file created successfully at {env_path}")
        print("\n📝 Next steps:")
        print("1. Verify your phone number in Twilio Console (for trial accounts)")
        print("2. Run: python scripts/seed_business_data.py")
        print("3. Run: python run.py")
        print("4. In another terminal: ngrok http 8000")
        print("5. Configure Twilio webhooks with your ngrok URL")
    except Exception as e:
        print(f"\n❌ Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_file()


