#!/usr/bin/env python3
import sys, asyncio
from nicegui import ui, app
import logging

# Import necessary modules from the app package
from app import config
from app.ui import chat_page, config_page # Import the page modules

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_asyncio_exception(loop, context):
    """Custom exception handler to suppress ConnectionResetError."""
    exc = context.get('exception')
    if isinstance(exc, ConnectionResetError):
        return # Suppress ConnectionResetError
    loop.default_exception_handler(context)

async def startup_handler():
    """Set the custom exception handler after the event loop starts."""
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_asyncio_exception)
    logger.info("Custom asyncio exception handler set.")

# Register the startup handler
app.on_startup(startup_handler)

# Handle Ctrl+C in terminal to stop the app
import signal
signal.signal(signal.SIGINT, lambda sig, frame: app.shutdown())

def main():
    # Load configuration at startup
    cfg = config.load_config()
    logger.info("Application starting with loaded configuration.")

    # Apply enhanced color theme
    ui.colors(
        primary='#bd93f9',    # Purple
        secondary='#ff79c6',  # Pink
        accent='#8be9fd',     # Cyan
        positive='#50fa7b',   # Green
        negative='#ff5555',   # Red
        warning='#f1fa8c',    # Yellow
        info='#6272a4',       # Comment Blue
        dark='#282a36',       # Background
        light='#f8f8f2'       # Foreground
    )
    
    # Add global CSS for enhanced theme and better UX
    ui.add_head_html('''
    <style>
        /* Base styling */
        body {
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
            background-color: #1a1b26 !important;
            color: #f8f8f2 !important;
            transition: background-color 0.3s, color 0.3s;
        }
        
        /* Card styling */
        .ni-card {
            border-radius: 12px !important;
            overflow: hidden !important;
            transition: transform 0.2s, box-shadow 0.2s !important;
        }
        .ni-card:hover {
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Input styling */
        .ni-input {
            border-radius: 8px !important;
            background-color: #383a59 !important;
            color: #f8f8f2 !important;
            transition: all 0.2s !important;
        }
        .ni-input:focus {
            border-color: #bd93f9 !important;
            box-shadow: 0 0 0 2px rgba(189, 147, 249, 0.3) !important;
        }
        
        /* Button styling */
        .ni-button {
            border-radius: 8px !important;
            transition: all 0.2s !important;
        }
        .ni-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Drawer styling */
        .ni-drawer {
            background-color: #1e1f29 !important;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.3) !important;
        }
        .ni-drawer-item {
            border-radius: 8px !important;
            margin: 4px 0 !important;
            transition: all 0.2s !important;
        }
        .ni-drawer-item:hover {
            background-color: rgba(189, 147, 249, 0.1) !important;
            transform: translateX(3px);
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(40, 42, 54, 0.2);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb {
            background-color: rgba(98, 114, 164, 0.5);
            border-radius: 3px;
            transition: background-color 0.3s;
        }
        ::-webkit-scrollbar-thumb:hover {
            background-color: rgba(98, 114, 164, 0.8);
        }
        
        /* Tooltip styling */
        .ni-tooltip {
            background-color: #44475a !important;
            color: #f8f8f2 !important;
            border-radius: 6px !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Notification styling */
        .ni-notification {
            border-radius: 8px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Animation for page transitions */
        .page-transition {
            animation: fadeIn 0.3s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Add Font Awesome for better icons */
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
        
        /* Add Inter font for better typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Add Fira Code for code blocks */
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&display=swap');
    </style>
    ''')

    # Run the NiceGUI app with enhanced settings
    ui.run(
        title=cfg.get("bot_name", "NiceGUI Chat"),
        dark=True,  # Always use dark mode for Dracula theme
        reload=False,  # Disable auto-reload for native mode
        show=True,
        favicon='https://raw.githubusercontent.com/zauberzeug/nicegui/main/nicegui/static/favicon.ico',
        viewport='width=device-width, initial-scale=1, shrink-to-fit=no',
        # storage_secret='YOUR_SECRET_KEY_HERE'  # Recommended for production
    )

if __name__ in {"__main__", "__mp_main__"}:
    main()