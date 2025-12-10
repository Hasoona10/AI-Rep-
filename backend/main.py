"""
FastAPI main application for AI Receptionist.

DEMO SECTION: Technical Architecture & API Endpoints
This is the main FastAPI application! It sets up all the routes:
- Phone call endpoints (/api/twilio/voice/*)
- Web chat endpoints (/api/chat/*)
- Owner dashboard (/owner/orders)
- Kitchen view (/kitchen/orders)
- Widget assets (/widget/*)

This is the entry point for the entire system.
"""
import os
from pathlib import Path
from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from dotenv import load_dotenv
import json

from .utils.logger import setup_logger, logger
from .twilio_handler import handle_incoming_call, handle_voice_input, handle_call_status
from .rag import RAGSystem, get_rag_system
from .reservation_logic import ReservationSystem, get_reservation_system
from .call_flow import ORDERS_LOG_PATH

# Load environment variables
load_dotenv()

# Initialize FastAPI app
# DEMO: This creates the FastAPI application - it's a modern Python web framework
# that's super fast and has automatic API documentation
app = FastAPI(
    title="AI Receptionist API",
    description="Multi-channel AI receptionist for local businesses",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting AI Receptionist API...")
    
    # Load business data and initialize RAG
    business_id = os.getenv("DEFAULT_BUSINESS_ID", "restaurant_001")
    business_data_path = Path(__file__).parent / "business_data.json"
    
    if business_data_path.exists():
        # Use the new chunking and seeding system
        try:
            from .rag import seed_vectordb
            
            # Check if vector DB is already seeded (has documents)
            rag = get_rag_system(business_id)
            collection_count = rag.collection.count()
            
            if collection_count == 0:
                logger.info("Vector database is empty, seeding from business_data.json...")
                try:
                    seed_vectordb(business_data_path, business_id, clear_existing=False)
                except Exception as e:
                    logger.warning(f"Could not seed vector database (may be quota issue): {str(e)}")
                    logger.info("Server will continue without RAG seeding - phone calls will still work")
            else:
                logger.info(f"Vector database already seeded ({collection_count} documents)")
                # Optionally re-seed if data has changed (uncomment if needed)
                # seed_vectordb(business_data_path, business_id, clear_existing=True)
        
        except Exception as e:
            logger.warning(f"Error seeding RAG with new system, falling back to old method: {str(e)}")
            # Fallback to old method
            with open(business_data_path, 'r') as f:
                business_data = json.load(f)
            
            # Initialize RAG system
            rag = get_rag_system(business_id)
            
            # Convert business data to documents for RAG (old method)
            documents = []
            # Check if business_data is a dict with business_id key (old format) or direct dict (new format)
            if business_id in business_data:
                biz = business_data[business_id]
            else:
                biz = business_data  # New format
            
            # Hours document
            hours = biz.get("hours", {})
            if hours:
                if isinstance(list(hours.values())[0], dict):
                    # Old format: {"monday": {"open": "11:00", "close": "22:00"}}
                    hours_text = "Business Hours:\n"
                    for day, times in hours.items():
                        hours_text += f"{day.capitalize()}: {times.get('open')} - {times.get('close')}\n"
                else:
                    # New format: {"monday": "11:00 am – 9:00 pm"}
                    hours_text = "Business Hours:\n"
                    for day, time in hours.items():
                        hours_text += f"{day.capitalize()}: {time}\n"
                documents.append({"text": hours_text, "metadata": {"type": "hours"}})
            
            # Menu document
            menu_sections = biz.get("menu_sections", biz.get("menu", {}))
            if menu_sections:
                menu_text = "Menu:\n"
                if isinstance(menu_sections, list):
                    # New format: list of menu sections
                    for section in menu_sections:
                        menu_text += f"\n{section.get('name', '')}:\n"
                        for item in section.get("items", []):
                            price = item.get("price", "")
                            if isinstance(price, (int, float)):
                                price = f"${price:.2f}"
                            menu_text += f"- {item.get('name')}: {price} - {item.get('description')}\n"
                else:
                    # Old format: dict of categories
                    for category, items in menu_sections.items():
                        menu_text += f"\n{category.capitalize()}:\n"
                        for item in items:
                            menu_text += f"- {item.get('name')}: {item.get('price')} - {item.get('description')}\n"
                documents.append({"text": menu_text, "metadata": {"type": "menu"}})
            
            # Address document
            address = biz.get("address", {})
            if isinstance(address, dict):
                addr = address
                address_text = f"Address: {addr.get('street', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}. Phone: {addr.get('phone', '')}"
            else:
                address_text = f"Address: {address}"
            documents.append({"text": address_text, "metadata": {"type": "contact"}})
            
            # Description
            desc_text = biz.get("description", "")
            if desc_text:
                documents.append({"text": desc_text, "metadata": {"type": "description"}})
            
            # Add documents to RAG
            if documents:
                try:
                    rag.add_documents(documents)
                    logger.info(f"Initialized RAG with {len(documents)} documents for business {business_id}")
                except Exception as e:
                    logger.warning(f"Could not add documents to RAG (may be quota issue): {str(e)}")
                    logger.info("Server will continue - phone calls will still work with basic responses")
        
        # Initialize reservation system
        get_reservation_system(business_id)
        logger.info(f"Initialized reservation system for business {business_id}")
    else:
        logger.warning(f"Business data file not found: {business_data_path}")
        logger.info("  → Run 'python scripts/seed_data.py' to seed the database")
    
    logger.info("AI Receptionist API started successfully")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Receptionist API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/owner/orders", response_class=HTMLResponse)
async def owner_orders():
    """
    DEMO SECTION: Owner Dashboard - Order Management
    
    This is the owner dashboard! Restaurant owners can view all phone orders here.
    It shows:
    - Timestamp of each call
    - What the customer said
    - Structured order items (parsed from natural language)
    - Order totals
    - Full conversation transcripts
    
    The data comes from orders_log.json which gets updated every time someone places an order.
    This is super useful for owners to see what's coming in and review orders.
    """
    orders = []
    if ORDERS_LOG_PATH.exists():
        try:
            with ORDERS_LOG_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                orders = data
        except Exception as e:
            logger.error(f"Error reading orders log: {str(e)}")

    # Build HTML table with POS-style order details when available
    rows = []
    for o in reversed(orders):  # newest first
        ts = o.get("timestamp", "")
        call_sid = o.get("call_sid", "")
        intent = o.get("intent", "")
        customer_text = o.get("customer_text", "")
        ai_response = o.get("ai_response", "")
        order_items = o.get("order_items", [])
        order_total = o.get("order_total")

        # Build items summary
        if order_items:
            line_parts = []
            for item in order_items:
                qty = item.get("quantity", 1)
                name = item.get("name", "item")
                line_price = item.get("total_price")
                if line_price is not None:
                    line_parts.append(f"{qty} x {name} (${line_price:0.2f})")
                else:
                    line_parts.append(f"{qty} x {name}")
            items_html = "<br>".join(line_parts)
        else:
            items_html = "<em>No structured items</em>"

        if order_total is not None:
            total_html = f"${order_total:0.2f}"
        else:
            total_html = "<em>N/A</em>"

        rows.append(
            f"<tr>"
            f"<td>{ts}</td>"
            f"<td>{call_sid}</td>"
            f"<td>{intent}</td>"
            f"<td>{customer_text}</td>"
            f"<td>{items_html}</td>"
            f"<td>{total_html}</td>"
            f"<td>{ai_response}</td>"
            f"</tr>"
        )

    table_body = "\n".join(rows) if rows else (
        "<tr><td colspan='7' style='text-align:center;'>No orders logged yet.</td></tr>"
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Cedar Garden – Phone Order Log</title>
        <style>
            body {{
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                margin: 24px;
                background: #fafafa;
                color: #222;
            }}
            h1 {{
                margin-bottom: 8px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                background: #fff;
                box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            }}
            th, td {{
                border: 1px solid #e5e5e5;
                padding: 8px 10px;
                vertical-align: top;
            }}
            th {{
                background: #f3f4f6;
                text-align: left;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }}
            td {{
                font-size: 14px;
            }}
            .meta {{
                margin-bottom: 16px;
                font-size: 13px;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <h1>Cedar Garden – Phone Orders</h1>
        <div class="meta">
            This page shows calls where the AI agent detected order-like language and, when possible,
            captured a structured order (items + total) for the owner to review.
        </div>
        <table>
            <thead>
                <tr>
                    <th>Time (UTC)</th>
                    <th>Call SID</th>
                    <th>Intent</th>
                    <th>Customer Said</th>
                    <th>Order Items</th>
                    <th>Order Total</th>
                    <th>AI Response</th>
                </tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


@app.get("/kitchen/orders", response_class=HTMLResponse)
async def kitchen_orders():
    """
    DEMO SECTION: Kitchen View - Order Display
    
    This is the kitchen view! It's designed to be displayed on a tablet in the kitchen.
    It shows:
    - Only active orders (with structured items)
    - Large, readable text (dark theme for easy viewing)
    - Item quantities and line totals
    - Pickup time estimates
    
    The design is minimal and focused - kitchen staff just need to see what to make,
    not full conversation transcripts. It automatically updates when new orders come in.
    """
    orders = []
    if ORDERS_LOG_PATH.exists():
        try:
            with ORDERS_LOG_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                orders = data
        except Exception as e:
            logger.error(f"Error reading orders log for kitchen view: {str(e)}")

    # Keep only orders that have structured items, newest first
    structured = [o for o in reversed(orders) if o.get("order_items")]

    # Limit to last 10 for readability
    structured = structured[:10]

    if not structured:
        cards_html = "<p>No active phone orders yet.</p>"
    else:
        cards = []
        for o in structured:
            ts = o.get("timestamp", "")
            order_items = o.get("order_items", [])
            order_total = o.get("order_total")
            kitchen_ticket = o.get("kitchen_ticket")

            # Prefer finalized kitchen ticket snapshot when available
            if kitchen_ticket:
                items = kitchen_ticket.get("items", [])
                note = kitchen_ticket.get("note", "Pickup in ~25–30 minutes")
                total = kitchen_ticket.get("total", order_total)
            else:
                items = [
                    {
                        "name": i.get("name", "item"),
                        "quantity": i.get("quantity", 1),
                        "line_total": i.get("total_price"),
                    }
                    for i in order_items
                ]
                note = "Pickup in ~25–30 minutes"
                total = order_total

            # Build item lines
            lines = []
            for item in items:
                qty = item.get("quantity", 1)
                name = item.get("name", "item")
                line_total = item.get("line_total")
                if line_total is not None:
                    lines.append(f"{qty} × {name}  —  ${line_total:0.2f}")
                else:
                    lines.append(f"{qty} × {name}")
            items_html = "<br>".join(lines)

            if total is not None:
                total_html = f"${float(total):0.2f}"
            else:
                total_html = "N/A"

            card = f"""
            <div class="ticket">
                <div class="ticket-header">
                    <span class="ticket-label">PHONE ORDER</span>
                    <span class="ticket-time">{ts}</span>
                </div>
                <div class="ticket-body">
                    <div class="ticket-items">
                        {items_html}
                    </div>
                    <div class="ticket-total">
                        Total (est): <strong>{total_html}</strong>
                    </div>
                    <div class="ticket-note">
                        {note}
                    </div>
                </div>
            </div>
            """
            cards.append(card)

        cards_html = "\n".join(cards)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Cedar Garden – Kitchen Orders</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                margin: 16px;
                background: #111827;
                color: #f9fafb;
            }}
            h1 {{
                margin: 0 0 8px 0;
                font-size: 24px;
            }}
            .subtitle {{
                margin: 0 0 16px 0;
                font-size: 14px;
                color: #9ca3af;
            }}
            .tickets {{
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            .ticket {{
                background: #1f2937;
                border-radius: 8px;
                padding: 12px 14px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.6);
            }}
            .ticket-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 6px;
                font-size: 12px;
                color: #9ca3af;
            }}
            .ticket-label {{
                font-weight: 600;
                letter-spacing: 0.08em;
            }}
            .ticket-time {{
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            }}
            .ticket-body {{
                display: flex;
                flex-direction: column;
                gap: 6px;
            }}
            .ticket-items {{
                font-size: 18px;
                line-height: 1.4;
            }}
            .ticket-total {{
                margin-top: 4px;
                font-size: 16px;
            }}
            .ticket-note {{
                margin-top: 2px;
                font-size: 13px;
                color: #9ca3af;
            }}
        </style>
    </head>
    <body>
        <h1>Kitchen – Phone Orders</h1>
        <div class="subtitle">
            Latest AI-captured phone orders. Keep this page open on a tablet near the line.
        </div>
        <div class="tickets">
            {cards_html}
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


# ============================================================================
# DEMO SECTION: Phone Call System - API Endpoints
# ============================================================================
# These endpoints handle incoming phone calls from Twilio
@app.post("/api/twilio/voice/incoming")
async def twilio_incoming(request: Request):
    """
    Handle incoming Twilio calls.
    
    DEMO: This endpoint is called when someone calls the restaurant number.
    Twilio sends a webhook here, and we respond with TwiML to start the conversation.
    """
    return await handle_incoming_call(request)


@app.post("/api/twilio/voice/process")
async def twilio_process(request: Request):
    """
    Process voice input from Twilio.
    
    DEMO: This processes what the customer said! It takes the speech-to-text result,
    runs it through the AI system, and returns a response that Twilio converts to speech.
    """
    return await handle_voice_input(request)


@app.post("/api/twilio/voice/status")
async def twilio_status(request: Request):
    """
    Handle Twilio call status updates.
    
    This is called when a call ends - we clean up the conversation state.
    """
    return await handle_call_status(request)


# ============================================================================
# DEMO SECTION: Web Chat Widget - API Endpoints
# ============================================================================
@app.post("/api/chat/message")
async def chat_message(request: Request):
    """
    Handle chat message via HTTP (fallback).
    
    DEMO: This handles chat messages sent via HTTP (non-WebSocket).
    The web chat widget can use this as a fallback if WebSocket isn't available.
    It uses the same process_customer_message function as phone calls!
    """
    try:
        from .call_flow import process_customer_message
        data = await request.json()
        text = data.get("text", "")
        business_id = data.get("business_id", "restaurant_001")
        
        # Use a session ID for web chat (different from call SID)
        session_id = request.headers.get("X-Session-ID", "web_session_default")
        
        response = await process_customer_message(text, session_id, business_id)
        
        return JSONResponse({"response": response})
        
    except Exception as e:
        logger.error(f"Error handling chat message: {str(e)}")
        return JSONResponse({"error": "Internal server error"}, status_code=500)


@app.websocket("/api/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    
    DEMO: This is the WebSocket endpoint for the chat widget! It maintains a persistent
    connection so messages can be sent back and forth in real-time. Much better than
    polling HTTP requests.
    """
    from .websocket_handler import websocket_chat_endpoint
    import uuid
    
    # Generate session ID
    session_id = f"ws_{uuid.uuid4().hex[:12]}"
    
    # Get business_id from query params or default
    business_id = "restaurant_001"
    
    await websocket_chat_endpoint(websocket, session_id, business_id)


# ============================================================================
# DEMO SECTION: Web Chat Widget - Static Assets
# ============================================================================
# These endpoints serve the widget files that websites can embed
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/widget/widget.js")
async def serve_widget_js():
    """
    Serve widget JavaScript.
    
    DEMO: This serves the JavaScript file for the chat widget. Websites can include
    this script tag to add the chat widget to their page.
    """
    widget_path = Path(__file__).parent.parent / "widget" / "widget.js"
    return FileResponse(widget_path)


@app.get("/widget/widget.css")
async def serve_widget_css():
    """
    Serve widget CSS.
    
    DEMO: This serves the CSS styling for the chat widget.
    """
    css_path = Path(__file__).parent.parent / "widget" / "widget.css"
    return FileResponse(css_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

