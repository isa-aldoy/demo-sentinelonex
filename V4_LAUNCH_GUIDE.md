# 🎯 SentinelOneX V4.0 - Dual-Platform Demo Launch Guide

**Date:** November 4, 2025  
**Version:** V4.0 Professional Edition  
**Status:** ✅ Ready for Production Demo

---

## 🚀 Quick Start: Launch Both Applications

### Prerequisites
```powershell
# Verify Python environment is configured
cd c:\Users\isaal\demo-sentinelonex
.venv\Scripts\activate
pip install -r requirements.txt  # Ensure all deps installed
```

### Launch Attacker App (Port 7860)
```powershell
# Terminal 1: Start the Attacker Simulator
$env:GOOGLE_API_KEY="AIzaSyCbAr_gNaWJABhjMvaxcXXFdHL7h8YDo8Q"
python attack_app.py
# Opens at: http://127.0.0.1:7860
```

### Launch Defender App (Port 7861)
```powershell
# Terminal 2: Start the SOAR Platform
$env:GOOGLE_API_KEY="AIzaSyCbAr_gNaWJABhjMvaxcXXFdHL7h8YDo8Q"
python v3_api_demo.py
# Opens at: http://127.0.0.1:7861
```

---

## 🎬 Demo Script (5-10 minutes)

### Setup Phase (1 minute)
1. **Browser Setup:**
   - Open TWO browser windows side-by-side
   - Window 1 (Left): http://127.0.0.1:7860 (Attacker - RED THEME)
   - Window 2 (Right): http://127.0.0.1:7861 (Defender - BLUE THEME)

2. **Defender Prep:**
   - Ensure "Proactive Sentry Mode" is ACTIVE (should show "Sentry Active" on load)
   - Mission Control tab should be visible

### Attack Phase (3-5 minutes)
**Narration: "Watch what happens when an attacker launches a threat..."**

1. **In Attacker Window (Left):**
   - Select attack type: "Fileless Attack (PowerShell Cradle)"
   - Click "🚀 LAUNCH ATTACK" button
   - Show the "✅ ATTACK LAUNCHED" status with PID

2. **Simultaneously in Defender Window (Right):**
   - **WATCH** as Mission Control Log STREAMS in real-time:
     - `[SENTRY] ⚠️ THREAT DETECTED!`
     - `[1/5] Launching threat...`
     - `[2/5] THREAT DETECTED! PID: [xxx]`
     - `[3/5] Sending to V1 Analyst...`
     - `V1 Analyst report received.`
     - `[4/5] Sending to V3 Expert...`
     - `[SUCCESS] V3 Expert (gemini_pro) playbook received`
     - `[METRICS] Threat Score: 87/100 | Confidence: 95% | Severity: HIGH`

3. **Expand JSON Accordions (Optional):**
   - Click "📋 Expand V1 Analyst Report" to show human-readable analysis
   - Click "🎯 Expand V3 Expert Playbook" to show machine-readable remediation

4. **Approval Flow:**
   - When buttons appear: "✅ Approve Remediation Plan"
   - Click to show execution logs streaming
   - Watch as playbook executes with real remediation actions

### Advanced Demo (Optional, 2-3 minutes)

**Try Other Attack Types:**
- Go back to Attacker app
- Select "Registry Persistence" or "Network C2"
- Show different threat patterns trigger different playbooks

**Check Metrics:**
- In Defender app, go to "📊 Incident Metrics" tab
- Click "Refresh Metrics" to see:
  - Total incidents tracked
  - Success rates
  - Threat distribution analysis
  - Complete audit trail

**Voice Command POC:**
- In Defender app, go to "🎤 Voice Command" tab
- Record a voice message
- Click "Transcribe" to show AI voice-to-text capability

---

## 📊 What Each Component Does

### Attacker App (Port 7860)
```
🔴 RED THEME - Represents the Attacker
├── Select Attack Type (4 options)
├── Click "LAUNCH ATTACK"
├── Shows PID and status
└── Instructs to watch Defender tab
```

**Attack Types Available:**
1. Fileless Attack (PowerShell Cradle) - Most dramatic
2. Registry Persistence - Shows persistence mechanisms
3. File Staging - Shows lateral movement prep
4. Network C2 - Shows command-and-control

### Defender App (Port 7861)
```
🛡️ BLUE THEME - Represents the Defender (SOAR)
├── Mission Control Tab (HERO FEATURE)
│   ├── Live Analysis Stream (18 lines of LOG)
│   ├── Hidden Accordion: V1 Analyst Report
│   ├── Hidden Accordion: V3 Expert Playbook
│   ├── Approve/Deny Buttons (appear when ready)
│   └── Incident ID tracking
│
├── Proactive Sentry Mode Tab
│   ├── Shows autonomous monitoring
│   ├── Auto-detects threats
│   ├── Auto-remediation logs
│   └── Background threat detection
│
├── Security Scan Tab
│   └── URL security testing (existing)
│
├── Metrics & Audit Log Tab
│   ├── Live metrics dashboard
│   ├── Threat distribution analysis
│   ├── Approval/Denial statistics
│   └── Complete incident audit trail
│
└── Voice Command POC Tab
    ├── Audio recording from microphone
    ├── OpenRouter Whisper transcription
    ├── Text output display
    └── Future: Voice command integration
```

---

## 🔄 AI Model Waterfall (Resilience Feature)

**For Analyst (V1) - Summary:**
```
Gemini 2.5 Flash (Fast)
  ↓ (if fails)
Google Gemma 3 27B (Fallback)
  ↓ (if fails)
Meta Llama 4 Scout (Last resort)
  ↓ (if all fail)
Hardcoded Error Response
```

