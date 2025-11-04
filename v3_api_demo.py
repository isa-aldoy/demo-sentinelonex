"""SentinelOneX V3.0 Demo – API‑Powered SOAR
Author: Your Name <you@example.com>
License: MIT
"""

import os
import sys
import json
import gradio as gr
import google.generativeai as genai
import jsonschema
from jsonschema import validate
import asyncio
import subprocess  # <-- NEW: To run real processes
import os          # <-- NEW: To get PIDs and kill processes
import time        # <-- NEW: To give processes time to start

# --- Configuration ---
genai.configure(api_key="AIzaSyAvl7mBKFL3xm9hxUbSaOdF2a48OCqLJvY")

# --- AI Model Definitions ---
v1_analyst_model = genai.GenerativeModel('gemini-2.5-flash')
v3_expert_model = genai.GenerativeModel('gemini-2.5-pro')

# --- Schemas ---
analyst_prompt = """
# ROLE: CYBER SECURITY ANALYST (V1.0)
# TASK: Analyze the provided security alert data and generate a human-readable report.
# OUTPUT FORMAT: Strict JSON
# {{
#  "summary": "Brief, 1-2 sentence summary of the critical threat.",
#  "mitre_technique": "MITRE ATT&CK Technique ID and Name (e.g., T1059.001 - PowerShell).",
#  "human_remediation": [
#    "Step 1:...",
#    "Step 2:...",
#    "Step 3:..."
#  ]
# }}
# ---
# ALERT DATA:
# {alert_data}
"""

expert_prompt = """
# ROLE: EXPERT SOAR ENGINEER (V3.0)
# TASK: Convert the V1 Analyst report and original alert data into a V3 machine-readable JSON playbook.
# CONSTRAINTS:
# 1.  Validate the original alert data against the 'alert_schema'.
# 2.  Generate a playbook that is 100% compliant with the 'playbook_schema'.
# 3.  If schema validation fails, return a JSON error object: {{"validation_status": "FAILED", "error": "details..."}}
# 4.  If successful, return a JSON object: {{"validation_status": "PASSED", "playbook": {{...}}}}
# ---
# ALERT SCHEMA (FOR VALIDATION):
{alert_schema}
# ---
# PLAYBOOK SCHEMA (FOR GENERATION):
{playbook_schema}
# ---
# V1 ANALYST REPORT:
{v1_report}
# ---
# ORIGINAL ALERT DATA:
{alert_data}
"""

alert_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SentinelOneX Alert",
    "type": "object",
    "properties": {
        "timestamp": {"type": "string", "format": "date-time"},
        "hostname": {"type": "string"},
        "process_name": {"type": "string"},
        "process_id": {"type": "integer"},  # <-- CHANGED: We will use a real PID
        "process_commandline": {"type": "string"},
    },
    "required": ["timestamp", "hostname", "process_name", "process_id"]
}

playbook_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SentinelOneX Playbook",
    "type": "object",
    "properties": {
        "id": {"type": "string", "pattern": "^playbook-.*$"},
        "case_id": {"type": "string"},
        "generated_by": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "command": {"type": "string", "enum": ["kill_process", "quarantine_file", "isolate_host", "remove_persistence"]},
                    "params": {"type": "object"},
                },
                "required": ["id", "command", "params"]
            }
        }
    },
    "required": ["id", "case_id", "generated_by", "actions"]
}

# --- mcp-testbench Imports (from our previous step) ---
from mcp_testbench.engine import TestEngine
from mcp_testbench.reporter import compute_score

def safe_json_loads(json_string):
    try:
        if json_string.startswith("```json"):
            json_string = json_string[7:]
        if json_string.endswith("```"):
            json_string = json_string[:-3]
        json_string = json_string.strip()
        return json.loads(json_string)
    except json.JSONDecodeError:
        print(f"--- AI JSON PARSE ERROR ---\n{json_string}\n--- END ERROR ---")
        return {"error": "Invalid JSON format received from AI."}

# --- NEW: Real Simulation & Remediation ---
def launch_real_threat():
    print("[SIMULATION] Launching harmless process (notepad.exe)...")
    DETACHED_PROCESS = 0x00000008
    process = subprocess.Popen(["notepad.exe"], creationflags=DETACHED_PROCESS)
    pid = process.pid
    print(f"[SIMULATION] Process launched with PID: {pid}")
    time.sleep(1)
    real_alert_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hostname": "DESKTOP-B3351V9",
        "process_name": "notepad.exe",
        "process_id": pid,
        "process_commandline": "notepad.exe C:\\Users\\isaal\\Desktop\\secret_plans.txt"
    }
    return real_alert_data

