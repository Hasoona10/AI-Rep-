# 📞 Step-by-Step Phone Demo Setup

## Step 1: Get Your Credentials

### A. Twilio Credentials (from Twilio Console)

1. Go to: https://console.twilio.com
2. On the dashboard, you'll see:
   - **Account SID** (starts with `AC...`) - Copy this
   - **Auth Token** - Click "Show" to reveal, then copy
   - **Phone Number** - You already have: `(714) 278-3407` → Format as `+17142783407`

### B. OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (you won't see it again!)

## Step 2: Create `.env` File

Create a file named `.env` in the project root (`/Users/souna/Desktop/local product/ai-assistant/.env`) with this content:

```bash
# Twilio Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+17142783407

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Database
CHROMA_DB_PATH=./chroma_db

# Application Settings
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
LOG_LEVEL=INFO
DEFAULT_BUSINESS_ID=restaurant_001
```

**Replace:**
- `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` with your Twilio Account SID
- `your_twilio_auth_token_here` with your Twilio Auth Token
- `your_openai_api_key_here` with your OpenAI API Key

## Step 3: Verify Your Phone Number in Twilio

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
2. Click "Add a new number" or "Verify a number"
3. Enter your personal phone number
4. Choose verification method (SMS or Call)
5. Enter the code you receive

**Why?** Trial accounts can only receive calls from verified numbers.

## Step 4: Start the Server

Open Terminal and run:

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

**Keep this terminal open!**

## Step 5: Start ngrok

Open a **NEW Terminal window** and run:

```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok-free.app`)

**Keep this terminal open too!**

## Step 6: Configure Twilio Webhooks

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click on your phone number: `(714) 278-3407`
3. Scroll down to **"Voice Configuration"**
4. Under **"A call comes in"**:
   - Select: **Webhook**
   - URL: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/incoming`
   - Method: **HTTP POST**
5. Under **"Call status changes"**:
   - URL: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/status`
   - Method: **HTTP POST**
6. Click **"Save configuration"** at the bottom

**Important:** Replace `your-ngrok-url.ngrok-free.app` with your actual ngrok URL!

## Step 7: Test the Call! 📞

1. Call `(714) 278-3407` from your verified phone number
2. You should hear: "Hello! Welcome to Bella Vista Restaurant. How can I help you today?"
3. Try asking:
   - "What are your hours?"
   - "What's on your menu?"
   - "I'd like to make a reservation for 2 people tomorrow at 7pm"
   - "What's your address?"

## 🎉 You're Done!

Watch your server terminal for logs showing:
- Incoming call received
- Speech transcribed
- Intent classified
- AI response generated

## 🐛 Troubleshooting

**Server won't start?**
- Check `.env` file exists and has correct credentials
- Make sure virtual environment is activated

**"No response from webhook"?**
- Verify ngrok is running
- Check webhook URLs use HTTPS (not HTTP)
- Make sure URLs match exactly (no trailing slashes)

**Can't call?**
- Verify your phone number in Twilio Console
- Trial accounts can only call verified numbers

**Need to restart ngrok?**
- You'll get a new URL - update Twilio webhooks!


