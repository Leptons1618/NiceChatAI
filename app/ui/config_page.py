from nicegui import ui, app
import logging

# Use relative imports for modules within the app package
from .. import config
from .. import llm

logger = logging.getLogger(__name__)

@ui.page('/config')
async def config_page():
    cfg = config.get_config() # Load current config

    # Add enhanced CSS for modern UI
    ui.add_head_html("""<style>
        /* Modern form styling */
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
        
        /* Input styling */
        .config-input {
            border-radius: 8px !important;
            transition: all 0.2s !important;
            border: 1px solid #44475a !important;
        }
        .config-input:focus {
            border-color: #bd93f9 !important;
            box-shadow: 0 0 0 2px rgba(189, 147, 249, 0.3) !important;
        }
        
        /* Button styling */
        .config-button {
            transition: all 0.2s !important;
            border-radius: 8px !important;
        }
        .config-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
        }
        
        /* Section styling */
        .config-section {
            border-left: 3px solid #bd93f9 !important;
            padding-left: 16px !important;
            margin-bottom: 24px !important;
        }
        
        /* Label styling */
        .config-label {
            font-weight: 500 !important;
            margin-bottom: 4px !important;
            color: #f8f8f2 !important;
        }
        
        /* Help text styling */
        .help-text {
            font-size: 0.8rem !important;
            opacity: 0.7 !important;
            margin-top: 4px !important;
        }
    </style>""")

    # --- Helper Functions ---
    async def refresh_models_list():
        # Show loading notification
        # ui.notify("Refreshing models list...", timeout=2000, position='top-right', 
        #           color='info', icon='fa-solid fa-spinner fa-spin', close_button='X')
        
        models = await llm.get_available_models() # Fetch and update cache via llm module
        if models:
            model_select.options = models
            # Update the value if the current default isn't in the new list
            current_default = config.get_default_model()
            if current_default not in models:
                 new_default = models[0] if models else None
                 config.set_default_model(new_default) # Update config directly
                 model_select.value = new_default # Update UI
                 ui.notify(f"Default model reset to {new_default}", color='warning', position='top-right', 
                           timeout=3000, icon='fa-solid fa-triangle-exclamation', close_button='X')
            else:
                 model_select.value = current_default # Ensure UI reflects config
            model_select.update()
            # ui.notify("Models list refreshed successfully", color='positive', position='top-right', 
            #           timeout=2000, icon='fa-solid fa-check', close_button='X')
        else:
            ui.notify("Failed to refresh models from Ollama", color='negative', position='top-right', 
                      timeout=3000, icon='fa-solid fa-circle-exclamation', close_button='X')
            # Keep existing options in selector if refresh fails
            model_select.options = config.get_available_models_cache()
            model_select.value = config.get_default_model()
            model_select.update()

    def save_and_notify():
        # Show saving notification
        # ui.notify("Saving configuration...", timeout=2000, position='top-right', 
        #           color='info', icon='fa-solid fa-spinner fa-spin', close_button='X')
        
        # Update config dictionary from UI elements before saving
        config.update_config_value("bot_name", bot_name_input.value)
        config.update_config_value("default_model", model_select.value)
        config.update_config_value("ollama_base_url", ollama_url_input.value)
        config.update_config_value("ollama_timeout", timeout_input.value)
        # Simple handling for comma-separated URLs
        urls = [url.strip() for url in source_urls_input.value.split(',') if url.strip()]
        config.update_config_value("source_urls", urls)
        config.update_config_value("theme_dark_mode", dark_mode_switch.value)

        if config.save_config():
            ui.notify("Configuration saved successfully!", color='positive', position='top-right', 
                      timeout=3000, icon='fa-solid fa-check', close_button='X')
            # Apply theme change immediately
            if dark_mode_switch.value:
                ui.dark_mode().enable()
            else:
                ui.dark_mode().disable()
            
            # Notify user to restart the app if they changed settings that require restart
            # ui.notify("Some settings will take effect after restarting the app", color='info', 
            #           timeout=5000, position='top-right', icon='fa-solid fa-info-circle', close_button='X')
        else:
            ui.notify("Failed to save configuration", color='negative', position='top-right', 
                      timeout=3000, icon='fa-solid fa-circle-exclamation', close_button='X')

    # --- Enhanced UI Layout ---
    # Header with visible back button and title
    with ui.header(elevated=True).classes('bg-dark flex items-center px-4 py-2 shadow-lg'):
        with ui.row().classes('items-center'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/'))\
                .props('flat round')\
                .classes('text-white mr-2')
            ui.label('Configuration').classes('text-xl font-semibold text-white')

    # Main content area with enhanced card styling
    with ui.column().classes('w-full px-4 py-4 flex-grow'):
        with ui.tabs().classes('w-full max-w-3xl mx-auto') as tabs:
            general_tab = ui.tab('General', icon='settings')
            model_tab = ui.tab('Model Settings', icon='smart_toy')
            appearance_tab = ui.tab('Appearance', icon='palette')
            advanced_tab = ui.tab('Advanced', icon='code')
        
        with ui.tab_panels(tabs, value=general_tab).classes('w-full max-w-3xl mx-auto'):
            # General Settings Tab
            with ui.tab_panel(general_tab):
                with ui.card().classes('w-full bg-gray-900 text-light shadow-xl rounded-lg config-card'):
                    with ui.column().classes('w-full p-6 space-y-6'):
                        # Bot Settings Section with enhanced styling
                        with ui.column().classes('config-section'):
                            ui.label('Bot Settings').classes('text-lg font-medium text-primary mb-4')
                            
                            ui.label('Bot Name').classes('config-label')
                            bot_name_input = ui.input(value=cfg.get("bot_name", "")).classes('w-full config-input').props('outlined dark color=primary')
                            ui.label('The name that will be displayed in the chat interface').classes('help-text')

            # Model Settings Tab
            with ui.tab_panel(model_tab):
                with ui.card().classes('w-full bg-gray-900 text-light shadow-xl rounded-lg config-card'):
                    with ui.column().classes('w-full p-6 space-y-6'):
                        # Ollama Settings Section with enhanced styling
                        with ui.column().classes('config-section'):
                            ui.label('Ollama Connection').classes('text-lg font-medium text-primary mb-4')
                            
                            ui.label('Ollama Base URL').classes('config-label')
                            ollama_url_input = ui.input(value=cfg.get("ollama_base_url", "")).classes('w-full config-input').props('outlined dark color=primary')
                            ui.label('The URL where your Ollama instance is running (e.g., http://localhost:11434)').classes('help-text')
                            
                            ui.label('Request Timeout (seconds)').classes('config-label mt-4')
                            timeout_input = ui.number(value=cfg.get("ollama_timeout", 60), min=5, step=1).classes('w-full config-input').props('outlined dark color=primary')
                            ui.label('Maximum time to wait for model responses').classes('help-text')
                        
                        # Model Selection Section with enhanced styling
                        with ui.column().classes('config-section'):
                            ui.label('Model Selection').classes('text-lg font-medium text-primary mb-4')
                            
                            with ui.row().classes('items-center w-full justify-between'):
                                ui.label('Default Model:').classes('config-label')
                                ui.button(icon='refresh', text='Refresh Models', on_click=refresh_models_list).props('flat dense').classes('config-button text-info')
                            
                            model_select = ui.select(
                                config.get_available_models_cache(),
                                value=config.get_default_model()
                            ).classes('w-full config-input mt-2').props('outlined dark color=primary')
                            ui.label('The model that will be used by default for new conversations').classes('help-text')

            # Appearance Tab
            with ui.tab_panel(appearance_tab):
                with ui.card().classes('w-full bg-gray-900 text-light shadow-xl rounded-lg config-card'):
                    with ui.column().classes('w-full p-6 space-y-6'):
                        # Theme Settings Section with enhanced styling
                        with ui.column().classes('config-section'):
                            ui.label('Theme Settings').classes('text-lg font-medium text-primary mb-4')
                            
                            with ui.row().classes('items-center justify-between'):
                                with ui.column().classes('flex-grow'):
                                    ui.label('Dark Mode').classes('config-label')
                                    ui.label('Enable dark mode for the application').classes('help-text')
                                dark_mode_switch = ui.switch(value=cfg.get("theme_dark_mode", True)).props('color=primary')

            # Advanced Tab
            with ui.tab_panel(advanced_tab):
                with ui.card().classes('w-full bg-gray-900 text-light shadow-xl rounded-lg config-card'):
                    with ui.column().classes('w-full p-6 space-y-6'):
                        # Source URLs Section with enhanced styling
                        with ui.column().classes('config-section'):
                            ui.label('Advanced Settings').classes('text-lg font-medium text-primary mb-4')
                            
                            ui.label('Source URLs (comma-separated)').classes('config-label')
                            source_urls_input = ui.textarea(value=','.join(cfg.get("source_urls", []))).classes('w-full config-input').props('outlined dark color=primary')
                            ui.label('URLs to use as sources for responses').classes('help-text')

        # Save Button at bottom
        with ui.row().classes('w-full max-w-3xl mx-auto justify-end mt-6'):
            ui.button('Save Configuration', icon='save', on_click=save_and_notify).props('color=primary').classes('config-button')

    # Initial model list load (non-blocking) 
    await refresh_models_list()