def execute_playbook(playbook_obj):
    execution_log = []
    if playbook_obj.get("validation_status") != "PASSED":
        execution_log.append("[EXECUTION] Playbook validation FAILED. No actions taken.")
        return "\n".join(execution_log)
    playbook = playbook_obj.get("playbook", {})
    actions = playbook.get("actions", [])
    if not actions:
        execution_log.append("[EXECUTION] Playbook is valid but contains no actions.")
        return "\n".join(execution_log)
    execution_log.append(f"[EXECUTION] Received playbook {playbook.get('id')}. Executing {len(actions)} actions...")
    for i, action in enumerate(actions):
        command = action.get("command")
        params = action.get("params", {})
        action_log = f"  [ACTION {i+1}] {command.upper()}: "
        if command == "kill_process":
            pid_to_kill = params.get("pid") or params.get("process_id")
            if pid_to_kill:
                try:
                    subprocess.run(["taskkill", "/F", "/PID", str(pid_to_kill)], check=True, capture_output=True)
                    action_log += f"SUCCESS. Terminated process with PID {pid_to_kill}."
                    print(f"[EXECUTION] Terminated PID: {pid_to_kill}")
                except subprocess.CalledProcessError:
                    action_log += f"FAILED. Process with PID {pid_to_kill} not found or access denied."
                except Exception as e:
                    action_log += f"ERROR. Failed to kill PID {pid_to_kill}: {e}"
            else:
                action_log += "SKIPPED. No 'pid' found in params."
        elif command == "quarantine_file":
            file_hash = params.get("hash") or params.get("file_hash")
            action_log += f"SKIPPED (Simulation). Would quarantine file with hash: {file_hash}"
        elif command == "isolate_host":
            hostname = params.get("hostname")
            action_log += f"SKIPPED (Simulation). Would isolate host: {hostname}"
        else:
            action_log += f"SKIPPED. Unknown command '{command}'."
        execution_log.append(action_log)
    execution_log.append("[EXECUTION] Playbook complete.")
    return "\n".join(execution_log)

def run_real_end_to_end_simulation():
    try:
        real_alert_data = launch_real_threat()
        alert_data_str = json.dumps(real_alert_data)
    except Exception as e:
        print(f"Failed to launch simulation: {e}")
        return {"error": str(e)}, {}, f"Failed to launch simulation: {e}"
    v1_prompt_filled = analyst_prompt.format(alert_data=alert_data_str)
    try:
        v1_response = v1_analyst_model.generate_content(v1_prompt_filled)
        v1_report = safe_json_loads(v1_response.text)
        if "error" in v1_report:
            return v1_report, {}, "V1 Analyst AI failed."
    except Exception as e:
        return {"error": str(e)}, {}, f"V1 Analyst AI failed: {e}"
    v3_prompt_filled = expert_prompt.format(
        alert_schema=json.dumps(alert_schema, indent=2),
        playbook_schema=json.dumps(playbook_schema, indent=2),
        v1_report=json.dumps(v1_report, indent=2),
        alert_data=alert_data_str
    )
    try:
        v3_response = v3_expert_model.generate_content(v3_prompt_filled)
        v3_playbook_response = safe_json_loads(v3_response.text)
    except Exception as e:
        return v1_report, {"error": str(e)}, f"V3 Expert AI failed: {e}"
    try:
        execution_log = execute_playbook(v3_playbook_response)
    except Exception as e:
        execution_log = f"[EXECUTION] CRITICAL ERROR: {e}"
    return v1_report, v3_playbook_response, execution_log

async def run_security_scan(target_url):
    if not target_url:
        return {"error": "No target URL provided."}, "Error: No URL"
    if not target_url.startswith('http://') and not target_url.startswith('https://'):
        target_url = 'http://' + target_url
    print(f"Starting MCP security scan on: {target_url}")
    try:
        engine = TestEngine(base_url=target_url)
        results = await engine.run_all()
        score = compute_score(results)
        print(f"Scan complete. Score: {score}")
        return results, f"Security Score: {score}"
    except Exception as e:
        error_message = f"Scan failed: {str(e)}"
        print(error_message)
        return {"error": error_message, "target": target_url}, "Scan Failed"

# ------------------------------------------------------------------
# 5️⃣  Gradio UI
# ------------------------------------------------------------------
with gr.Blocks(theme=gr.themes.Monochrome()) as demo:
    gr.Markdown("# SentinelOneX V3.0 – AI-Powered SOAR Demo")
    with gr.Tabs():
        with gr.Tab("Real End-to-End Remediation"):
            with gr.Column():
                simulate_button = gr.Button("Launch 'Notepad' Threat & Remediate", variant="danger")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## V1.0 Analyst AI Report (Flash)")
                    output_analyst = gr.JSON(label="Analyst Report")
                with gr.Column():
                    gr.Markdown("## V3.0 Expert Playbook (Pro)")
                    output_expert = gr.JSON(label="Remediation Playbook")
            with gr.Row():
                gr.Markdown("## V3.1 Remediation Execution Log")
                output_execution = gr.Textbox(label="Execution Log", lines=8, interactive=False)
            simulate_button.click(
                fn=run_real_end_to_end_simulation,
                inputs=None,
                outputs=[output_analyst, output_expert, output_execution]
            )
        with gr.Tab("On-Demand Security Scan (MCP Testbench)"):
            gr.Markdown(
                "## 🔍 Run Security Scan\n"
                "Enter a URL to test its security against the MCP Testbench. "
            )
            with gr.Row():
                scan_url_input = gr.Textbox(
                    label="Target URL", 
                    placeholder="e.g., http://localhost:8000 or mcp.yourcompany.com"
                )
            scan_button = gr.Button("Start Security Scan", variant="primary")
            gr.Markdown("### Scan Results")
            scan_score_output = gr.Label(label="Security Score")
            scan_report_output = gr.JSON(label="Full JSON Report")
            scan_button.click(
                fn=run_security_scan,
                inputs=[scan_url_input],
                outputs=[scan_report_output, scan_score_output]
            )
# ------------------------------------------------------------------
# 6️⃣  Entrypoint
# ------------------------------------------------------------------
if __name__ == "__main__":
    demo.launch()
