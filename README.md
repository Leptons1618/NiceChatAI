# NiceGUI ChatBot

A sleek, interactive chatbot built with Python and [NiceGUI](https://nicegui.io/) for seamless conversations powered by your preferred Large Language Model (LLM).

## Features

- Modern, responsive UI with real-time streaming responses
- Support for local LLMs through Ollama integration
- Enhanced message rendering with proper formatting for lists, code blocks, and more
- MongoDB-based conversation storage and retrieval
- Conversation summaries and automatic title generation
- User-friendly settings management
- Easy configuration via web interface

## Installation

1. Clone the repository:
   ```fish
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. Create and activate a virtual environment:
   ```fish
   python3 -m venv .venv
   source .venv/bin/activate.fish
   ```

3. Install dependencies:
   ```fish
   pip install -r requirements.txt
   ```

4. Install MongoDB:
   - [MongoDB Installation Guide](https://docs.mongodb.com/manual/installation/)
   - Alternatively, use MongoDB Atlas cloud service

5. Set up environment variables:
   ```fish
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

### Environment Variables

Create a `.env` file based on the provided `.env.example`:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=nicechat
```

### Configuration Files

It'll automatically create a `config.json` file in the root directory. You can modify it to set your preferences.
- **config.json**: General settings (e.g., model parameters, UI preferences)
- **app/config.py**: Python-level defaults and overrides
- **ui/config_page.py**: UI for live configuration changes

Example `config.json`:
```json
{
    "ollama_base_url": "http://localhost:11434",
    "ollama_timeout": 60,
    "bot_name": "Assistant",
    "default_model": "llama3.2:latest",
    "source_urls": [],
    "theme_dark_mode": true,
    "available_models_cache": [
        "llama3.2:latest"
    ]
}
```

## Usage

1. Start your local Ollama instance:
   ```fish
   ollama serve
   ```

2. Ensure MongoDB service is running:
   ```fish
   # Linux/macOS
   sudo systemctl start mongodb
   # Windows
   net start MongoDB
   ```

3. Launch the app:
   ```fish
   python main.py
   ```

By default, the web interface is available at `http://localhost:8080`.

## Project Structure

```
├── main.py                # Entry point
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .env                   # Your environment variables (git-ignored)
├── config.json            # User config
├── app/
│   ├── llm.py             # LLM wrapper (Ollama integration)
│   ├── config.py          # Python config
│   ├── db.py              # MongoDB operations
│   └── ui/
│       ├── chat_page.py   # Chat UI
│       ├── config_page.py # Settings UI
│       └── message_renderer.py # Enhanced message formatting
```

## Contributing

1. Fork this repo
2. Create a feature branch
3. Submit a pull request

## License

MIT © 2025 Anish Giri
