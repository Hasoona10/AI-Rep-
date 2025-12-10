# 🌐 Get Your Cloudflare Tunnel URL

## ✅ Cloudflare Tunnel is Running!

It's running in the background. To see the URL, you have two options:

## Option 1: Check Terminal Output (Easiest)

**Open a NEW Terminal window** and run:

```bash
cloudflared tunnel --url http://localhost:8000
```

You'll immediately see output like:
```
Your quick Tunnel has been created! Visit it at:
https://random-name-here.trycloudflare.com
```

**Copy that URL!**

## Option 2: Use the Previous URL

From earlier, your Cloudflare URL was:
**https://celebrities-relationships-folder-morgan.trycloudflare.com**

You can try using this URL in Twilio. If it doesn't work, get a fresh one using Option 1.

## 📞 Update Twilio Webhook

Once you have the URL:

1. Go to Twilio Console → Phone Numbers → `(714) 278-3407` → Configure
2. Under "A call comes in", set URL to:
   ```
   https://YOUR-URL.trycloudflare.com/api/twilio/voice/incoming
   ```
3. Save configuration

## 💡 Pro Tip

**Keep Cloudflare Tunnel running** in its own terminal window so you can see it. Don't close that terminal!

## 🎯 Quick Command

Just run this in a new terminal:
```bash
cloudflared tunnel --url http://localhost:8000
```

The URL will be printed right there! 📋


