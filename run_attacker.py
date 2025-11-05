import subprocess
import sys

print("="*60)
print("SentinelOneX V4.0 - Attacker Launcher")
print("="*60)
print()
print("Starting ATTACKER on port 7860...")
print()
print("KEEP THIS WINDOW OPEN!")
print("Open browser to: http://127.0.0.1:7860")
print()
print("Press Ctrl+Break (NOT Ctrl+C) to stop")
print("="*60)
print()

# Run attacker
try:
    subprocess.run([sys.executable, "attack_app.py"], check=True)
except KeyboardInterrupt:
    print("\nShutting down...")
except Exception as e:
    print(f"\nError: {e}")
    input("Press Enter to exit...")
