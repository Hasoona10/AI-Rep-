# 🚀 Quick Start - Phone Call Demo

## ✅ Setup Complete!

Your project is ready for the phone call demo. Here's what's been set up:

- ✅ Python virtual environment created
- ✅ Core dependencies installed (FastAPI, Twilio, OpenAI, ChromaDB)
- ✅ Project structure verified
- ✅ Setup scripts created

## 📋 What You Need to Do Now

### 1. Create `.env` File (2 minutes)

Run this command and follow the prompts:

```bash
cd "/Users/souna/Desktop/local product/ai-assistant"
python setup_env.py
```

Or manually create `.env` in the project root:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+17142783407
OPENAI_API_KEY=your_openai_api_key_here
CHROMA_DB_PATH=./chroma_db
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
LOG_LEVEL=INFO
DEFAULT_BUSINESS_ID=restaurant_001
```

**Get your credentials:**
- Twilio: https://console.twilio.com (Account SID, Auth Token, Phone Number)
- OpenAI: https://platform.openai.com/api-keys

### 2. Verify Your Phone Number in Twilio (1 minute)

1. Go to Twilio Console → Verify → Verified Caller IDs
2. Add your personal phone number
3. Verify it (via SMS or call)

### 3. Start Everything (3 steps)

**Terminal 1 - Start Server:**
```bash
cd "/Users/souna/Desktop/local product/ai-assistant"
source venv/bin/activate
python run.py
```

**Terminal 2 - Start ngrok:**
```bash
ngrok http 8000
```
Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

**Terminal 3 - Configure Twilio:**
1. Go to Twilio Console → Phone Numbers → Your number `(714) 278-3407`
2. Set webhooks:
   - **A call comes in**: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/incoming`
   - **Call status changes**: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/status`
3. Save

### 4. Make a Test Call! 📞

Call `(714) 278-3407` from your verified phone and try:
- "What are your hours?"
- "What's on your menu?"
- "I'd like to make a reservation"

## 📚 Full Documentation

- **Detailed setup**: See `PHONE_DEMO_SETUP.md`
- **Project overview**: See `README.md`
- **ML features**: See `ML_README.md`

## 🎯 You're All Set!

Once you complete step 1 (create `.env`), you can start the demo. The server will automatically seed the business data on first startup.

**Need help?** Check the troubleshooting section in `PHONE_DEMO_SETUP.md`


