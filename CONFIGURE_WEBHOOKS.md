# 🔗 Configure Twilio Webhooks - Step by Step

## Current Status
You're on the phone number configuration page for `(714) 278-3407`.

## What You Need First

Before configuring webhooks, you need:
1. ✅ `.env` file with your credentials (check if done)
2. ⏳ Server running on localhost:8000
3. ⏳ ngrok running to expose your server

## Step-by-Step Instructions

### Step 1: Click "Go to Configure"

On the page you're viewing, click the **"Go to Configure"** button (or click the **"Configure"** tab at the top).

### Step 2: Start Your Server (if not running)

Open Terminal and run:

```bash
cd "/Users/souna/Desktop/local product/ai-assistant"
./start_demo.sh
```

Wait until you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

### Step 3: Start ngrok (in NEW Terminal)

Open a **NEW Terminal window** and run:

```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copy the HTTPS URL** (the part that looks like `https://abc123.ngrok-free.app`)

**Keep this terminal open too!**

### Step 4: Configure Webhooks in Twilio

1. **In Twilio Console**, you should be on the "Configure" page for your number
2. Scroll down to **"Voice Configuration"** section
3. Under **"A call comes in"**:
   - Select: **Webhook**
   - URL: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/incoming`
     - Replace `your-ngrok-url.ngrok-free.app` with your actual ngrok URL!
   - HTTP Method: **POST**
4. Under **"Call status changes"**:
   - URL: `https://your-ngrok-url.ngrok-free.app/api/twilio/voice/status`
     - Same ngrok URL as above!
   - HTTP Method: **POST**
5. Scroll down and click **"Save configuration"**

### Step 5: Verify Setup

After saving, you should see:
- ✅ Webhook URLs saved
- ✅ Configuration active

### Step 6: Test!

1. Make sure your phone number is verified in Twilio (for trial accounts)
2. Call `(714) 278-3407` from your verified phone
3. You should hear: "Hello! Welcome to Bella Vista Restaurant..."

## 🎯 Quick Reference

**Webhook URLs to use:**
- Incoming calls: `https://YOUR-NGROK-URL.ngrok-free.app/api/twilio/voice/incoming`
- Status updates: `https://YOUR-NGROK-URL.ngrok-free.app/api/twilio/voice/status`

**Important:**
- Use HTTPS (not HTTP)
- No trailing slashes
- Replace `YOUR-NGROK-URL.ngrok-free.app` with your actual ngrok URL

## 🐛 Troubleshooting

**"No response from webhook"**
- Check ngrok is running
- Verify URLs are correct (HTTPS, no typos)
- Check server is running and shows startup logs

**Can't save webhooks?**
- Make sure URLs start with `https://`
- Check ngrok is running (the URL should be accessible)

**Need to restart ngrok?**
- You'll get a new URL - update the webhooks in Twilio!


