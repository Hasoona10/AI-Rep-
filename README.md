# AI Receptionist - Multi-Channel AI Assistant for Local Businesses

An intelligent receptionist system for local businesses (restaurants first) that handles phone calls, web chat, and reservations using AI.

**Repository**: [https://github.com/Hasoona10/AI-Rep-](https://github.com/Hasoona10/AI-Rep-)

## 🚀 Features

### ML Components (NEW) ✅
- **Trained Intent Classifier**: Supervised ML model (Random Forest, SVM, Logistic Regression)
- **Feature Extraction**: TF-IDF, Bag-of-Words, PCA
- **Model Training Pipeline**: Automated training with cross-validation
- **Evaluation Framework**: Comprehensive metrics (accuracy, F1, precision, recall)
- **Model Comparison**: ML vs. Rule-based vs. LLM API comparison
- **Model Registry**: Version tracking and best model selection
- **Fallback Strategy**: Intelligent fallback (ML → Rule → LLM)

See [ML_README.md](ML_README.md) for detailed ML documentation.

### Phase 1 - Phone Agent MVP ✅
- Twilio webhook integration
- Speech-to-Text using OpenAI Whisper
- Intent classification (LLM-based)
- Basic RAG (Retrieval-Augmented Generation)
- GPT-4o response generation
- Text-to-Speech via Twilio
- Comprehensive logging

### Phase 2 - RAG + Business Info ✅
- ChromaDB vector store
- Business data loading (menu, hours, pricing)
- Retrieval augmentation pipeline
- Multi-turn conversation state

### Phase 3 - Reservations ✅
- Reservation intent detection
- Calendar integration (JSON-based)
- Reservation rules ("table for 2", "tomorrow 7pm")
- SMS confirmation (placeholder)

### Phase 4 - Web Chat Widget ✅
- JavaScript chat widget
- HTML injection snippet
- WebSocket endpoint (structure)
- Real-time chat interface

### Phase 5 - Owner Dashboard (Structure)
- Login page
- Edit hours, menu, pricing
- View logs
- Update inventory availability
- Toggle settings

### Phase 6 - Stripe Subscription (Structure)
- Pricing tiers
- Stripe checkout links
- Webhook for subscription success
- Auto-create business profile

## 📁 Project Structure

```
ai-assistant/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── stt_tts.py             # Speech-to-Text & Text-to-Speech
│   ├── rag.py                 # RAG system with ChromaDB
│   ├── intents.py             # Intent classification
│   ├── call_flow.py           # Conversation flow management
│   ├── twilio_handler.py      # Twilio webhook handlers
│   ├── reservation_logic.py   # Reservation handling
│   ├── business_data.json     # Business data (menu, hours, etc.)
│   ├── utils/
│   │   └── logger.py          # Logging utility
│   ├── tests/
│   │   └── test_intents.py    # Intent classification tests
│   └── requirements.txt       # Python dependencies
├── dashboard/                 # Owner dashboard (structure)
│   ├── pages/
│   ├── components/
│   └── api/
├── widget/                    # Web chat widget
│   ├── widget.js             # Widget JavaScript
│   ├── widget.css            # Widget styles
│   └── index.html            # Widget demo
├── scripts/
│   └── seed_business_data.py # Seed business data to RAG
└── README.md
```

## 🛠️ Setup

### 1. Environment Variables

Create a `.env` file in the root directory:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Database
CHROMA_DB_PATH=./chroma_db

# Stripe
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key

# Application
API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
LOG_LEVEL=INFO
DEFAULT_BUSINESS_ID=restaurant_001
```

### 2. Install Dependencies

```bash
cd ai-assistant/backend
pip install -r requirements.txt
```

### 3. Seed Business Data

```bash
python scripts/seed_business_data.py
```

### 4. Run the Server

```bash
cd ai-assistant/backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or:

```bash
cd ai-assistant/backend
python main.py
```

## 📞 Twilio Configuration

1. Get a Twilio phone number
2. Configure webhook URLs in Twilio Console:
   - Voice URL: `https://your-domain.com/api/twilio/voice/incoming`
   - Status Callback: `https://your-domain.com/api/twilio/voice/status`

## 🌐 Web Widget Usage

Add the widget to any website:

```html
<script>
window.AIReceptionistConfig = {
    apiUrl: 'http://localhost:8000',
    businessId: 'restaurant_001'
};
</script>
<script src="http://localhost:8000/widget/widget.js"></script>
```

## 🔧 API Endpoints

### Phone (Twilio)
- `POST /api/twilio/voice/incoming` - Handle incoming calls
- `POST /api/twilio/voice/process` - Process voice input
- `POST /api/twilio/voice/status` - Call status updates

### Chat
- `POST /api/chat/message` - Send chat message (HTTP)
- `GET /api/chat/ws` - WebSocket endpoint

### Widget Assets
- `GET /widget/widget.js` - Widget JavaScript
- `GET /widget/widget.css` - Widget CSS

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## 🧪 Testing

Run intent classification tests:

```bash
cd ai-assistant/backend
pytest tests/test_intents.py -v
```

## 📝 Development Phases

- [x] Phase 1: Phone Agent MVP
- [x] Phase 2: RAG + Business Info
- [x] Phase 3: Reservations
- [x] Phase 4: Web Chat Widget (structure)
- [ ] Phase 5: Owner Dashboard (full implementation)
- [ ] Phase 6: Stripe Subscription (full implementation)

## 🔒 Security Notes

- Change CORS settings for production
- Use environment variables for all secrets
- Implement proper authentication for dashboard
- Validate all Twilio webhook requests
- Rate limit API endpoints

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

