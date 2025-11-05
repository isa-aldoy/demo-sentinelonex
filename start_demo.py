#!/usr/bin/env python3
"""
SentinelOneX V4.0 - Launcher Helper
Starts both apps in correct order
"""

import subprocess
import time
import sys
import os

def main():
    print("="*60)
    print("SentinelOneX V4.0 - Application Launcher")
    print("="*60)
    print()
    
    print("🔴 Starting ATTACKER app on port 7860...")
    print("   (This will open in a new Command Prompt window)")
    
    # Start attacker in new window
    attacker_cmd = f'start cmd /k "cd /d {os.getcwd()} && python attack_app.py"'
    subprocess.Popen(attacker_cmd, shell=True)
    
    print("✅ Attacker starting...")
    print()
    time.sleep(3)
    
    print("🛡️ Starting DEFENDER app on port 7861...")
    print("   (This will open in a new Command Prompt window)")
    
    # Start defender in new window
    defender_cmd = f'start cmd /k "cd /d {os.getcwd()} && set GOOGLE_API_KEY=AIzaSyCbAr_gNaWJABhjMvaxcXXFdHL7h8YDo8Q && python v3_api_demo.py"'
    subprocess.Popen(defender_cmd, shell=True)
    
    print("✅ Defender starting...")
    print()
    time.sleep(5)
    
    print("="*60)
    print("✅ Both apps should now be starting!")
    print("="*60)
    print()
    print("📱 Open these URLs in your browser:")
    print("   🔴 Attacker:  http://127.0.0.1:7860")
    print("   🛡️  Defender: http://127.0.0.1:7861")
    print()
    print("📋 Next steps:")
    print("   1. Wait 10-15 seconds for both apps to fully start")
    print("   2. Open Defender tab → Click 'Watch for Sentry Threats'")
    print("   3. Open Attacker tab → Click 'LAUNCH ATTACK'")
    print("   4. Watch real-time detection in Defender!")
    print()
    print("="*60)

if __name__ == "__main__":
    main()
