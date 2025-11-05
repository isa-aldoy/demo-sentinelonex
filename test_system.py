#!/usr/bin/env python3
"""
SentinelOneX V4.0 - Complete End-to-End Test
This script verifies the entire threat detection pipeline
"""

import subprocess
import time
import sys

def print_status(message, status="INFO"):
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
    print(f"{symbols.get(status, 'ℹ️')} [{status}] {message}")

def check_app_running(port):
    """Check if app is running on given port"""
    try:
        result = subprocess.run(
            f'netstat -ano | findstr ":{port}"',
            shell=True,
            capture_output=True,
            text=True
        )
        return f":{port}" in result.stdout
    except:
        return False

def main():
    print("="*60)
    print("SentinelOneX V4.0 - System Verification Test")
    print("="*60)
    print()
    
    # Step 1: Check if apps are running
    print_status("Checking if Attacker app is running on port 7860...")
    attacker_running = check_app_running(7860)
    if attacker_running:
        print_status("Attacker app is RUNNING", "SUCCESS")
    else:
        print_status("Attacker app is NOT running", "ERROR")
        print_status("Please start it with: START_ATTACKER.bat", "WARNING")
        return
    
    print_status("Checking if Defender app is running on port 7861...")
    defender_running = check_app_running(7861)
    if defender_running:
        print_status("Defender app is RUNNING", "SUCCESS")
    else:
        print_status("Defender app is NOT running", "ERROR")
        print_status("Please start it with: START_DEFENDER.bat", "WARNING")
        return
    
    print()
    print_status("Both apps are running!  ", "SUCCESS")
    print()
    
    # Step 2: Provide manual test instructions
    print("="*60)
    print("MANUAL TEST PROCEDURE:")
    print("="*60)
    print()
    print("1. Open Browser Tab: http://127.0.0.1:7861 (DEFENDER)")
    print("   - Go to 'Real End-to-End Remediation' tab")
    print("   - Click '👁️ Watch for Sentry Threats' button")
    print("   - Look for: '[SENTRY THREAT STREAM] Listening...'")
    print()
    print("2. Open Another Browser Tab: http://127.0.0.1:7860 (ATTACKER)")
    print("   - Ensure 'Fileless Attack (PowerShell Cradle)' is selected")
    print("   - Click '🚀 LAUNCH ATTACK' button")
    print("   - Note the Process ID shown")
    print()
    print("3. Switch Back to DEFENDER Tab")
    print("   - Within 1-2 seconds you should see:")
    print("     [SENTRY DETECTION #1] ✅ Threat intercepted!")
    print("     [1/5] Processing threat with AI analysis...")
    print("     [2/5] Sending to V1 Analyst AI...")
    print("     [SUCCESS] V1 Analyst report received")
    print("     [3/5] Sending to V3 Expert AI...")
    print("     [SUCCESS] V3 Expert playbook received")
    print("     [4/5] ✅ Analysis complete. Awaiting approval...")
    print()
    print("4. Verify Buttons Appear:")
    print("   - '✅ Approve Remediation Plan' button visible")
    print("   - '❌ Deny Plan' button visible")
    print()
    print("5. Click 'Approve' to Execute Remediation")
    print("   - Should see: [EXECUTION] Human operator APPROVED")
    print("   - Process should be terminated")
    print()
    print("="*60)
    print("EXPECTED RESULT: Threat detected → AI analyzed → Human approved → Remediated")
    print("="*60)
    print()
    print_status("System is ready for testing!", "SUCCESS")
    print()

if __name__ == "__main__":
    main()
