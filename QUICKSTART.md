# 🚀 Quick Start Guide - Smart Ambulance Pre-Arrival System

## ✅ System Status: READY

All components have been tested and are operational!

## 🎯 Running the Dashboard

### Option 1: Run with Demo Mode (No API Key Required)

The dashboard works with simulated data and doesn't require OpenAI for the demo:

```bash
streamlit run dashboard/er_dashboard.py
```

This will:
- Launch a real-time ER dashboard in your browser
- Show live vital signs monitoring with graphs
- Display critical alerts and warnings
- Demonstrate HIPAA-compliant PII redaction
- Show AI-style recommendations (pre-formatted for demo)

### Option 2: Run with Full AI Integration (Requires OpenAI API Key)

For full RAG-based AI analysis:

1. **Create .env file:**
```bash
cp .env.example .env
```

2. **Edit .env and add your OpenAI API key:**
```
OPENAI_API_KEY=sk-your-actual-key-here
```

3. **Run the dashboard:**
```bash
streamlit run dashboard/er_dashboard.py
```

## 🧪 Testing Individual Components

### Test Telemetry Simulator
Watch simulated vital signs for 20 seconds:
```bash
python simulators/telemetry_simulator.py
```

### Test EMT Voice Notes
See voice notes with PII:
```bash
python simulators/emt_voice_simulator.py
```

### Test PII Redaction
Verify HIPAA compliance:
```bash
python utils/pii_redactor.py
```

### Run Full System Test
```bash
python test_system.py
```

## 📊 What You'll See in the Dashboard

1. **Real-Time Vital Signs Monitor**
   - Live graphs showing Heart Rate, SpO2, and Blood Pressure
   - Updates every 2 seconds
   - Historical trend visualization

2. **Critical Alerts**
   - CODE BLUE PREP for critical conditions
   - WARNING for abnormal vitals
   - Color-coded severity levels

3. **EMT Voice Notes**
   - Automatically redacted for HIPAA compliance
   - Names → [PATIENT]
   - SSN → [SSN-REDACTED]
   - Other PII masked

4. **AI Recommendations**
   - Suspected diagnosis
   - Preparation steps for ER team
   - Protocol-based recommendations
   - Time-sensitive actions

5. **Patient Status**
   - Current metrics
   - ETA countdown
   - Severity indicators

## 🎬 Demo Scenario

The system simulates a **Myocardial Infarction (MI)** patient:
- 58-year-old female with chest pain
- History of angina and hypertension
- Critical vitals: tachycardia, hypotension, low SpO2
- Transport time: ~8 minutes
- Expected outcome: CODE BLUE PREP alert + Catheter Lab activation

## 🛑 Stopping the Dashboard

Press `Ctrl+C` in the terminal to stop the Streamlit server.

## 📝 Project Structure

```
Hackathon Project/
├── dashboard/
│   └── er_dashboard.py          # Main dashboard UI
├── simulators/
│   ├── telemetry_simulator.py   # Vital signs simulator
│   └── emt_voice_simulator.py   # Voice notes simulator
├── pipeline/
│   └── ambulance_pipeline.py    # Pathway processing pipeline
├── utils/
│   └── pii_redactor.py          # HIPAA PII redaction
├── data/
│   └── hospital_protocols.txt   # ER protocols for RAG
└── test_system.py               # System verification tests
```

## 🔧 Troubleshooting

**Issue: "ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

**Issue: PII redaction not working**
```bash
python -m spacy download en_core_web_lg
```

**Issue: Dashboard won't start**
- Check if port 8501 is available
- Try: `streamlit run dashboard/er_dashboard.py --server.port 8502`

## 🎓 Key Features Demonstrated

✅ **Real-time data streaming** with Pathway framework  
✅ **Dual stream processing** (telemetry + voice)  
✅ **Critical alerting system** with threshold monitoring  
✅ **HIPAA-compliant PII redaction** using Presidio  
✅ **RAG-based protocol analysis** (when OpenAI configured)  
✅ **Interactive ER dashboard** with Streamlit  
✅ **Live visualization** with Plotly charts  

## 📞 Next Steps

1. Run the dashboard: `streamlit run dashboard/er_dashboard.py`
2. Watch the simulated ambulance scenario
3. Observe the critical alerts trigger
4. See PII redaction in action
5. Review AI recommendations

## 💡 Hackathon Highlights

This project demonstrates:
- **Pathway Framework** for real-time stream processing
- **Pathway LLM xPack** integration (ready for RAG)
- **Emergency medicine workflow** optimization
- **Data privacy** in healthcare applications
- **AI-assisted decision making** for critical care

---

**Ready to launch? Run:** `streamlit run dashboard/er_dashboard.py`
