# 🚨 FIX: Webhook URL is Missing the Path!

## The Problem

Twilio is calling:
```
https://water-exchange-verde-term.trycloudflare.com
```

But it should be calling:
```
https://water-exchange-verde-term.trycloudflare.com/api/twilio/voice/incoming
```

## The Fix

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click on `(714) 278-3407`
3. Scroll to **"Voice & Fax"** section
4. Under **"A call comes in"**, make sure it says:
   ```
   https://water-exchange-verde-term.trycloudflare.com/api/twilio/voice/incoming
   ```
   **NOT just:**
   ```
   https://water-exchange-verde-term.trycloudflare.com
   ```
5. **Click "Save configuration"**

## Why This Happened

The webhook URL in Twilio is missing the `/api/twilio/voice/incoming` path at the end. Twilio is calling the root URL, which returns a 405 error because the root endpoint doesn't accept POST requests.

## After Fixing

Once you update the URL with the full path, try calling again. You should:
1. Hear the greeting: "Hello! Welcome to Bella Vista Restaurant..."
2. See logs in your server terminal
3. The call should work properly!


