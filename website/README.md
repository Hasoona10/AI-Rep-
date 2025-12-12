# Cedar Garden Lebanese Kitchen - Website

A modern, aesthetic website for Cedar Garden Lebanese Kitchen with an integrated AI chatbot.

## Features

- **Modern Design**: Clean, professional layout with Lebanese-inspired color palette
- **Responsive**: Works beautifully on desktop, tablet, and mobile devices
- **AI Chatbot**: Integrated chat widget powered by the AI Receptionist system
- **Menu Preview**: Showcase of signature dishes
- **Contact Information**: Hours, location, and contact details
- **Smooth Animations**: Elegant transitions and hover effects

## Color Palette

- **Primary Green**: `#2D5016` - Represents Lebanese cedar trees
- **Accent Gold**: `#C9A961` - Warm, inviting gold
- **Warm Beige**: `#F5E6D3` - Soft background tones
- **Deep Brown**: `#5C3A1F` - Rich, earthy brown

## How to View

1. Make sure the FastAPI server is running:
   ```bash
   cd ai-assistant/backend
   python -m uvicorn main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Chat Widget

The chatbot is automatically integrated and appears in the bottom-right corner. It uses the AI Receptionist system to:
- Answer questions about menu items
- Provide hours and location information
- Help with reservations
- Process orders
- Answer FAQs

## Customization

To customize the website:
- Edit `index.html` for content changes
- Edit `styles.css` for design changes
- Update colors in the `:root` CSS variables

## Files

- `index.html` - Main website HTML
- `styles.css` - All styling and design
- `README.md` - This file

