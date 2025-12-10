# 🚀 Start Your Phone Call Demo - Final Steps

## ✅ All Credentials Configured!

Your `.env` file is complete with:
- ✅ Twilio Account SID
- ✅ Twilio Auth Token  
- ✅ OpenAI API Key
- ✅ Twilio Phone Number

## 🎯 Next Steps to Start Demo

### Step 1: Start the Server

Open Terminal and run:

```bash
cd "/Users/souna/Desktop/local product/ai-assistant"
./start_demo.sh
```

**OR manually:**

```bash
cd "/Users/souna/Desktop/local product/ai-assistant"
source venv/bin/activate
python run.py
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Keep this terminal open!**

### Step 2: Start ngrok

Open a **NEW Terminal window** and run:

```bash
ngrok http 8000
```

You'll see:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok-free.app`)

**Keep this terminal open too!**

### Step 3: Configure Twilio Webhooks

1. Go back to Twilio Console (the page you were on)
2. Under **"Voice Configuration"** → **"A call comes in"**:
   - Select: **Webhook**
   - URL: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/incoming`
   - Method: **HTTP POST**
3. Under **"Call status changes"**:
   - URL: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/status`
   - Method: **HTTP POST**
4. Click **"Save configuration"**

**Replace `your-ngrok-url.ngrok-free.app` with your actual ngrok URL!**

### Step 4: Verify Your Phone Number (if not done)

For trial accounts, verify your phone:
1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
2. Add your personal phone number
3. Verify via SMS or Call

### Step 5: Test the Call! 📞

Call `(714) 278-3407` from your verified phone number.

You should hear:
> "Hello! Welcome to Bella Vista Restaurant. How can I help you today?"

Try asking:
- "What are your hours?"
- "What's on your menu?"
- "I'd like to make a reservation for 2 people tomorrow at 7pm"

## 🎉 You're Ready!

Watch your server terminal for:
- Incoming call logs
- Speech transcription
- Intent classification
- AI responses

## 🐛 Troubleshooting

**Server won't start?**
- Make sure virtual environment is activated
- Check `.env` file exists and has all credentials

**"No response from webhook"?**
- Verify ngrok is running
- Check webhook URLs use HTTPS (not HTTP)
- Make sure server is running

**Can't call?**
- Verify your phone number in Twilio Console
- Trial accounts can only call verified numbers


