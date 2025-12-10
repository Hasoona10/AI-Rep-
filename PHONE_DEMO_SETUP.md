# Phone Call Demo - Quick Setup Guide

## ✅ What's Already Done

1. ✅ Virtual environment created (`venv/`)
2. ✅ Core dependencies installed (FastAPI, Twilio, OpenAI, ChromaDB)
3. ✅ Business data seeded into RAG system
4. ✅ Setup script created (`setup_env.py`)

## 🚀 Next Steps to Run Your Phone Demo

### Step 1: Create `.env` File

You need to create a `.env` file in the project root with your credentials. Run:

```bash
cd "/Users/souna/Desktop/local product/ai-assistant"
python setup_env.py
```

Or manually create `.env` with:

```bash
# Twilio Credentials (REQUIRED)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+17142783407

# OpenAI API Key (REQUIRED for AI responses)
OPENAI_API_KEY=your_openai_api_key_here

# Database
CHROMA_DB_PATH=./chroma_db

# Application Settings
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
LOG_LEVEL=INFO
DEFAULT_BUSINESS_ID=restaurant_001
```

### Step 2: Verify Your Phone Number in Twilio

Since you're on a trial account:
1. Go to Twilio Console → Verify → Verified Caller IDs
2. Add and verify your personal phone number
3. This allows you to call your Twilio number for testing

### Step 3: Start the Server

```bash
cd "/Users/souna/Desktop/local product/ai-assistant"
source venv/bin/activate
python run.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 4: Expose Server with ngrok

In a **new terminal window**:

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### Step 5: Configure Twilio Webhooks

1. Go to Twilio Console → Phone Numbers → Manage → Active numbers
2. Click your phone number `(714) 278-3407`
3. Scroll to "Voice Configuration"
4. Set:
   - **A call comes in**: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/incoming`
   - **Call status changes**: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/status`
5. Click "Save configuration"

### Step 6: Test the Call! 📞

1. Call `(714) 278-3407` from your verified phone number
2. You should hear: "Hello! Welcome to Bella Vista Restaurant. How can I help you today?"
3. Try asking:
   - "What are your hours?"
   - "What's on your menu?"
   - "I'd like to make a reservation for 2 people tomorrow at 7pm"
   - "What's your address?"

## 🐛 Troubleshooting

### Server won't start
- Check that `.env` file exists and has valid credentials
- Make sure virtual environment is activated: `source venv/bin/activate`

### "No response from webhook"
- Verify ngrok is running and URL is correct
- Check that webhook URLs in Twilio use HTTPS (not HTTP)
- Look at server logs for errors

### "I didn't catch that"
- Speak clearly into the phone
- Check server logs to see if speech was received

### Can't call the number
- Make sure your phone number is verified in Twilio Console
- Trial accounts can only call verified numbers

## 📝 Important Notes

- **Keep ngrok running** while testing - if you restart it, you'll get a new URL and need to update webhooks
- **Keep server running** in one terminal, ngrok in another
- The AI uses business data from `backend/business_data.json` for responses
- All call logs will appear in your server terminal

## 🎯 What Works Now

✅ Phone calls via Twilio  
✅ Speech recognition (Twilio's built-in)  
✅ Intent classification (ML → Rule → LLM fallback)  
✅ RAG-based responses using business data  
✅ Reservation handling  
✅ Multi-turn conversations  

Enjoy your phone call demo! 🎉


