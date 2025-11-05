import subprocess
import sys
import os

print("="*60)
print("SentinelOneX V4.0 - Simple Launcher")
print("="*60)
print()

# Set API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyCbAr_gNaWJABhjMvaxcXXFdHL7h8YDo8Q"

print("Starting DEFENDER on port 7861...")
print()
print("KEEP THIS WINDOW OPEN!")
print("Open browser to: http://127.0.0.1:7861")
print()
print("Press Ctrl+Break (NOT Ctrl+C) to stop")
print("="*60)
print()

# Run defender
try:
    subprocess.run([sys.executable, "v3_api_demo.py"], check=True)
except KeyboardInterrupt:
    print("\nShutting down...")
except Exception as e:
    print(f"\nError: {e}")
    input("Press Enter to exit...")
