#!/usr/bin/env python3
import sys, asyncio
from nicegui import ui, app
import logging
import platform  # Import platform to detect operating system

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

    # Apply modern color theme with a professional palette
    # Using the same color scheme as in config_page
    ui.colors(
        primary='#6366f1',    # Indigo
        secondary='#ec4899',  # Pink
        accent='#06b6d4',     # Cyan
        positive='#22c55e',   # Green
        negative='#ef4444',   # Red
        warning='#eab308',    # Yellow
        info='#3b82f6',       # Blue
        dark='#1e293b',       # Slate 800
        light='#f8fafc'       # Slate 50
    )
    
    # Add global CSS for enhanced theme and better UX
    ui.add_head_html('''
    <style>
        /* Base styling */
        body {
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
            background-color: #0f172a !important;
            color: #f8fafc !important;
            transition: background-color 0.3s, color 0.3s;
        }
        
        /* Card styling */
        .ni-card {
            border-radius: 16px !important;
            overflow: hidden !important;
            transition: transform 0.2s, box-shadow 0.2s !important;
            border: 1px solid rgba(148, 163, 184, 0.1) !important;
            background-color: #1e293b !important;
        }
        .ni-card:hover {
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Input styling */
        .ni-input {
            border-radius: 12px !important;
            background-color: #334155 !important;
            color: #f8fafc !important;
            transition: all 0.2s !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
        }
        .ni-input:focus {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
        }
        
        /* Button styling */
        .ni-button {
            border-radius: 12px !important;
            transition: all 0.2s !important;
            font-weight: 500 !important;
        }
        .ni-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* Drawer styling */
        .ni-drawer {
            background-color: #1e293b !important;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.3) !important;
            border-right: 1px solid rgba(148, 163, 184, 0.1) !important;
        }
        .ni-drawer-item {
            border-radius: 12px !important;
            margin: 4px 8px !important;
            transition: all 0.2s !important;
        }
        .ni-drawer-item:hover {
            background-color: rgba(99, 102, 241, 0.1) !important;
            transform: translateX(3px);
        }
        
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.2);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb {
            background-color: rgba(99, 102, 241, 0.5);
            border-radius: 3px;
            transition: background-color 0.3s;
        }
        ::-webkit-scrollbar-thumb:hover {
            background-color: rgba(99, 102, 241, 0.8);
        }
        
        /* Tooltip styling */
        .ni-tooltip {
            background-color: #334155 !important;
            color: #f8fafc !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Notification styling */
        .ni-notification {
            border-radius: 12px !important;
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
        
        /* Header styling */
        .ni-header {
            background-color: rgba(15, 23, 42, 0.8) !important;
            backdrop-filter: blur(10px) !important;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
        }
        
        /* Footer styling */
        .ni-footer {
            background-color: rgba(15, 23, 42, 0.8) !important;
            backdrop-filter: blur(10px) !important;
            border-top: 1px solid rgba(148, 163, 184, 0.1) !important;
        }
        
        /* Tab styling */
        .ni-tab {
            border-radius: 12px 12px 0 0 !important;
            transition: all 0.2s !important;
        }
        .ni-tab--selected {
            background-color: rgba(99, 102, 241, 0.1) !important;
            border-bottom: 2px solid #6366f1 !important;
        }
        
        /* Switch styling */
        .ni-switch {
            transition: all 0.2s !important;
        }
        
        /* Add Font Awesome for better icons */
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
        
        /* Add Inter font for better typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Add Fira Code for code blocks */
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&display=swap');
    </style>
    ''')

    # Determine if we should use native mode based on the OS
    is_windows = platform.system() == 'Windows'
    
    # Run the NiceGUI app with enhanced settings
    ui.run(
        title=cfg.get("bot_name", "NiceGUI Chat"),
        dark=True,  # Always use dark mode for modern theme
        native=is_windows,  # Use native mode only on Windows
        fullscreen=True,  # Fullscreen mode for immersive experience
        reload=False,  # Disable auto-reload for native mode
        show=True,
        favicon='https://raw.githubusercontent.com/zauberzeug/nicegui/main/nicegui/static/favicon.ico',
        viewport='width=device-width, initial-scale=1, shrink-to-fit=no',
        # storage_secret='YOUR_SECRET_KEY_HERE'  # Recommended for production
    )

if __name__ in {"__main__", "__mp_main__"}:
    main()