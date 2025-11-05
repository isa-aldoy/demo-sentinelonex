"""SentinelOneX V4.0 - DEFENDER APP (Streamlit Version)
Runs on Port 7861
Purpose: Real-time threat monitoring and AI-powered remediation dashboard
"""

import streamlit as st
import time
import datetime
import psutil
import subprocess
import threading
import json
from collections import deque
import asyncio
import requests  # For OpenRouter API

# Google Gemini API
import google.generativeai as genai
import os

# MCP Security Scanner
try:
    from mcp_testbench.engine import TestEngine
    from mcp_testbench.reporter import compute_score
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[WARNING] mcp_testbench not available - Security Scan disabled")

# === API CONFIGURATION ===
# Google Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    gemini_flash_model = genai.GenerativeModel('gemini-2.0-flash')
    gemini_pro_model = genai.GenerativeModel('gemini-2.0-pro')
else:
    gemini_flash_model = None
    gemini_pro_model = None
    print("[WARNING] GOOGLE_API_KEY not set - Gemini disabled")

# OpenRouter API Keys (FREE MODELS - No Gemini limits!)
openrouter_primary = os.getenv("OPENROUTER_KEY") or "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"
openrouter_fallback = os.getenv("OPENROUTER_FALLBACK") or "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"

# AI Model Selection (Change this to switch between providers)
USE_OPENROUTER = True  # Set to True to use FREE OpenRouter models, False for Gemini

# === OPENROUTER AI FUNCTIONS ===
def call_openrouter_api(model_name, prompt, api_key):
    """Call OpenRouter API for FREE AI models (no rate limits like Gemini)."""
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
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[OPENROUTER] Error calling {model_name}: {str(e)[:200]}")
        raise

def waterfall_ai_call(prompt, is_expert=False):
    """
    WATERFALL AI: Try multiple FREE models in priority order.
    
    ANALYST (Fast): Gemma → Llama Scout → DeepSeek → MiniMax → Gemini
    EXPERT (Deep): DeepSeek → Gemma → Llama Scout → MiniMax → Gemini
    """
    if is_expert:
        # EXPERT MODELS (complex reasoning for playbooks)
        attempts = [
            ("DeepSeek V3.1", lambda: call_openrouter_api("deepseek/deepseek-chat-v3.1:free", prompt, openrouter_primary)),
            ("Google Gemma 27B", lambda: call_openrouter_api("google/gemma-3-27b-it:free", prompt, openrouter_primary)),
            ("Meta Llama Scout", lambda: call_openrouter_api("meta-llama/llama-4-scout:free", prompt, openrouter_primary)),
            ("MiniMax M2", lambda: call_openrouter_api("minimax/minimax-m2:free", prompt, openrouter_fallback)),
            ("Gemini Pro", lambda: gemini_pro_model.generate_content(prompt).text if gemini_pro_model else None),
        ]
    else:
        # ANALYST MODELS (fast analysis)
        attempts = [
            ("Google Gemma 27B", lambda: call_openrouter_api("google/gemma-3-27b-it:free", prompt, openrouter_primary)),
            ("Meta Llama Scout", lambda: call_openrouter_api("meta-llama/llama-4-scout:free", prompt, openrouter_primary)),
            ("DeepSeek V3.1", lambda: call_openrouter_api("deepseek/deepseek-chat-v3.1:free", prompt, openrouter_primary)),
            ("MiniMax M2", lambda: call_openrouter_api("minimax/minimax-m2:free", prompt, openrouter_fallback)),
            ("Gemini Flash", lambda: gemini_flash_model.generate_content(prompt).text if gemini_flash_model else None),
        ]
    
    # Try each model in order
    for model_name, model_call in attempts:
        try:
            print(f"[AI] Trying {model_name}...")
            result = model_call()
            if result:
                print(f"[AI] ✅ {model_name} succeeded!")
                return result, model_name
        except Exception as e:
            print(f"[AI] ❌ {model_name} failed: {str(e)[:100]}")
            continue
    
    return "ERROR: All AI models failed", "None"

