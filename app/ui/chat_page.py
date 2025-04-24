from nicegui import Client, ui, app

from typing import List, Dict, Tuple
import logging
import asyncio  # Import asyncio for sleep
import os, json, datetime
import re  # for cleaning titles

# Use relative imports for modules within the app package
from .. import config
from .. import llm

logger = logging.getLogger(__name__)

# Store chat history per client (remains client-specific)
chats: Dict[str, List[Tuple[str, str]]] = {}
# Store selected model per client (client-specific selection)
selected_models: Dict[str, str] = {}
session_titles: Dict[str, str] = {}

@ui.page('/')
async def chat_page(client: Client):
    client_id = client.id
    cfg = config.get_config()

    # Restore CSS styling and JS scripts for scrollbars, chat bubbles, and copy/exit behavior
    ui.add_head_html("""<style>
        /* Chat scroll area styling */
        #chat-scroll { height: calc(100vh - 190px) !important; overflow-y: auto !important; scrollbar-width: none; }
        #chat-scroll::-webkit-scrollbar { width: 0; }
        #chat-scroll:hover { scrollbar-width: thin; }
        #chat-scroll:hover::-webkit-scrollbar { width: 6px; }
        /* Chat bubble markdown styling */
        .chat-bubble h1 { font-size:1em; margin:0.4em 0; }
        .chat-bubble h2 { font-size:0.95em; margin:0.35em 0; }
        .chat-bubble h3 { font-size:0.9em; margin:0.3em 0; }
        .chat-bubble p, .chat-bubble li { font-size:0.9em; line-height:1.4; }
        .chat-bubble p { margin:0.2em 0 !important; }
        .chat-bubble ul, .chat-bubble ol { margin-left:1em; margin-bottom:0.5em; }
        .chat-bubble code { background:#2e2e2e; color:#f8f8f2; padding:2px 4px; border-radius:4px; font-family:monospace; font-size:0.85em; user-select:text; }
        .chat-bubble pre { background:#2e2e2e; padding:12px; padding-top:30px; border-radius:8px; overflow-x:auto; font-family:monospace; font-size:0.85em; margin:0.5em 0; position:relative; user-select:text; }
        .chat-bubble pre code { background:none; }
        /* Copy button styling */
        .copy-button { position:absolute; top:5px; right:5px; background:#44475a; color:#f8f8f2; border:none; padding:3px 8px; border-radius:4px; cursor:pointer; font-size:0.75em; opacity:0.7; transition:opacity 0.2s; }
        .copy-button:hover { opacity:1; }
        .copy-button:active { background:#6272a4; }
    </style>""")
    ui.add_head_html("""<style>
    /* Modern form styling from config_page */
    .config-card {
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
        overflow: hidden !important;
        border: none !important;
    }
    .config-card:hover {
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
    }
    .config-input {
        border-radius: 8px !important;
        transition: all 0.2s !important;
        border: 1px solid #44475a !important;
    }
    .config-input:focus {
        border-color: #bd93f9 !important;
        box-shadow: 0 0 0 2px rgba(189, 147, 249, 0.3) !important;
    }
    .config-button {
        transition: all 0.2s !important;
        border-radius: 8px !important;
    }
    .config-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }
    .config-section {
        border-left: 3px solid #bd93f9 !important;
        padding-left: 16px !important;
        margin-bottom: 24px !important;
    }
    .config-label {
        font-weight: 500 !important;
        margin-bottom: 4px !important;
        color: #f8f8f2 !important;
    }
    .help-text {
        font-size: 0.8rem !important;
        opacity: 0.7 !important;
        margin-top: 4px !important;
    }
</style>""")
    ui.add_head_html("""
<script>
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
    document.addEventListener('DOMContentLoaded', addCopyButtons);
    new MutationObserver((mutations) => { mutations.forEach(m=>m.addedNodes.forEach(node=>{ if(node.nodeType===1&&(node.matches('pre')||node.querySelector('pre'))) addCopyButtons(); })); }).observe(document.body,{childList:true,subtree:true});
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
        # ui.notify(f"Loaded '{display_title}'", timeout=2000, position='top')

    # initialize per-session title (empty until first save)
    session_titles[client_id] = ''

    # Placeholder for header title label
    title_label = None

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
        saved_conversations[title] = { 'messages': messages, 'summary': summary }
        save_saved_conversations()
        # re-render saved list in drawer
        saved_list.refresh()
        # open drawer automatically to show the new title
        left_drawer.value = True
        left_drawer.update()
        # update header title
        if title_label:
            title_label.set_text(title)
            title_label.update()
        # ui.notify(f"Saved '{title}'", timeout=2000, position='top')

    # Placeholder for dropdown to be referenced by fetch helper
    model_selector = None

    # Handler: fetch models and update the dropdown
    async def fetch_models_and_update_ui():
        models = await llm.get_available_models()
        config.set_available_models_cache(models)
        if model_selector:
            model_selector.options = models
            if models and selected_models.get(client_id) not in models:
                selected_models[client_id] = models[0]
                model_selector.value = models[0]
            model_selector.update()

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
        chats[client_id].append((cfg.get('bot_name', 'Bot'), ''))
        chat_messages.refresh()
        async for chunk in llm.generate_ollama_response(
            client_id,
            user_text,
            selected_models.get(client_id) or '',
            system_prompt,
        ):
            name, prev = chats[client_id][-1]
            chats[client_id][-1] = (name, prev + chunk)
            chat_messages.refresh()
        # auto-save conversation after assistant response
        await save_current_conversation()

    # --- Navigation drawer with save/load conversations ---
    left_drawer = ui.left_drawer(value=False).props("width=350").classes('bg-dark')
    with left_drawer:
        ui.label(f'{cfg.get("bot_name", "ChatBot")}').classes('text-2xl font-bold text-center py-4')
        ui.separator().classes('mb-2')
        # new chat action
        ui.button('New Chat', icon='add', on_click=new_chat).props('flat dense').classes('w-full text-left text-sm text-white hover:text-accent py-1 mb-2 config-button')
        @ui.refreshable
        def render_saved_list():
            ui.label('Saved Chats').classes('text-xs text-center opacity-50')
            # sort by timestamp prefix descending
            for key in sorted(saved_conversations.keys(), key=lambda t: t.split('_')[0], reverse=False):
                display_title = format_display_title(key, max_len=40)  # Shorter title for drawer items
                btn = ui.button(display_title, on_click=lambda e, t=key: load_conversation(t)).props('no-caps text-left align=left')
                btn.props('flat')
                btn.classes('w-full text-left text-sm text-gray-200 hover:text-accent py-1')
        # keep a reference to the refreshable function
        saved_list = render_saved_list
        # initial render
        saved_list()

        ui.space()
        ui.label('Powered by NiceGUI & Ollama').classes('text-xs text-center opacity-50')

    # --- Header ---
    with ui.header(elevated=True).classes('bg-dark px-4'):
        with ui.row().classes('w-full items-center justify-between'):
            # left: menu and app name
            with ui.row().classes('items-center'):
                ui.button(icon='menu', on_click=lambda: left_drawer.toggle()).props('flat round').classes('mr-2')
                ui.label(f'{cfg.get("bot_name", "ChatBot")}').classes('text-lg font-semibold text-white')
            # center: session title
            with ui.row().classes('flex-1 justify-center'):
                # initial header title
                init_key = session_titles.get(client_id)
                init_title = format_display_title(init_key, max_len=70) if init_key else 'New Conversation'  # Longer title for header
                title_label = ui.label(init_title)
                title_label.classes('text-base font-medium text-gray-300 truncate')
                title_label.style('max-width:350px; white-space:nowrap; overflow:hidden;')  # Increased max width
            # right: model selector and actions
            with ui.row().classes('items-center'):
                model_selector = ui.select(
                    options=config.get_available_models_cache(),
                    value=selected_models.get(client_id),
                    on_change=lambda e: selected_models.update({client_id: e.value})
                ).props('outlined dense').classes('text-xs mr-2')
                ui.button(icon='refresh', on_click=fetch_models_and_update_ui).props('flat round').classes('text-light ml-2')
                ui.button(icon='settings', on_click=lambda: ui.navigate.to('/config')).props('flat round').classes('text-light ml-2')
                ui.button(icon='exit_to_app', on_click=lambda: app.shutdown()).props('flat round').classes('text-light ml-2')

    # Main chat container - Full size (not including the footer)
    with ui.column().classes('w-full px-2 py-2'):
        # Scroll area now uses CSS height
        scroll_container = ui.scroll_area().props('id=chat-scroll').classes('w-full bg-gray-900 shadow-lg')
        # Use the scroll_container
        with scroll_container:
             @ui.refreshable
             def chat_messages() -> None:
                 bot_name = config.get_config().get("bot_name", "Bot")
                 with ui.column().classes('w-full p-4 space-y-4'):
                     # Render messages with custom bubbles and avatars
                     for name, message in chats.get(client_id, []):
                         is_user = (name == 'You')
                         # Use different RoboHash sets for user and bot
                         avatar_id = 'User' if is_user else bot_name
                         robo_set = 'set4' if is_user else 'set2'
                         avatar_url = f'https://robohash.org/{avatar_id}?set={robo_set}'
                         # Row for message and avatar
                         with ui.row().classes(f"w-full {'justify-end' if is_user else 'justify-start'} items-start"):
                             # Bot avatar on left
                             if not is_user:
                                 ui.image(avatar_url).classes('w-9 h-9 rounded-full mr-2') # Larger avatar
                             # Message bubble
                             with ui.card().classes('chat-bubble p-2 mb-2 shadow-md config-card'):
                                 ui.markdown(message)
                             # User avatar on right
                             if is_user:
                                 ui.image(avatar_url).classes('w-9 h-9 rounded-full ml-2') # Larger avatar
                 # Auto-scroll to bottom of scroll area after UI update
                 ui.timer(0.1, lambda: scroll_container.scroll_to(percent=1.0), once=True)
                 ui.run_javascript("addCopyButtons()")
             # Initial rendering of chat messages
             chat_messages()
             ui.run_javascript("addCopyButtons()")

    # Input area - Footer as top-level element (moved outside the column)
    with ui.footer().classes('bg-dark px-4 py-3 shadow-lg'):
        with ui.row().classes('w-full items-center max-w-6xl mx-auto'):
            with ui.input(placeholder='Type your message...').classes('flex-grow rounded-full config-input').props('outlined dense').on('keydown.enter', send) as text:
                pass
            ui.button('', icon='send', on_click=send).props('flat dense color=accent').classes('ml-2 text-xl config-button')  # Icon-only send button

    # --- Initial Setup ---
    await client.connected()
    text.run_method('focus')
    # fetch model list and populate dropdown on connect
    await fetch_models_and_update_ui()

# Utilities for saving/loading conversations
SAVED_CONV_FILE = os.path.join(os.path.dirname(__file__), '..', 'saved_conversations.json')
saved_conversations = {}

def load_saved_conversations():
    global saved_conversations
    try:
        with open(SAVED_CONV_FILE) as f:
            saved_conversations = json.load(f)
    except FileNotFoundError:
        saved_conversations = {}
    except Exception as e:
        logger.error(f"Failed to load saved conversations: {e}")
        saved_conversations = {}

def save_saved_conversations():
    try:
        with open(SAVED_CONV_FILE, 'w') as f:
            json.dump(saved_conversations, f)
    except Exception as e:
        logger.error(f"Failed to save conversations: {e}")

async def generate_conversation_title(messages: List[Tuple[str, str]]) -> str:
    """Generate a short descriptive title for the conversation using the LLM."""
    # Take last up to 10 messages for context
    snippet = "\n".join(f"{name}: {msg}" for name, msg in messages[-10:])
    prompt = (
        "Generate a concise title (under 8 words) for the following chat conversation:\n\n" + snippet
    )
    title = ""
    model_name = config.get_default_model() or ''
    async for chunk in llm.generate_ollama_response(
        client_id="system",
        user_input=prompt,
        model_name=model_name,
        system_prompt=None
    ):
        title += chunk
    title = title.strip().strip('"')
    # fallback to first user message if empty
    if not title:
        first = next((m[1] for m in messages if m[0] == 'You'), '')
        title = first.split('\n')[0][:30]
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
    async for chunk in llm.generate_ollama_response(
        client_id="system", user_input=prompt, model_name=model_name, system_prompt=None
    ):
        summary += chunk
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
    async for chunk in llm.generate_ollama_response(
        client_id="system", user_input=prompt, model_name=model_name, system_prompt=None
    ):
        response += chunk
    return response.strip().lower().startswith('yes')

# Helper: format display title by stripping special chars, preserving case, and truncating
def format_display_title(key: str, max_len: int = 30) -> str:
    raw = key.split('_', 1)[1] if '_' in key else key
    # remove leading non-alphanumeric chars
    raw = re.sub(r'^[^A-Za-z0-9]+', '', raw)
    # truncate longer titles with ellipsis
    return raw if len(raw) <= max_len else raw[:max_len-3] + '...'

