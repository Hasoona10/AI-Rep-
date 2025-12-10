# ✅ Verify Your Setup

## 1. Check Your Verified Phone Number in Twilio

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/verified
2. Make sure your phone number is listed there
3. If not, add it by clicking "Add a new number" and verify it

## 2. Verify Twilio Webhook Configuration

1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click on your number: `(714) 278-3407`
3. Scroll down to "Voice & Fax" section
4. Under "A call comes in", make sure the URL is set to:
   ```
   https://advice-powerseller-bidding-portsmouth.trycloudflare.com/api/twilio/voice/incoming
   ```
   (Use your current Cloudflare Tunnel URL)

5. Under "Call status changes", set to:
   ```
   https://advice-powerseller-bidding-portsmouth.trycloudflare.com/api/twilio/voice/status
   ```

6. Click "Save configuration"

## 3. Verify Everything is Running

✅ **Server** (Terminal 1): Should show "Application startup complete"
✅ **Cloudflare Tunnel** (Terminal 2): Should show "Registered tunnel connection"

## 4. Test the Webhook URL

Open this URL in your browser (replace with your Cloudflare URL):
```
https://advice-powerseller-bidding-portsmouth.trycloudflare.com/health
```

You should see: `{"status":"healthy"}`

## 5. Test the Call

1. Call `(714) 278-3407` from your **verified phone number**
2. You should hear: "Hello! Welcome to Bella Vista Restaurant..."
3. Check your server terminal - you should see log messages like:
   ```
   INFO - Incoming call - SID: CA..., From: +1...
   ```

## 🔍 Troubleshooting

### If you still get "trial account" message:
- Double-check your phone number is verified in Twilio Console
- Make sure you're calling from the EXACT number you verified (including country code)

### If the call doesn't connect:
- Check that Cloudflare Tunnel is still running
- Verify the webhook URL in Twilio matches your Cloudflare URL exactly
- Check server logs for any errors

### If you see errors in server logs:
- Make sure the server is running on port 8000
- Check that Cloudflare Tunnel is pointing to `http://localhost:8000`