# Compatibility aliases for existing code
v1_analyst_model = "openrouter" if USE_OPENROUTER else gemini_flash_model
v3_expert_model = "openrouter" if USE_OPENROUTER else gemini_pro_model


# FIXED: Use Streamlit session_state to persist data across reruns
if 'threat_queue' not in st.session_state:
    st.session_state.threat_queue = deque(maxlen=100)
    st.session_state.threat_lock = threading.Lock()
    st.session_state.sentry_active = threading.Event()
    st.session_state.detected_pids = set()

# Create local references for cleaner code
threat_queue = st.session_state.threat_queue
threat_lock = st.session_state.threat_lock
sentry_active = st.session_state.sentry_active
detected_pids = st.session_state.detected_pids

# Background Sentry monitoring function - DEFINED FIRST!
def sentry_monitor_loop():
    """Background worker thread that monitors processes for threats."""
    print("[SENTRY] Sentry thread activated. Monitoring processes...")
    
    while sentry_active.is_set():
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if not proc.info['cmdline']:
                    continue
                
                pid = proc.info['pid']
                if pid in detected_pids:
                    continue
                
                cmdline_list = proc.info['cmdline']
                cmdline = " ".join(cmdline_list).lower() if isinstance(cmdline_list, list) else str(cmdline_list).lower()
                proc_name = proc.info['name'].lower()
                
                # Threat patterns
                threat_patterns = [
                    ("powershell.exe", "nonexistent-malware.ps1"),
                    ("cmd.exe", "staged_malware"),
                    ("powershell.exe", ".connect"),
                    ("svchost.exe", "windows_update_service"),
                ]
                
                threat_detected = False
                threat_type = "unknown"
                
                for pattern_name, pattern_indicator in threat_patterns:
                    if pattern_name in proc_name and pattern_indicator in cmdline:
                        threat_detected = True
                        threat_type = pattern_name
                        break
                
                if threat_detected:
                    detected_pids.add(pid)
                    print(f"[SENTRY] ⚠️ THREAT DETECTED! PID: {pid} | Type: {threat_type}")
                    
                    with threat_lock:
                        threat_queue.append({
                            "pid": pid,
                            "threat_type": threat_type,
                            "cmdline": cmdline_list,
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "analyzed": False
                        })
                        print(f"[SENTRY] 📤 Added to threat queue for analysis")
                    
                    # DISABLED: Auto-remediation - let UI handle manual review
                    # try:
                    #     subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                    #                  check=False, capture_output=True, timeout=5)
                    #     print(f"[SENTRY] ✅ Auto-remediated threat (PID {pid})")
                    # except Exception as e:
                    #     print(f"[SENTRY] ⚠️ Remediation failed: {e}")
            
            time.sleep(0.1)  # Fast polling
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception as e:
            print(f"[SENTRY] Error: {e}")
            time.sleep(1)
    
    print("[SENTRY] Sentry thread deactivated.")

# Page config
st.set_page_config(
    page_title="SentinelOneX V4.0 Defender",
    page_icon="🛡️",
    layout="wide"
)

# Initialize session state and AUTO-START SENTRY
if 'sentry_started' not in st.session_state:
    st.session_state.sentry_started = False
    # AUTO-START SENTRY ON LOAD
    sentry_active.set()
    sentry_thread = threading.Thread(target=sentry_monitor_loop, daemon=True)
    sentry_thread.start()
    st.session_state.sentry_started = True
    print("[STREAMLIT] 🚀 Auto-started Sentry monitoring!")

