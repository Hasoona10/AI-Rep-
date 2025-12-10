# 🔍 Check Your Server Logs

## Critical: We Need to See the Error

The "application error" means something is failing, but we need to see **what** is failing.

## Steps to Debug

### 1. Check Your Server Terminal

**Look at the terminal where your server is running** (`python run.py` or `uvicorn`).

When you call the number, you should see **one of these**:

#### ✅ If you see logs:
```
INFO - Incoming call - SID: CA..., From: +1...
```
**Good!** The webhook is being called. If you see an error after this, share it.

#### ❌ If you see NO logs:
**Problem:** Twilio isn't reaching your server. This means:
- Webhook URL in Twilio is wrong
- Cloudflare Tunnel isn't running
- Server isn't running

### 2. Check Twilio Call Logs

1. Go to: https://console.twilio.com/us1/monitor/logs/calls
2. Find your most recent call
3. Click on it
4. **Look for these fields:**
   - **Request URL**: What URL did Twilio try?
   - **Request Method**: Should be `POST`
   - **Response Status**: What HTTP status code? (200, 400, 500, etc.)
   - **Error Code**: Any error code?
   - **Error Message**: What does it say?

### 3. Verify Everything is Running

**Terminal 1 - Server:**
```bash
# Should show:
INFO:     Application startup complete.
```

**Terminal 2 - Cloudflare Tunnel:**
```bash
# Should show:
INF Registered tunnel connection...
```

### 4. Test the Webhook Manually

Run this command (replace with your current Cloudflare URL):
```bash
curl -X POST https://water-exchange-verde-term.trycloudflare.com/api/twilio/voice/incoming \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Host: water-exchange-verde-term.trycloudflare.com" \
  -d "CallSid=CA123&From=%2B17145551234"
```

**Check your server terminal** - you should see logs from this test.

## What to Share

Please share:
1. **Server terminal output** (any logs when you call?)
2. **Twilio call log details** (Request URL, Response Status, Error Code/Message)
3. **Are both terminals running?** (Server + Cloudflare Tunnel)

## Quick Fixes

### If no logs appear:
1. Double-check webhook URL in Twilio matches your Cloudflare URL exactly
2. Make sure Cloudflare Tunnel is still running
3. Make sure server is running

### If you see error logs:
Share the exact error message and we'll fix it!


