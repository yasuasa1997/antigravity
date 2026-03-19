@echo off
cd /d "%~dp0"
echo Installing dependencies...
pip install -r requirements.txt

echo Starting Data Collector...
start "Stock Data Collector" python collector.py

echo Starting Streamlit Dashboard...
streamlit run app.py
