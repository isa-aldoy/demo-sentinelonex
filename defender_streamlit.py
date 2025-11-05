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

# Google Gemini API
import google.generativeai as genai
import os

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    v1_analyst_model = genai.GenerativeModel('gemini-2.0-flash')
    v3_expert_model = genai.GenerativeModel('gemini-2.0-pro')
else:
    v1_analyst_model = None
    v3_expert_model = None

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
                        with st.spinner("Analyzing with Gemini AI..."):
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
                                
                                response = v1_analyst_model.generate_content(analyst_prompt)
                                st.success("✅ AI Analysis Complete!")
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
st.caption("SentinelOneX V4.0 | Powered by Google Gemini 2.0 | Streamlit Dashboard")

# Auto-refresh mechanism
if auto_refresh:
    time.sleep(0.5)
    st.rerun()