**For Expert (V3) - Playbook:**
```
Gemini 2.5 Pro (Best reasoning)
  ↓ (if fails)
DeepSeek Pro (Advanced reasoning)
  ↓ (if fails)
Gemini 2.5 Flash (Fast fallback)
  ↓ (if fails)
Google Gemma 3 27B (Last resort)
  ↓ (if all fail)
Hardcoded Fallback Playbook (Guaranteed working)
```

**What This Means:**
- ✅ App NEVER completely fails
- ✅ If one AI is down, another auto-takes over
- ✅ If all AIs down, hardcoded response keeps system working
- ✅ Perfect for "no single point of failure" demo

---

## 🎨 UI/UX Highlights

### Design Philosophy
1. **Separation of Concerns:** Attack and defense in different tabs/apps
2. **Hero Feature:** Mission Control Log is the star (not buried in accordions)
3. **Executive Simplicity:** Large, readable logs without jargon
4. **Professional Theme:** Soft blue (defender) vs. soft red (attacker)

### Key UI Elements

**Mission Control Log (HERO):**
```
[1/5] Launching threat...
[2/5] THREAT DETECTED! PID: 5432
[3/5] Sending to V1 Analyst...
V1 Analyst report received.
[4/5] Sending to V3 Expert...
[SUCCESS] V3 Expert (gemini_pro) playbook received
[METRICS] Threat Score: 87/100 | Confidence: 95% | HIGH
[5/5] AI plan generated. Awaiting human approval...
```

**Accordions (Optional Details):**
- `📋 Expand V1 Analyst Report` - Human-readable summary
- `🎯 Expand V3 Expert Playbook` - JSON structure for technical folks

**Approval Flow:**
```
✅ APPROVE REMEDIATION PLAN (Green)
❌ DENY PLAN (Red)
```

---

## 💡 What Makes This Impressive for Investors

### 1. **Visual Narrative**
- Two browsers side-by-side = "Attacker vs. Defender"
- Click = Attack triggers
- Watch = Real-time response streams live
- Approve = Threat neutralized

### 2. **Autonomous Defense**
- No manual intervention needed
- Sentry detects, analyzes, proposes, awaits approval
- Shows "intelligent security" not just rules

### 3. **Redundancy/Resilience**
- Waterfall AI ensures nothing ever fails
- "Even if major AI provider goes down, we keep working"
- Demonstrates enterprise-grade reliability

### 4. **Executive-Level Interface**
- No technical jargon
- Clear metrics (Threat Score, Confidence %, Severity)
- Incident IDs for compliance
- Audit trail for governance

### 5. **Proof of Concepts**
- Voice command tab shows "we can do voice too"
- Future-proof architecture
- Extensible design

---

## 🔧 Technical Stack Visible in Demo

**AI Models Used (Show in Log):**
```
V1 Analyst (Flash) → "gemini_pro" appears in log
V3 Expert (Pro) → "gemini_pro" appears in log
If failures → "deepseek_pro", "gemma_3", "llama_4_scout" auto-try
```

**Technologies Demonstrated:**
- ✅ Real process spawning (actual threat simulation)
- ✅ Background thread monitoring (Sentry)
- ✅ Dual AI models (Fast + Smart)
- ✅ Streaming UI (Generator-based Gradio)
- ✅ Fallback architecture (Resilience)
- ✅ Voice API integration (Future-ready)
- ✅ Metrics tracking (Compliance-ready)

---

## 📋 Demo Checklist

Before presenting:
- [ ] Both apps have Python environment activated
- [ ] API keys set: GOOGLE_API_KEY, OPENROUTER_KEY
- [ ] attack_app.py running on 7860
- [ ] v3_api_demo.py running on 7861
- [ ] Browser 1 (Attacker) open at 7860
- [ ] Browser 2 (Defender) open at 7861
- [ ] Proactive Sentry showing "Active"
- [ ] Network connection stable (for OpenRouter fallback)

---

## 🎯 Key Talking Points

**To Investors:**

"This is SentinelOneX - an AI-powered SOAR platform that demonstrates autonomous threat response.

On the left, we have an attacker launching a real PowerShell threat. On the right, our Sentry watches in real-time, detects the threat, analyzes it with cutting-edge AI, and proposes a remediation plan - all while the attacker is still launching.

What you're seeing is:
1. Real threat simulation
2. Autonomous detection (no manual alerts)
3. Dual AI analysis (fast Flash for humans, smart Pro for machines)
4. Waterfall resilience (if one AI fails, others take over)
5. Human approval gate (we don't automate everything)
6. Complete audit trail (compliance-ready)

This is enterprise-grade security orchestration. It's impressive, it's automated, and it never fails."

---

## 🚨 Troubleshooting

**Attacker app won't start:**
```
pip install gradio
```

**Defender app port conflict:**
```powershell
# Check if 7861 is in use
netstat -ano | findstr :7861
# Kill if needed
taskkill /PID [PID] /F
```

**AI models returning errors:**
- Check API keys are set
- Check network connection
- Check OpenRouter status (may have rate limits)

**Mission Control log not streaming:**
- Ensure Sentry is active in Defender app
- Try launching threat again
- Check browser console for errors (F12)

---

## 📁 Files

- `attack_app.py` - Attacker simulator (Port 7860, RED theme)
- `v3_api_demo.py` - SOAR platform (Port 7861, BLUE theme)
- This file - Demo guide
- `requirements.txt` - All dependencies
- `.venv/` - Python virtual environment

---

**Ready to impress! 🎉**

Questions? Check the terminal logs - they're verbose and helpful!
