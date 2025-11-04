# SentinelOneX V3.0 – API‑Powered SOAR Demo

This demo shows how Gemini-powered agents can:
- Analyze a security alert (fast, human-readable)
- Generate a machine-readable remediation playbook
- Validate the playbook against a JSON schema
- Show everything in a sleek Gradio UI

## Getting Started

### Prerequisites
- Python 3.10+
- Gemini API key (get it at https://aistudio.google.com/app/apikey)

### Setup
1. Clone the repo or copy the files
2. Create a virtual environment
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies
   ```powershell
   pip install -r requirements.txt
   ```
4. Add your Gemini API key to `v3_api_demo.py` or set the `GOOGLE_API_KEY` environment variable
5. Run the demo
   ```powershell
   python v3_api_demo.py
   ```
6. Open [http://127.0.0.1:7860](http://127.0.0.1:7860) in your browser

## Optional
- `.gitignore` and `demo_output/` for logs/samples
- Dockerfile included for containerized runs
