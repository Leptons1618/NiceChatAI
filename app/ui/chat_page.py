from nicegui import ui, app, Client

from typing import List, Dict, Tuple
import logging
import asyncio  # Import asyncio for sleep
import os, json, datetime
import re  # for cleaning titles

# Use relative imports for modules within the app package
from .. import config
from .. import llm
from .. import db  # Import the new db module
from . import message_renderer  # Import the new message renderer

logger = logging.getLogger(__name__)

# Store chat history per client (remains client-specific)
chats: Dict[str, List[Tuple[str, str]]] = {}
# Store selected model per client (client-specific selection)
selected_models: Dict[str, str] = {}
session_titles: Dict[str, str] = {}
# Shared dictionary for saved conversations (now loaded from MongoDB)
saved_conversations: Dict[str, Dict] = {}

@ui.page('/')
async def chat_page(client: Client):
    client_id = client.id
    cfg = config.get_config()

    # Add consistent styling with config_page
    ui.add_head_html("""<style>
        /* Prevent body scrolling */
        body {
            overflow: hidden !important; 
        }

        /* Chat scroll area styling - Adjust height calculation */
        #chat-scroll { 
            /* Estimate header (~60px) + footer (~70px) + padding/margins (~10px) = ~140px */
            height: calc(100vh - 140px) !important; 
            overflow-y: auto !important; 
            scrollbar-width: none; /* Firefox */
            -ms-overflow-style: none; /* IE and Edge */
            border-radius: 16px !important;
            border: 1px solid rgba(148, 163, 184, 0.1) !important;
            background-color: #1e293b !important;
        }
        #chat-scroll::-webkit-scrollbar { 
            width: 0; /* Webkit browsers - Hide default */
            height: 0;
        }
        /* Optional: Show custom scrollbar on hover if desired */
        /*
        #chat-scroll:hover::-webkit-scrollbar { width: 6px; }
        #chat-scroll:hover::-webkit-scrollbar-thumb { background-color: rgba(98, 114, 164, 0.5); border-radius: 3px; }
        #chat-scroll:hover { scrollbar-width: thin; scrollbar-color: rgba(98, 114, 164, 0.5) transparent; } 
        */

        /* Chat bubble markdown styling - Enhanced for lists */
        .chat-bubble h1 { font-size:1em; margin:0.4em 0; }
        .chat-bubble h2 { font-size:0.95em; margin:0.35em 0; }
        .chat-bubble h3 { font-size:0.9em; margin:0.3em 0; }
        .chat-bubble p, .chat-bubble li { font-size:0.9em; line-height:1.4; }
        .chat-bubble p { margin:0.2em 0 !important; }
        .chat-bubble ul, .chat-bubble ol { margin-left:1em; margin-bottom:0.5em; }
        /* Enhanced list styling for better spacing and clarity */
        .chat-bubble ol { padding-left:1.5em !important; margin-top:0.5em !important; }
        .chat-bubble ul { padding-left:1.5em !important; margin-top:0.5em !important; }
        .chat-bubble li { margin-bottom:0.25em !important; }
        .chat-bubble ol > li { padding-left:0.3em !important; }
        .chat-bubble ul > li { padding-left:0.2em !important; }
        .chat-bubble code { background:#334155; color:#f8fafc; padding:2px 4px; border-radius:4px; font-family:'Fira Code', monospace; font-size:0.85em; user-select:text; }
        .chat-bubble pre { background:#334155; padding:12px; padding-top:30px; border-radius:12px; overflow-x:auto; font-family:'Fira Code', monospace; font-size:0.85em; margin:0.5em 0; position:relative; user-select:text; }
        .chat-bubble pre code { background:none; }
        
        /* User message styling */
        .user-message {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.2) !important;
        }
        
        /* Bot message styling */
        .bot-message {
            background-color: #1e293b !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Copy button styling */
        .copy-button { 
            position:absolute; 
            top:5px; 
            right:5px; 
            background:#475569; 
            color:#f8fafc; 
            border:none; 
            padding:3px 8px; 
            border-radius:6px; 
            cursor:pointer; 
            font-size:0.75em; 
            opacity:0.7; 
            transition:opacity 0.2s; 
        }
        .copy-button:hover { opacity:1; background:#6366f1; }
        .copy-button:active { background:#4f46e5; }
        
        /* Avatar styling */
        .avatar-img {
            border: 2px solid rgba(148, 163, 184, 0.2);
            transition: all 0.2s;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        .user-avatar {
            border-color: rgba(99, 102, 241, 0.5) !important;
        }
        .bot-avatar {
            border-color: rgba(6, 182, 212, 0.5) !important;
        }
        
        /* Input styling - matching config_page */
        .chat-input {
            border-radius: 12px !important;
            transition: all 0.2s !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
            background-color: #334155 !important;
        }
        .chat-input:focus {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
        }
        
        /* Button styling - matching config_page */
        .chat-button {
            transition: all 0.2s !important;
            border-radius: 12px !important;
            font-weight: 500 !important;
        }
        .chat-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Drawer styling - Allow vertical scroll ONLY if needed, hide default bar */
        .chat-drawer {
            background-color: #1e293b !important;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.3) !important;
            border-right: 1px solid rgba(148, 163, 184, 0.1) !important;
            overflow-y: auto; /* Allow scroll if content overflows */
            overflow-x: hidden; /* Prevent horizontal scroll */
            scrollbar-width: none; /* Firefox */
            -ms-overflow-style: none; /* IE and Edge */
        }
        .chat-drawer::-webkit-scrollbar {
             width: 0; /* Webkit browsers - Hide default */
             height: 0;
        }
        /* Ensure card inside drawer doesn't cause unexpected overflow */
        .chat-drawer > .ni-card {
             overflow: visible !important; /* Let drawer handle scroll */
             box-shadow: none !important;
        }
        
        /* Saved chat item styling */
        .saved-chat-item {
            border-radius: 12px !important;
            transition: all 0.2s !important;
            overflow: hidden !important;
        }
        .saved-chat-item:hover {
            background-color: rgba(99, 102, 241, 0.1) !important;
            transform: translateX(3px);
        }
        
        /* Header and footer styling */
        .chat-header, .chat-footer {
            background-color: rgba(15, 23, 42, 0.8) !important;
            backdrop-filter: blur(10px) !important;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
        }
        .chat-footer {
            border-top: 1px solid rgba(148, 163, 184, 0.1) !important;
            border-bottom: none !important;
        }
        
        /* Model selector styling */
        .model-selector {
            border-radius: 12px !important;
            background-color: #334155 !important;
            border: 1px solid rgba(148, 163, 184, 0.2) !important;
        }
    </style>""")
    
    ui.add_head_html("""<script>
        function copyCode(button) {
            const pre = button.parentElement;
            const code = pre.querySelector('code');
            if (navigator.clipboard && code) {
                navigator.clipboard.writeText(code.innerText).then(() => { button.textContent='Copied!'; setTimeout(()=>button.textContent='Copy',2000); });
            }
        }
        function addCopyButtons() {
            document.querySelectorAll('.chat-bubble pre').forEach(pre => {
                if (pre.querySelector('.copy-button')) return;
                const btn = document.createElement('button'); btn.className='copy-button'; btn.textContent='Copy'; btn.onclick=function(){copyCode(this);}; pre.appendChild(btn);
            });
        }
        // Wait for the DOM to be fully loaded before running scripts that access it
        document.addEventListener('DOMContentLoaded', () => {
            addCopyButtons(); // Initial call
            // Initialize the observer *after* the DOM is ready
            new MutationObserver((mutations) => { 
                mutations.forEach(m => m.addedNodes.forEach(node => { 
                    // Check if the added node is an element and contains or is a 'pre' tag
                    if (node.nodeType === 1 && (node.matches('pre') || node.querySelector('pre'))) {
                        addCopyButtons(); 
                    }
                })); 
            }).observe(document.body, { childList: true, subtree: true });
        });
    </script>
    <script>
      document.addEventListener('keydown', function(event) {
          if (event.ctrlKey && (event.key==='c' || event.key==='C')) { event.preventDefault(); window.close(); }
      });
    </script>""")

    # Initialize client state
    chats[client_id] = []
    load_saved_conversations()
    current_default_model = config.get_default_model() or ''
    selected_models[client_id] = current_default_model

    # Helper: reset to a new chat session
    def new_chat():
        session_titles[client_id] = ''
        # reset conversation with welcome message
        bot = cfg.get('bot_name', 'Bot')
        chats[client_id] = [(bot, f"Hi there! I'm {bot}. How can I help you today?")]
        chat_messages.refresh()
        # reset header title
        if title_label:
            title_label.set_text('New Conversation')
            title_label.update()

    # Helper: load a saved conversation
    def load_conversation(title: str):
        entry = saved_conversations.get(title, {})
        chats[client_id] = entry.get('messages', [])
        chat_messages.refresh()
        # set session title to this key
        session_titles[client_id] = title
        # display only the human title (strip timestamp, Title Case)
        display_title = format_display_title(title, max_len=70)  # Use longer title in header
        if title_label:
            title_label.set_text(display_title)
            title_label.update()

    # initialize per-session title (empty until first save)
    session_titles[client_id] = ''

    # Placeholder for header title label
    title_label = None

    # Handler: send user message and stream assistant response
    async def send(e=None):
        user_text = text.value.strip()
        if not user_text:
            return
        chats[client_id].append(('You', user_text))
        chat_messages.refresh()
        text.value = ''
        # Include summary if this conversation was previously saved
        last_title = list(saved_conversations.keys())[-1] if saved_conversations else None
        summary = saved_conversations.get(last_title, {}).get('summary', '') if last_title else ''
        system_prompt = summary + '\n\n' if summary else None
        
        bot_name = cfg.get('bot_name', 'Bot')
        chats[client_id].append((bot_name, ''))
        # Get the current message index for selective update
        current_msg_idx = len(chats[client_id]) - 1
        chat_messages.refresh()
        
        try:
            async for chunk in llm.generate_ollama_response(
                client_id,
                user_text,
                selected_models.get(client_id) or '',
                system_prompt,
            ):
                name, prev = chats[client_id][current_msg_idx]
                chats[client_id][current_msg_idx] = (name, prev + chunk)
                # Only refresh the specific message component being updated
                if current_msg_idx in message_components:
                    message_components[current_msg_idx].refresh()
                else:
                    # Fallback to full refresh if message component not found
                    chat_messages.refresh()
            # auto-save conversation after assistant response
            await save_current_conversation()
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {e}")
            chats[client_id][current_msg_idx] = (bot_name, "Error: Could not connect to Ollama service. Please ensure it's running.")
            if current_msg_idx in message_components:
                message_components[current_msg_idx].refresh()
            else:
                chat_messages.refresh()
            ui.notify("Failed to get response from Ollama service.", color='negative', position='top')

    # Define delete_conversation helper before drawer creation
    def delete_conversation(title):
        if title in saved_conversations:
            db.delete_conversation(title)
            del saved_conversations[title]
            # Use drawer_saved_list instead of saved_list 
            if drawer_saved_list:
                drawer_saved_list.refresh()
            ui.notify(f"Conversation deleted", color='info', position='top')
            # Reset to new chat if the current one was deleted
            if session_titles.get(client_id) == title:
                new_chat()
    
    # --- Navigation drawer with save/load conversations ---
    # Ensure the drawer itself handles scrolling, not necessarily the card inside
    left_drawer = ui.left_drawer(value=False).props("width=450").classes('chat-drawer')
    
    # Declare drawer_saved_list before using it
    drawer_saved_list = None
    
    with left_drawer:
        # Use nonlocal inside functions, not at this level
        # Removed the wrapping ui.card here, apply styles directly or to drawer items
        ui.label(f'{cfg.get("bot_name", "ChatBot")}').classes('text-2xl font-bold text-center py-4 px-4')
        ui.separator().classes('mb-4 opacity-20 mx-4')
            
        # new chat action with improved styling (apply padding/margin here)
        ui.button('New Chat', icon='add', on_click=new_chat) \
            .props('flat') \
            .classes('w-full text-left text-sm text-white hover:text-primary py-3 mb-3 chat-button mx-4')
        
        @ui.refreshable
        def render_saved_list():
            ui.label('Saved Chats').classes('text-xs text-center opacity-70 my-3 px-4')
            # sort by timestamp prefix descending
            # Apply margin/padding to the container or items directly
            with ui.column().classes('w-full px-4'): # Add padding to the column
                for key in sorted(saved_conversations.keys(), key=lambda t: t.split('_')[0], reverse=True):
                    display_title = format_display_title(key, max_len=40)  # Shorter title for drawer items
                    # Card for item styling, ensure it doesn't cause overflow itself
                    with ui.card().classes('w-full mb-2 p-0 saved-chat-item bg-transparent border-0 shadow-none'):
                        with ui.row().classes('w-full justify-between items-center'):
                            btn = ui.button(display_title, on_click=lambda e, t=key: load_conversation(t)) \
                                .props('no-caps text-left align=left flat') \
                                .classes('flex-grow text-left text-sm text-gray-200 hover:text-primary py-2')
                            # Add delete button
                            ui.button(icon='delete', on_click=lambda e, t=key: delete_conversation(t)) \
                                .props('flat round text-negative') \
                                .classes('text-xs opacity-50 hover:opacity-100')
        # Assign the drawer_saved_list reference inside the drawer
        # drawer_saved_list = render_saved_list
        drawer_saved_list = render_saved_list
        # Initial render of saved list
        drawer_saved_list()

    # Remove the old references to saved_list that were outside the drawer
    # saved_list = render_saved_list  # REMOVED
    # saved_list()  # REMOVED

    # Helper: save current conversation with summary (title is generated once)
    async def save_current_conversation():
        messages = chats[client_id]
        if not messages:
            ui.notify("No messages to save", color='warning', position='top')
            return
        # generate title only once per session
        if not session_titles[client_id]:
            raw_title = await generate_conversation_title(messages)
            # prefix with timestamp for uniqueness
            prefix = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            title = f"{prefix}_{raw_title}"
            session_titles[client_id] = title
        else:
            title = session_titles[client_id]
        summary = await summarize_conversation(messages)
        saved_conversations[title] = {'messages': messages, 'summary': summary}
        
        # Save to MongoDB instead of JSON file
        db.save_conversation(title, saved_conversations[title])
        
        # re-render saved list in drawer
        if drawer_saved_list:
            drawer_saved_list.refresh()
        # open drawer automatically to show the new title
        left_drawer.value = True
        left_drawer.update()
        # update header title
        if title_label:
            display_title = format_display_title(title, max_len=100)  # Use longer title in header
            title_label.set_text(display_title)
            title_label.update()

    # Placeholder for dropdown to be referenced by fetch helper
    model_selector = None

    # Handler: fetch models and update the dropdown
    async def fetch_models_and_update_ui():
        try:
            models = await llm.get_available_models()
            config.set_available_models_cache(models)
            if model_selector:
                model_selector.options = models
                if models and selected_models.get(client_id) not in models:
                    selected_models[client_id] = models[0]
                    model_selector.value = models[0]
                model_selector.update()
        except Exception as e:
            logger.error(f"Failed to fetch models from Ollama: {e}")
            ui.notify("Could not connect to Ollama service. Please ensure it's running.", color='negative', position='top')

    # --- Header ---
    # Note: The actual rendered height of header/footer might vary. 
    # Inspect element in browser dev tools to get precise heights if needed.
    with ui.header(elevated=True).classes('px-4 py-3 chat-header'): # Approx 50-60px height
        with ui.row().classes('w-full items-center justify-between'):
            # left: menu and app name
            with ui.row().classes('items-center'):
                ui.button(icon='menu', on_click=lambda: left_drawer.toggle()) \
                    .props('flat round') \
                    .classes('mr-2 text-light chat-button')
                ui.label(f'{cfg.get("bot_name", "ChatBot")}') \
                    .classes('text-lg font-semibold text-white')
            
            # center: session title
            with ui.row().classes('flex-1 justify-center'):
                # initial header title
                init_key = session_titles.get(client_id)
                init_title = format_display_title(init_key, max_len=100) if init_key else 'New Conversation'  # Longer title for header
                title_label = ui.label(init_title) \
                    .classes('text-base font-medium text-gray-300 truncate') \
                    .style('max-width:450px; white-space:nowrap; overflow:hidden;')  # Increased max width
            
            # right: model selector and actions
            with ui.row().classes('items-center'):
                model_selector = ui.select(
                    options=config.get_available_models_cache(),
                    value=selected_models.get(client_id),
                    on_change=lambda e: selected_models.update({client_id: e.value})
                ).props('outlined dense').classes('text-xs mr-2 model-selector')
                
                ui.button(icon='refresh', on_click=fetch_models_and_update_ui) \
                    .props('flat round') \
                    .classes('text-light ml-2 chat-button')
                ui.button(icon='settings', on_click=lambda: ui.navigate.to('/config')) \
                    .props('flat round') \
                    .classes('text-light ml-2 chat-button')
                ui.button(icon='exit_to_app', on_click=lambda: app.shutdown()) \
                    .props('flat round') \
                    .classes('text-light ml-2 chat-button')

    # Main chat container - Full size (not including the footer)
    with ui.column().classes('w-full px-4 py-3'): # This padding adds to the total height calculation
        # Scroll area with improved styling
        scroll_container = ui.scroll_area().props('id=chat-scroll').classes('w-full shadow-lg')
        # Use the scroll_container
        with scroll_container:
             # Dictionary to store message components for selective refreshing
             message_components = {}
             
             # Create a refreshable component for a single message
             def create_message_component(msg_idx):
                 @ui.refreshable
                 def message_content(idx=msg_idx):
                     if idx >= len(chats.get(client_id, [])):
                         return
                     name, message = chats.get(client_id, [])[idx]
                     with ui.card().classes(f'chat-bubble p-3 mb-2 shadow-md {"user-message" if name == "You" else "bot-message"} rounded-2xl max-w-[80%]'):
                         # Use the enhanced message renderer instead of direct ui.markdown
                         message_renderer.render_message(message)
                     # Run JavaScript to add copy buttons after content is updated
                     ui.run_javascript("addCopyButtons()")
                 return message_content
             
             @ui.refreshable
             def chat_messages() -> None:
                 bot_name = config.get_config().get("bot_name", "Bot")
                 with ui.column().classes('w-full p-4 space-y-4'):
                     # Render messages with custom bubbles and avatars
                     for idx, (name, message) in enumerate(chats.get(client_id, [])):
                         is_user = (name == 'You')
                         # Use different RoboHash sets for user and bot
                         avatar_id = 'User' if is_user else bot_name
                         robo_set = 'set4' if is_user else 'set2'
                         avatar_url = f'https://robohash.org/{avatar_id}?set={robo_set}'
                         # Row for message and avatar
                         with ui.row().classes(f"w-full {'justify-end' if is_user else 'justify-start'} items-start"):
                             # Bot avatar on left
                             if not is_user:
                                 ui.image(avatar_url).classes('w-10 h-10 rounded-full mr-3 avatar-img bot-avatar') # Larger avatar
                             
                             # Create a refreshable component for this message if it doesn't exist
                             if idx not in message_components:
                                 message_components[idx] = create_message_component(idx)
                             # Render the message content
                             message_components[idx]()
                             
                             # User avatar on right
                             if is_user:
                                 ui.image(avatar_url).classes('w-10 h-10 rounded-full ml-3 avatar-img user-avatar') # Larger avatar
                 
                 # Auto-scroll to bottom of scroll area after UI update
                 ui.timer(0.1, lambda: scroll_container.scroll_to(percent=1.0), once=True)
             
             # Initial rendering of chat messages
             chat_messages()
             ui.run_javascript("addCopyButtons()")

    # Input area - Footer as top-level element with improved styling
    with ui.footer().classes('px-4 py-4 chat-footer'): # Approx 60-70px height
        with ui.row().classes('w-full items-center max-w-6xl mx-auto'):
            with ui.input(placeholder='Type your message...') \
                    .classes('flex-grow rounded-full chat-input') \
                    .props('outlined dense') \
                    .on('keydown.enter', send) as text:
                pass
            
            ui.button('', icon='send', on_click=send) \
                .props('flat dense color=primary') \
                .classes('ml-3 text-xl rounded-full h-12 w-12 flex items-center justify-center chat-button')

    # --- Initial Setup ---
    await client.connected()
    text.run_method('focus')
    # fetch model list and populate dropdown on connect
    await fetch_models_and_update_ui()

