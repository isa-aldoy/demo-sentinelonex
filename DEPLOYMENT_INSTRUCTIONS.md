# SentinelOneX V4.0 - Deployment Instructions

## 🚀 Quick Start (FIXED VERSION)

### Critical Fixes Applied:
1. ✅ **Auto-start Sentry**: Sentry monitoring now activates automatically on app launch
2. ✅ **Fixed async bug**: Security scan no longer crashes the app
3. ✅ **Continuous monitoring**: No more 60-second timeout - runs until threat detected

---

## Step-by-Step Deployment

### 1. Open TWO PowerShell Windows

**Window 1 - Attacker App:**
```powershell
cd c:\Users\isaal\demo-sentinelonex
python attack_app.py
```
Wait for: `* Running on local URL:  http://127.0.0.1:7860`

**Window 2 - Defender App:**
```powershell
cd c:\Users\isaal\demo-sentinelonex
$env:GOOGLE_API_KEY="AIzaSyCbAr_gNaWJABhjMvaxcXXFdHL7h8YDo8Q"
python v3_api_demo.py
```
Wait for: `[DEFENDER APP] ✅ Sentry monitoring ACTIVE`

---

### 2. Open TWO Browser Tabs

**Tab 1 - Attacker:** http://127.0.0.1:7860 (Red theme)
**Tab 2 - Defender:** http://127.0.0.1:7861 (Blue theme)

---

### 3. Test Threat Detection

#### On Defender Tab (http://127.0.0.1:7861):
1. Go to **"Real End-to-End Remediation"** tab
2. Click **"👁️ Watch for Sentry Threats"** button
3. You should see: `[SENTRY THREAT STREAM] 🔄 Listening for Sentry-detected threats...`

#### On Attacker Tab (http://127.0.0.1:7860):
1. Ensure "Fileless Attack (PowerShell Cradle)" is selected
2. Click **"🚀 LAUNCH ATTACK"**
3. Note the Process ID that appears

#### Back to Defender Tab:
**Within 1-2 seconds**, you should see:
```
[SENTRY DETECTION #1] ✅ Threat intercepted by Sentry!
[SENTRY] PID: 12345
[SENTRY] Type: powershell.exe
[1/5] Processing threat with AI analysis...
[2/5] Sending to V1 Analyst AI...
[SUCCESS] V1 Analyst (google_gemma) report received.
[3/5] Sending to V3 Expert AI...
[SUCCESS] V3 Expert (deepseek_expert) playbook received.
[4/5] ✅ Analysis complete. Awaiting human approval...
```

The **"✅ Approve Remediation Plan"** and **"❌ Deny Plan"** buttons will appear.

---

## 🎯 What Was Fixed

### Issue #1: Sentry Not Running
**BEFORE:** User had to manually click "Activate Sentry" in the "Proactive Sentry Mode" tab
**AFTER:** Sentry auto-starts when v3_api_demo.py launches
**Code Change:** Added auto-start in `__main__` section

### Issue #2: Threats Not Showing in UI
**BEFORE:** 60-second timeout caused monitoring to stop before threats appeared
**AFTER:** Continuous polling until threat detected
**Code Change:** Removed timeout loop in `sentry_threat_stream()`

### Issue #3: App Crashes During Security Scan
**BEFORE:** Async function called from sync context caused TypeError
**AFTER:** Proper async/sync wrapper with event loop
**Code Change:** Fixed `run_security_scan()` to handle async properly

---

## 🔍 Troubleshooting

### "Port already in use" error:
```powershell
Get-Process python | Stop-Process -Force
Start-Sleep -Seconds 2
# Then restart apps
```

### Threats not detected:
1. Check PowerShell window for `[SENTRY] ⚠️ THREAT DETECTED!` message
2. Verify "Watch for Sentry Threats" button was clicked
3. Ensure attack was launched AFTER clicking watch button

### AI models failing:
- Check internet connection (OpenRouter API required)
- Verify API keys in code (Gemini + OpenRouter)
- Models fallback: DeepSeek → Gemma → Llama → MiniMax → Gemini

---

## 📊 Expected Console Output

### Defender App Console (v3_api_demo.py):
```
[DEFENDER APP] Starting on port 7861...
[DEFENDER APP] Auto-activating Sentry monitoring...
[SENTRY] Sentry thread activated. Monitoring processes...
[DEFENDER APP] ✅ Sentry monitoring ACTIVE
* Running on local URL:  http://127.0.0.1:7861

[SENTRY] ⚠️  THREAT DETECTED! PID: 12345 | Type: powershell.exe
[SENTRY] 📤 Added to threat queue for analysis
[SENTRY] ✅ Auto-remediated threat (PID 12345)
[STREAM] Threat #1 found in queue! {'pid': 12345, ...}
[WATERFALL] Attempting google_gemma...
[WATERFALL] ✅ google_gemma succeeded
```

### Attacker App Console (attack_app.py):
```
[ATTACKER APP] Starting on port 7860...
* Running on local URL:  http://127.0.0.1:7860

[ATTACKER] Launching PowerShell cradle threat...
[ATTACKER] ✅ Threat launched! PID: 12345
```

---

## 🎬 Demo Flow for Presentations

1. **Pre-show:** Both apps running, browser tabs open
2. **Intro:** "This is a dual-platform threat simulation..."
3. **Action:** Click "Watch for Sentry Threats" on Defender
4. **Attack:** Click "LAUNCH ATTACK" on Attacker
5. **Show:** Real-time detection streaming in Mission Control
6. **Analysis:** AI generates threat report (expand accordions)
7. **Decision:** Click "Approve" to execute remediation
8. **Metrics:** Show Incident Metrics & Audit Log tab

---

## 🛡️ Architecture Summary

```
ATTACKER (7860) → Launches PowerShell threat
    ↓
SENTRY (background thread) → Monitors via psutil every 1 second
    ↓
THREAT QUEUE (thread-safe) → Stores detected threats
    ↓
UI STREAM (sentry_threat_stream) → Polls queue continuously
    ↓
AI WATERFALL (4-5 models) → Gemma/DeepSeek/Llama/MiniMax/Gemini
    ↓
PLAYBOOK GENERATION → JSON remediation plan
    ↓
HUMAN APPROVAL → Approve/Deny buttons
    ↓
EXECUTION → Real taskkill commands
```

---

## ✅ Verification Checklist

- [ ] Both PowerShell windows open and apps running
- [ ] Attacker app shows red theme
- [ ] Defender app shows blue theme
- [ ] Console shows `[DEFENDER APP] ✅ Sentry monitoring ACTIVE`
- [ ] "Watch for Sentry Threats" button clicked
- [ ] Attack launched from Attacker tab
- [ ] Threat appears in Mission Control log within 2 seconds
- [ ] AI analysis completes successfully
- [ ] Approve/Deny buttons visible
- [ ] Clicking Approve terminates the process

---

## 🎯 Success Criteria

**The demo is working correctly when:**
1. Launching an attack shows PID in Attacker tab
2. Within 1-2 seconds, Defender log shows `[SENTRY DETECTION #1]`
3. AI analysis runs through all 5 steps
4. Approve button appears
5. Clicking Approve shows `[EXECUTION] Human operator APPROVED`
6. Process is terminated (check Task Manager - PID gone)

---

**Demo is now ready for investor presentations! 🚀**
