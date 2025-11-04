# SentinelOneX Copilot Instructions

## Project Overview
**SentinelOneX V3.0** is an AI-powered SOAR (Security Orchestration, Automation and Response) demo that simulates a multi-agent threat response system using Google Gemini models. It combines two AI models (Flash for analysis, Pro for expert remediation) with a Gradio UI to demonstrate autonomous security response workflows.

### Key Architecture
```
THREAT SIMULATION → V1 ANALYST (Flash) → V3 EXPERT (Pro) → PLAYBOOK EXECUTION
    (Real Process)         (Human Summary)    (Machine Playbook)   (taskkill/etc)
```

## Core Components & Patterns

### 1. **Dual-Model AI Pipeline** (`v3_api_demo.py` lines 13-14)
- **V1 Analyst Model** (`gemini-2.5-flash`): Lightweight, fast analysis for human readability
- **V3 Expert Model** (`gemini-2.5-pro`): Advanced reasoning for JSON playbook generation
- Both models use strict JSON output formats via prompt engineering (not function calling)
- Always use `safe_json_loads()` to parse AI responses (handles markdown code blocks)

**Pattern**: When adding new AI capabilities, define separate models and prompts; don't try to make one model do both analysis and execution planning.

### 2. **JSON Schema Validation** (lines 47-95)
- **alert_schema**: Validates incoming security alert data (required fields: `timestamp`, `hostname`, `process_name`, `process_id`)
- **playbook_schema**: Validates AI-generated remediation playbooks
- Use `jsonschema.validate()` in the V3 Expert prompt to ensure AI compliance
- All AI prompts must include schema definitions as context

**Pattern**: Schemas are defined in Python dicts, passed to prompts as formatted JSON strings. Schemas enforce consistency without custom validation code.

### 3. **Threat Simulation & Real Process Management** (lines 107-135)
- `launch_real_threat()`: Spawns a real subprocess with `DETACHED_PROCESS` flag (Windows-specific)
- Returns alert_data dict with real PID for downstream processing
- `execute_playbook()`: Runs actual OS commands (e.g., `taskkill /F /PID`)
- Pattern: Simulated threats (e.g., PowerShell cradle) must set `creationflags=subprocess.DETACHED_PROCESS` to prevent UI blocking

### 4. **Safe JSON Parsing** (lines 103-110)
```python
def safe_json_loads(json_string):
    # Strips markdown code blocks: ```json ... ```
    # Returns {"error": "..."} on parse failure
```
**Always use this** instead of `json.loads()` directly because Gemini sometimes wraps JSON in markdown blocks.

### 5. **Gradio UI Patterns** (lines 191-245)
- Tabs separate workflows (Real End-to-End, Security Scan)
- Each tab is a workflow with Input → Button → Outputs
- Button clicks wire to functions with `inputs`/`outputs` mapping
- Use `gr.JSON()` for structured data, `gr.Textbox()` for logs/streaming
- Theme: `gr.themes.Monochrome()` for professional look

**Pattern**: For streaming/multi-step workflows, use generator functions with `yield` to update UI progressively.

## Critical Workflows

### Adding a New Threat Type
1. Modify `launch_real_threat()` to spawn the new threat
2. Update `alert_schema` if new fields are needed
3. Update `analyst_prompt` to reference the new threat pattern
4. Update `expert_prompt` to include new remediation commands
5. Add new `elif` blocks in `execute_playbook()` to handle new command types

### Adding a New Remediation Action
1. Add command name to `playbook_schema` enum: `"enum": ["kill_process", "quarantine_file", "NEW_ACTION"]`
2. Document the command in `expert_prompt` under "AVAILABLE REMEDIATION COMMANDS"
3. Add `elif command == "NEW_ACTION":` block in `execute_playbook()`
4. For simulated actions: just log and skip. For real actions: use `subprocess.run()`

### Integrating New Gemini Models
- Update model lines: `v1_analyst_model = genai.GenerativeModel('model-name')`
- Keep prompts generic (don't hardcode model names in prompts)
- Test with `safe_json_loads()` to ensure consistent JSON output

## Configuration & Secrets

- **API Key**: Set via `genai.configure(api_key="...")` or `GOOGLE_API_KEY` env var
- **Models**: Hardcoded at top of file (v1 = Flash, v3 = Pro)
- **Schemas**: Defined as module-level Python dicts (not external files)

## Common Pitfalls

1. **AI JSON Format**: Gemini often wraps JSON in markdown. Always use `safe_json_loads()`.
2. **Windows Process Management**: Use `creationflags=subprocess.DETACHED_PROCESS` to prevent UI freezes.
3. **Schema Validation**: Schemas must be passed as formatted JSON strings in prompts, not Python dicts.
4. **Gradio Streaming**: Use `yield` in button click handlers to update UI progressively; avoid blocking operations.
5. **Real vs Simulated**: Real commands use `subprocess.run()` (e.g., `taskkill`). Simulated commands just log.

## Files of Interest

| File | Purpose |
|------|---------|
| `v3_api_demo.py` | Main app: AI models, schemas, threat sim, UI |
| `requirements.txt` | Dependencies: `gradio`, `google-generativeai`, `jsonschema` |
| `mcp_testbench/` | Security scan module (separate workflow) |
| `.venv/` | Python virtual environment (activate before running) |
| `demo_output/` | Logs and sample outputs |

## Development Workflow

1. Activate `.venv`: `.venv\Scripts\activate` (PowerShell)
2. Install deps: `pip install -r requirements.txt`
3. Set API key: `$env:GOOGLE_API_KEY="..."`
4. Run: `python v3_api_demo.py`
5. Open: `http://127.0.0.1:7860`

## Testing & Debugging

- **Print debugging**: Use `print("[TAG]")` at start of functions; appears in terminal
- **JSON errors**: Enable `safe_json_loads()` error logging to see raw AI responses
- **UI issues**: Use Gradio's browser inspector (F12) to check console errors
- **Process management**: Use `tasklist` or Task Manager to verify process spawning/cleanup