# Custom CSS
st.markdown("""
<style>
.stAlert {font-size: 14px;}
.threat-box {
    background-color: #1e1e1e;
    padding: 20px;
    border-radius: 10px;
    border-left: 5px solid #ff4b4b;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# Header
st.title("🛡️ SentinelOneX V4.0 - Defender Platform")
st.markdown("**Real-Time Threat Detection & AI Remediation**")
st.markdown("---")

# Sidebar controls
with st.sidebar:
    st.header("🎛️ Controls")
    
    # AI MODEL SELECTION
    st.markdown("---")
    st.subheader("🤖 AI Provider")
    ai_provider = st.radio(
        "Select AI Provider",
        ["OpenRouter (FREE, No Limits)", "Google Gemini (Limited)"],
        index=0 if USE_OPENROUTER else 1,
        help="OpenRouter provides FREE models without rate limits. Gemini has usage restrictions."
    )
    
    if ai_provider == "OpenRouter (FREE, No Limits)":
        USE_OPENROUTER = True
        st.success("✅ Using FREE OpenRouter models")
        st.caption("Models: DeepSeek V3.1, Gemma 27B, Llama Scout, MiniMax M2")
    else:
        USE_OPENROUTER = False
        st.info("ℹ️ Using Gemini (rate limits apply)")
        st.caption("Models: Gemini 2.0 Flash, Gemini 2.0 Pro")
    
    # DEBUG PANEL - Shows real-time state
    st.markdown("---")
    st.subheader("🔍 Debug Panel")
    with st.container(border=True):
        st.metric("Queue Length", len(st.session_state.threat_queue))
        st.metric("Sentry Active", "✅ YES" if st.session_state.sentry_active.is_set() else "❌ NO")
        st.metric("Detected PIDs", len(st.session_state.detected_pids))
        if len(st.session_state.threat_queue) > 0:
            st.success(f"🎯 {len(st.session_state.threat_queue)} threat(s) in queue")
        else:
            st.info("📭 Queue is empty")
    st.markdown("---")
    
    if st.button("🟢 Start Sentry Monitoring", use_container_width=True):
        if not sentry_active.is_set():
            sentry_active.set()
            st.success("✅ Sentry activated!")
            st.rerun()
    
    if st.button("🔴 Stop Sentry Monitoring", use_container_width=True):
        if sentry_active.is_set():
            sentry_active.clear()
            st.warning("⏹️ Sentry deactivated")
            st.rerun()
    
    st.markdown("---")
    st.markdown(f"**Status:** {'🟢 ACTIVE' if sentry_active.is_set() else '🔴 STOPPED'}")
    st.markdown(f"**Threats Detected:** {len(threat_queue)}")
    
    st.markdown("---")
    auto_refresh = st.checkbox("🔄 Auto-refresh (every 0.5s)", value=True)
    
    if auto_refresh:
        st.markdown("*Refreshing in real-time...*")

# Main display area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📡 Live Threat Feed")
    
    if len(threat_queue) == 0:
        st.info("🔍 Monitoring... No threats detected yet.")
    else:
        # Display threats in reverse chronological order
        for threat in reversed(list(threat_queue)):
            with st.container():
                st.markdown(f"""
                <div class="threat-box">
                    <h4>⚠️ Threat Detected</h4>
                    <p><strong>PID:</strong> {threat['pid']}</p>
                    <p><strong>Type:</strong> {threat['threat_type']}</p>
                    <p><strong>Time:</strong> {threat['timestamp']}</p>
                    <p><strong>Status:</strong> {'🔍 Analyzed' if threat.get('analyzed') else '⏳ Pending Analysis'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # AI Analysis button
                if not threat.get('analyzed') and v1_analyst_model:
                    if st.button(f"🤖 Analyze Threat (PID {threat['pid']})", key=f"analyze_{threat['pid']}"):
                        with st.spinner("Analyzing with AI (trying FREE models first)..."):
                            try:
                                alert_data = {
                                    "process_id": threat['pid'],
                                    "process_name": threat['threat_type'],
                                    "command_line": " ".join(threat['cmdline']),
                                    "timestamp": threat['timestamp']
                                }
                                
                                analyst_prompt = f"""You are a V1 security analyst. Analyze this threat:
{json.dumps(alert_data, indent=2)}

Provide a brief human-readable summary (2-3 sentences)."""
                                
                                # Use waterfall AI (tries OpenRouter models first if enabled)
                                if USE_OPENROUTER:
                                    analysis_result, model_used = waterfall_ai_call(analyst_prompt, is_expert=False)
                                    st.success(f"✅ AI Analysis Complete! (Model: {model_used})")
                                    st.markdown(f"**Analysis:** {analysis_result}")
                                else:
                                    # Fallback to Gemini
                                    response = gemini_flash_model.generate_content(analyst_prompt)
                                    st.success("✅ AI Analysis Complete! (Model: Gemini Flash)")
                                    st.markdown(f"**Analysis:** {response.text}")
                                
                                threat['analyzed'] = True
                                
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")

with col2:
    st.subheader("📊 System Stats")
    st.metric("Active Threats", len(threat_queue))
    st.metric("Sentry Status", "🟢 Active" if sentry_active.is_set() else "🔴 Stopped")
    st.metric("Detected PIDs", len(detected_pids))
    
    st.markdown("---")
    st.markdown("### 🎯 Quick Actions")
    if st.button("🗑️ Clear Threat Queue", use_container_width=True):
        with threat_lock:
            threat_queue.clear()
            detected_pids.clear()
        st.success("Queue cleared!")
        st.rerun()

# Footer
st.markdown("---")

# --- MCP SECURITY SCAN TAB ---
with st.expander("🔍 **MCP Security Scan** - Test URL Security", expanded=False):
    if not MCP_AVAILABLE:
        st.error("❌ MCP Testbench module not available. Please install dependencies.")
    else:
        st.markdown("""
        ### 🔍 On-Demand Security Scan
        Enter a URL to test its security against the **Model Context Protocol (MCP) Testbench**.
        This will run automated security tests and provide a comprehensive security score.
        """)
        
        col1_scan, col2_scan = st.columns([3, 1])
        with col1_scan:
            scan_url = st.text_input(
                "Target URL", 
                placeholder="e.g., http://localhost:8000 or https://example.com",
                help="Enter the URL you want to scan for security vulnerabilities"
            )
        with col2_scan:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            scan_button = st.button("🚀 Start Scan", type="primary", use_container_width=True)
        
        if scan_button:
            if not scan_url:
                st.error("❌ Please enter a target URL")
            else:
                # Normalize URL
                if not scan_url.startswith('http://') and not scan_url.startswith('https://'):
                    scan_url = 'http://' + scan_url
                
                st.info(f"🔍 Starting MCP security scan on: **{scan_url}**")
                
                with st.spinner("Running security tests... This may take a moment..."):
                    try:
                        # Run MCP scan
                        engine = TestEngine(base_url=scan_url)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        results = loop.run_until_complete(engine.run_all())
                        loop.close()
                        
                        score = compute_score(results)
                        # Convert score to int if it's a string
                        try:
                            score_num = int(score) if isinstance(score, str) else score
                        except (ValueError, TypeError):
                            score_num = 0
                        
                        # Display results
                        st.success(f"✅ Scan Complete!")
                        
                        # Score display
                        col_score1, col_score2 = st.columns(2)
                        with col_score1:
                            st.metric("🎯 Security Score", f"{score}/100", 
                                     delta="High" if score_num > 80 else ("Medium" if score_num > 50 else "Low"))
                        with col_score2:
                            st.metric("Target URL", scan_url)
                        
                        # Detailed results
                        st.markdown("### 📋 Detailed Scan Results")
                        
                        if isinstance(results, dict):
                            # Format results nicely
                            for key, value in results.items():
                                if key == "score":
                                    continue  # Already shown above
                                elif isinstance(value, dict):
                                    with st.expander(f"📦 {key.replace('_', ' ').title()}", expanded=True):
                                        st.json(value)
                                elif isinstance(value, list):
                                    with st.expander(f"📝 {key.replace('_', ' ').title()} ({len(value)} items)", expanded=False):
                                        st.json(value)
                                else:
                                    st.text(f"{key.replace('_', ' ').title()}: {value}")
                        else:
                            st.json(results)
                        
                        # Download results as JSON
                        st.download_button(
                            label="📥 Download Full Report (JSON)",
                            data=json.dumps(results, indent=2),
                            file_name=f"mcp_scan_{scan_url.replace('://', '_').replace('/', '_')}.json",
                            mime="application/json"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Scan failed: {str(e)}")
                        st.exception(e)

st.markdown("---")
st.caption("SentinelOneX V4.0 | Powered by Google Gemini 2.0 | Streamlit Dashboard")

# Auto-refresh mechanism
if auto_refresh:
    time.sleep(0.5)
    st.rerun()
