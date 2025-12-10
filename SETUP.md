# Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd ai-assistant/backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- `OPENAI_API_KEY`: Get from https://platform.openai.com/api-keys
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`: Get from https://console.twilio.com
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number

### 3. Seed Business Data

```bash
python scripts/seed_business_data.py
```

### 4. Run the Server

```bash
python run.py
```

Or:

```bash
cd backend
python -m uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### 5. Test the API

Visit `http://localhost:8000` in your browser or check:

```bash
curl http://localhost:8000/health
```

## Twilio Setup

1. Go to [Twilio Console](https://console.twilio.com)
2. Get a phone number (or use your existing one)
3. Configure Voice webhook:
   - Voice URL: `https://your-domain.com/api/twilio/voice/incoming`
   - Status Callback: `https://your-domain.com/api/twilio/voice/status`

For local development, use [ngrok](https://ngrok.com) to expose your local server:

```bash
ngrok http 8000
```

Then use the ngrok URL in Twilio webhooks.

## Widget Testing

1. Start the server
2. Open `widget/index.html` in your browser
3. The chat widget should appear in the bottom-right corner

Or embed in your website:

```html
<script>
window.AIReceptionistConfig = {
    apiUrl: 'http://localhost:8000',
    businessId: 'restaurant_001'
};
</script>
<script src="http://localhost:8000/widget/widget.js"></script>
```

## Testing

Run intent classification tests:

```bash
cd backend
pytest tests/test_intents.py -v
```

## Next Steps

- Customize business data in `backend/business_data.json`
- Add more intents in `backend/intents.py`
- Configure reservation rules in `backend/reservation_logic.py`
- Set up dashboard (Phase 5)
- Integrate Stripe (Phase 6)


