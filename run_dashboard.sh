#!/bin/bash
echo "🚀 Iniciando Dashboard de FacturIA 2.0..."
cd ~/FacturIA-2.0
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q streamlit plotly pandas sqlalchemy 2>/dev/null
streamlit run src/dashboard/app.py
