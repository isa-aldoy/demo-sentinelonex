import google.generativeai as genai
import uvicorn
import json
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from jsonschema import validate, ValidationError
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64

# --- NEW: Correct OPA (WASM) import ---
from opa_wasm import OPA

# --- 1. CONFIGURATION ---

# CRITICAL: Set your Gemini API Key in Vercel environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")
genai.configure(api_key=GOOGLE_API_KEY)

# Load schemas and policies
try:
    with open("playbook.schema.json") as f:
        PLAYBOOK_SCHEMA = json.load(f)
    with open("policy.rego") as f:
        POLICY_REGO = f.read()
except FileNotFoundError as e:
    print(f"CRITICAL ERROR: Missing required file: {e.filename}")
    print("Please create playbook.schema.json and policy.rego in the same directory.")
    raise e

# --- NEW: Initialize the OPA (WASM) engine ---
opa_engine = OPA(policy=POLICY_REGO, query="data.sentinelonex.authz")

# --- NEW: Corrected Gemini Model Names ---
ANALYST_MODEL = genai.GenerativeModel('gemini-2.5-flash')
EXPERT_MODEL = genai.GenerativeModel('gemini-2.5-pro')

# In-memory "databases" for the 48-hour demo
telemetry_db = {}
alerts_db = {}
alert_id_counter = 0

# Generate a signing key pair
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# --- 2. PYDANTIC MODELS (DATA CONTRACTS) ---

class AgentTelemetry(BaseModel):
    hostname: str
    os_platform: str
    processes: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]

class Alert(BaseModel):
    id: int
    agent_id: str
    title: str
    v1_analyst_report: Dict[str, Any]
    v3_expert_playbook: Dict[str, Any]
    playbook_is_valid: bool
    playbook_is_policy_compliant: bool
    policy_check_message: str

# --- 3. HELPER FUNCTIONS (WITH IMPROVED ERROR HANDLING) ---

def get_v1_analyst_report(alert_title: str) -> Dict:
    prompt = f"""
    Act as 'Virtual Security Analyst' (V1.0). Analyze this alert: "{alert_title}"
    Provide ONLY a JSON object with keys: "summary", "mitre_technique", "human_remediation".
    """
    try:
        response = ANALYST_MODEL.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception as e:
        print(f"Error from Analyst AI (Flash): {e}")
        return {"summary": "AI Analyst Error", "mitre_technique": "N/A", "human_remediation": f"Error: {e}"}

def get_v3_expert_playbook(analyst_report: dict) -> Dict:
    prompt = f"""
    Act as 'V3.0 Expert Remediation Agent'. Generate a machine-readable playbook to fix the problem.
    You MUST follow this JSON schema exactly: {json.dumps(PLAYBOOK_SCHEMA)}
    Analyst Report: {json.dumps(analyst_report)}
    Generate the V3.0 playbook now.
    """
    try:
        response = EXPERT_MODEL.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception as e:
        print(f"Error from Expert AI (Pro): {e}")
        return {"case_id": "error", "generated_by": "gemini-pro", "actions": [{"id": "error", "command": "error", "params": {"error": str(e)}, "postcheck": {}}]}

def is_playbook_policy_compliant(playbook: dict, hostname: str) -> tuple[bool, str]:
    input_data = {"playbook": playbook, "agent_hostname": hostname}
    try:
        allow_result = opa_engine.eval(input_data, query="data.sentinelonex.authz.allow")
        
        if allow_result and allow_result[0]['result'] == True:
            return True, "PASSED: AI plan is compliant with human safety policy."
        
        deny_reasons = opa_engine.eval(input_data, query="data.sentinelonex.authz.deny[msg]")
        reason_msg = deny_reasons[0]['result'][0] if deny_reasons and deny_reasons[0]['result'] else "Unknown policy violation."
        return False, f"FAILED: {reason_msg}"
    except Exception as e:
        print(f"Policy Engine Error: {e}")
        return False, f"Policy Engine Error: {str(e)}"

# --- 4. THE API ENDPOINTS ---

app = FastAPI(title="SentinelOneX V3.0 Brain")

# Corrected CORS origins for Tauri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "https://tauri.localhost", "http://localhost:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ingest")
async def ingest_telemetry(telemetry: AgentTelemetry):
    global alert_id_counter
    agent_id = telemetry.hostname
    telemetry_db[agent_id] = telemetry.model_dump()
    print(f"Telemetry received from: {agent_id}")
    
    try:
        # Sentry Detection Engine (Simplified)
        for process in telemetry.processes:
            cmdline = process.get("cmdline", "").lower()
            if "powershell" in process.get("name", "").lower() and "downloadstring" in cmdline and "iex" in cmdline:
                alert_title = f"CRITICAL: PowerShell Download Cradle Detected on '{agent_id}'"
                
                # V3.0 AI PIPELINE
                v1_report = get_v1_analyst_report(alert_title)
                v3_playbook = get_v3_expert_playbook(v1_report)
                
                try:
                    validate(instance=v3_playbook, schema=PLAYBOOK_SCHEMA)
                    is_valid = True
                except ValidationError as e:
                    is_valid = False
                
                is_compliant, policy_msg = is_playbook_policy_compliant(v3_playbook, agent_id)
                
                alert_id_counter += 1
                new_alert = Alert(
                    id=alert_id_counter,
                    agent_id=agent_id,
                    title=alert_title,
                    v1_analyst_report=v1_report,
                    v3_expert_playbook=v3_playbook,
                    playbook_is_valid=is_valid,
                    playbook_is_policy_compliant=is_compliant,
                    policy_check_message=policy_msg
                )
                alerts_db[new_alert.id] = new_alert
                print(f"New alert generated: {alert_title}")
                
        return {"status": "received"}
    except Exception as e:
        print(f"Error during ingestion processing: {e}")
        # Don't crash the whole endpoint if one part fails
        return {"status": "error", "detail": str(e)}

@app.get("/agents")
async def get_agents():
    return {"agents": list(telemetry_db.keys())}

@app.get("/alerts")
async def get_alerts():
    return {"alerts": list(alerts_db.values())}

@app.post("/remediate/{alert_id}")
async def remediate_alert(alert_id: int):
    alert = alerts_db.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if not (alert.playbook_is_valid and alert.playbook_is_policy_compliant):
        raise HTTPException(status_code=400, detail="Cannot remediate: Playbook is unsafe or invalid")

    try:
        playbook_bytes = json.dumps(alert.v3_expert_playbook, sort_keys=True).encode('utf-8')
        signature = private_key.sign(
            playbook_bytes,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        
        signed_playbook = {
            "playbook": alert.v3_expert_playbook,
            "signature_b64": base64.b64encode(signature).decode('utf-8')
        }
        
        print(f"--- SIGNED PLAYBOOK FOR AGENT {alert.agent_id} ---")
        print(json.dumps(signed_playbook, indent=2))
        
        return {"status": "remediation_approved", "signed_playbook": signed_playbook}
    except Exception as e:
        print(f"Error during playbook signing: {e}")
        raise HTTPException(status_code=500, detail=f"Error during playbook signing: {e}")

# This is a Vercel requirement
app = app