# Utilities for loading/saving conversations from MongoDB
def load_saved_conversations():
    global saved_conversations
    try:
        saved_conversations = db.get_all_conversations()
    except Exception as e:
        logger.error(f"Failed to load saved conversations from MongoDB: {e}")
        saved_conversations = {}

# The following helpers remain the same as they don't interact with storage directly
async def generate_conversation_title(messages: List[Tuple[str, str]]) -> str:
    """Generate a short descriptive title for the conversation using the LLM."""
    # Take last up to 10 messages for context
    snippet = "\n".join(f"{name}: {msg}" for name, msg in messages[-10:])
    prompt = (
    "Generate a concise, relevant title (under 8 words, title case, no markdown) "
    "for the following conversation:\n\n"
    f"{snippet}"
    )
    title = ""
    model_name = config.get_default_model() or ''
    
    try:
        async for chunk in llm.generate_ollama_response(
            client_id="system",
            user_input=prompt,
            model_name=model_name,
            system_prompt=None
        ):
            title += chunk
    except Exception as e:
        logger.error(f"Failed to generate title via Ollama: {e}")
        return "Chat" # Default title on error
        
    title = title.strip().strip('"')
    # fallback to first user message if empty
    if not title:
        for name, msg in messages:
            if name.lower() == 'you' and msg.strip():
                title = msg.strip().split('.')[0][:50].strip()
                break
    return title

