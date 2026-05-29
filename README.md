# AI GitHub Repository Summarizer

A Streamlit web app that fetches any public GitHub repository's key source files and uses **Google Gemini** to generate a structured **Developer Onboarding Guide**.

## Features

- Parses any public GitHub URL and recursively fetches the file tree via the GitHub REST API
- Automatically tries both `main` and `master` as the default branch
- Extracts `README.md`, `package.json`, `requirements.txt`, and all `.py` / `.js` / `.ts` source files
- Sends the bundled content to `gemini-2.5-flash` with a strict system prompt
- Renders the generated guide as formatted Markdown in the browser

## Project Structure

```
repo-analyzer/
├── app.py              # Streamlit UI
├── github_fetcher.py   # GitHub API + file-tree parsing
├── summarizer.py       # Gemini API integration
├── requirements.txt
└── .gitignore
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/repo-analyzer.git
cd repo-analyzer
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Obtain a Gemini API key

Get a free key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey).

You can supply the key in two ways:

**Option A – Sidebar input (recommended for quick use)**  
Paste it directly into the sidebar field when the app loads.

**Option B – Environment variable**  
```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your-key-here"
# macOS / Linux
export GEMINI_API_KEY="your-key-here"
```

### 5. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser, paste a public GitHub URL, and click **Summarize Repository**.

## Usage Example

```
https://github.com/pallets/flask
```

The app will analyze the repository and produce a guide covering:

1. High-level project purpose
2. Core tech stack
3. Key architectural components and files
4. 3-sentence getting-started summary for new developers

## Limitations

- Only public repositories are supported (no GitHub token required, but the unauthenticated API rate limit is 60 requests/hour)
- Binary files and very large files may be skipped or truncated by the model's context window
- Requires a valid Gemini API key with access to `gemini-2.5-flash`

## License

MIT
