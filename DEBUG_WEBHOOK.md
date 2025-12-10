# 🐛 Debugging "Application Error" from Twilio

## What We Just Fixed

I added better error logging to help us see what's happening. The server will now log:
- The exact error message
- The full stack trace
- The TwiML that's being generated

## Next Steps

### 1. Check Your Server Logs

When you call the number, **immediately check your server terminal** (where `python run.py` is running).

Look for:
- `INFO - Incoming call - SID: CA..., From: +1...`
- `INFO - Generated TwiML: ...`
- `ERROR - Error handling incoming call: ...` (if there's an error)

**Copy and share any error messages you see!**

### 2. Check Twilio Call Logs

1. Go to: https://console.twilio.com/us1/monitor/logs/calls
2. Find your recent call attempt
3. Click on it to see details
4. Look for:
   - **Status**: What status does it show?
   - **Error Code**: Any error codes?
   - **Error Message**: What does it say?

### 3. Verify Webhook URL

Make sure in Twilio Console, your webhook URL is:
```
https://advice-powerseller-bidding-portsmouth.trycloudflare.com/api/twilio/voice/incoming
```

**Important**: Make sure:
- It starts with `https://`
- No trailing slash
- The path is exactly `/api/twilio/voice/incoming`

### 4. Test the Webhook Manually

You can test if the webhook is working by simulating a Twilio request:

```bash
curl -X POST https://advice-powerseller-bidding-portsmouth.trycloudflare.com/api/twilio/voice/incoming \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "CallSid=CA1234567890&From=%2B17145551234"
```

You should get back XML (TwiML) that looks like:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">Hello! Welcome to Bella Vista Restaurant...</Say>
  ...
</Response>
```

### 5. Common Issues

#### Issue: "Application Error" from Twilio
**Possible causes**:
- Webhook returned invalid TwiML
- Webhook timed out (took > 5 seconds)
- Webhook returned error status code
- Webhook URL is unreachable

**Solution**: Check server logs for the actual error

#### Issue: Webhook timeout
**Solution**: Make sure your server responds quickly (< 5 seconds)

#### Issue: Invalid TwiML
**Solution**: Check the TwiML format in server logs

## What to Share

When you call again, please share:
1. **Server log output** (especially any ERROR messages)
2. **Twilio call log details** (from Twilio Console)
3. **Any error messages** you see

This will help us pinpoint the exact issue!