async def summarize_conversation(messages: List[Tuple[str, str]]) -> str:
    # Use the LLM to produce a concise summary of the chat
    convo_text = "\n".join(f"{name}: {msg}" for name, msg in messages)
    prompt = (
        "Summarize the following conversation between a user and an assistant in 3 concise sentences:\n\n" \
        + convo_text
    )
    summary = ""
    # stream the summary
    model_name = config.get_default_model() or ''
    
    try:
        async for chunk in llm.generate_ollama_response(
            client_id="system", user_input=prompt, model_name=model_name, system_prompt=None
        ):
            summary += chunk
    except Exception as e:
        logger.error(f"Failed to generate summary via Ollama: {e}")
        return "" # Return empty summary on error
        
    return summary.strip()

async def should_generate_title(new_message: str, messages: List[Tuple[str, str]]) -> bool:
    """Use the LLM to judge if this user message introduces the main topic for the chat title."""
    snippet = "\n".join(f"{name}: {msg}" for name, msg in messages[-10:])
    prompt = (
        f"Given the conversation context:\n{snippet}\n\n"
        f"And the new user message:\n'{new_message}'\n\n"
        "Answer 'Yes' if this should be used as the conversation title; otherwise answer 'No'."
    )
    response = ""
    model_name = config.get_default_model() or ''
    
    try:
        async for chunk in llm.generate_ollama_response(
            client_id="system", user_input=prompt, model_name=model_name, system_prompt=None
        ):
            response += chunk
    except Exception as e:
        logger.error(f"Failed to check title generation via Ollama: {e}")
        return False # Default to not generating title on error
        
    return response.strip().lower().startswith('yes')

# Helper: format display title by stripping special chars, preserving case, and truncating
def format_display_title(key: str, max_len: int = 30) -> str:
    raw = key.split('_', 1)[1] if '_' in key else key
    # remove leading non-alphanumeric chars
    raw = re.sub(r'^[^A-Za-z0-9]+', '', raw)
    # truncate longer titles with ellipsis
    return raw if len(raw) <= max_len else raw[:max_len-3] + '...'