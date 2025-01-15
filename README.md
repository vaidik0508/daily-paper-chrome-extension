# Daily AI Research Papers Chrome Extension

A Chrome extension that shows daily research papers in AI with detailed explanations using AI-powered analysis completely locally using LLM from LMStudio.

## Features

- Daily updates of new AI research papers from arXiv
- AI-powered paper analysis and summarization
- Section-wise paper explanations
- Easy-to-use Chrome extension interface
- MongoDB-based storage for processed papers

## Setup

### Prerequisites

- Python 3.8+
- MongoDB
- Chrome browser
- Ollama with phi3.5 model installed

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DailyPaperChromeExtension.git
cd DailyPaperChromeExtension
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory:
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ai_papers
MAX_PAPERS=5
```

4. Install the Chrome extension:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `chrome_extension` folder

### Usage

1. Start the FastAPI backend server:
   - Windows: Double-click `start_server.bat`
   - Linux: `python app.py`

2. Start the paper sync service:
   - Windows: Double-click `start_sync.bat`
   - Linux: `python utils.py`

3. Click the extension icon in Chrome to view the latest papers

## Architecture

- `chrome_extension/`: Chrome extension files
- `app.py`: FastAPI backend server
- `utils.py`: Paper fetching and processing logic
- `models.py`: Database models and operations

## License

MIT License
