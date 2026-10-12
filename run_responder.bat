@echo off
cd /d "%~dp0"
pip install google-genai python-dotenv --quiet
python auto_responder.py
pause