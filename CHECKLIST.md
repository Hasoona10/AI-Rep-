# ✅ Phone Demo Setup Checklist

## Step 1: Get Credentials ⏱️ 5 minutes

- [ ] **Twilio Account SID** 
  - Go to: https://console.twilio.com
  - Copy Account SID (starts with `AC...`)
  
- [ ] **Twilio Auth Token**
  - In Twilio Console, click "Show" next to Auth Token
  - Copy the token
  
- [ ] **Twilio Phone Number**
  - You have: `(714) 278-3407`
  - Format: `+17142783407`
  
- [ ] **OpenAI API Key**
  - Go to: https://platform.openai.com/api-keys
  - Create new key and copy it

## Step 2: Create .env File ⏱️ 2 minutes

- [ ] Open `.env` file in project root
- [ ] Replace `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` with your Twilio Account SID
- [ ] Replace `your_twilio_auth_token_here` with your Twilio Auth Token
- [ ] Replace `your_openai_api_key_here` with your OpenAI API Key
- [ ] Save the file

**Location:** `/Users/souna/Desktop/local product/ai-assistant/.env`

## Step 3: Verify Phone Number ⏱️ 2 minutes

- [ ] Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
- [ ] Click "Add a new number"
- [ ] Enter your personal phone number
- [ ] Verify via SMS or Call
- [ ] Enter verification code

## Step 4: Start Server ⏱️ 1 minute

- [ ] Open Terminal
- [ ] Run: `cd "/Users/souna/Desktop/local product/ai-assistant"`
- [ ] Run: `./start_demo.sh`
- [ ] Wait for: "Uvicorn running on http://0.0.0.0:8000"
- [ ] **Keep this terminal open!**

## Step 5: Start ngrok ⏱️ 1 minute

- [ ] Open a **NEW Terminal window**
- [ ] Run: `ngrok http 8000`
- [ ] Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)
- [ ] **Keep this terminal open!**

## Step 6: Configure Twilio Webhooks ⏱️ 3 minutes

- [ ] Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
- [ ] Click your number: `(714) 278-3407`
- [ ] Scroll to "Voice Configuration"
- [ ] Set "A call comes in" to: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/incoming`
- [ ] Set "Call status changes" to: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/status`
- [ ] Click "Save configuration"

## Step 7: Test! 📞

- [ ] Call `(714) 278-3407` from your verified phone
- [ ] You should hear the greeting
- [ ] Try asking questions!

## 🎉 Done!

Watch your server terminal for call logs and AI responses.

---

## Quick Commands Reference

```bash
# Start server
cd "/Users/souna/Desktop/local product/ai-assistant"
./start_demo.sh

# Start ngrok (in new terminal)
ngrok http 8000

# Edit .env file
open -e "/Users/souna/Desktop/local product/ai-assistant/.env"
```


