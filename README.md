# NiceGUI ChatBot

A sleek, interactive chatbot built with Python and [NiceGUI](https://nicegui.io/) for seamless conversations powered by your preferred Large Language Model (LLM).

## Features

- Modern web-based UI with NiceGUI
- Configurable LLM backend (e.g., OpenAI, local models)
- Persistent conversation history
- Easy configuration via `config.json` and `app/config.py`

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

## Configuration

- **config.json**: General settings (e.g., API keys, model parameters).
- **app/config.py**: Python-level defaults and overrides.
- **ui/config_page.py**: UI for live configuration changes.

Example `config.json`:
```json
{
  "OPENAI_API_KEY": "your_key_here",
  "MODEL_NAME": "gpt-3.5-turbo",
  "MAX_TOKENS": 1024
}
```

## Usage

Launch the app:
```fish
python main.py
```

By default, the web interface is available at `http://localhost:8080`.

## Project Structure

```
├── main.py                # Entry point
├── requirements.txt       # Python dependencies
├── config.json            # User config
├── app/
│   ├── llm.py             # LLM wrapper
│   ├── config.py          # Python config
│   └── saved_conversations.json
└── ui/
    ├── chat_page.py       # Chat UI
    └── config_page.py     # Settings UI
```

## Contributing

1. Fork this repo
2. Create a feature branch
3. Submit a pull request

## License

MIT © 2025 Anish Giri
