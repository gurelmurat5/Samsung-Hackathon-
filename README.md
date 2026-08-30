Digital Zen-Coach 🧘

Video Link:https://drive.google.com/file/d/1Z_2GUm1c1COfqPED73HJkH-4FVrCAhWb/view?usp=sharing

Team:
Ayşe Sena Nasır
Kamber Can Şahin
Murat Gürel
Hayrettin Kaan Özsoy
Büşra Kabak

A Generative-AI powered digital well-being coach — a Streamlit prototype built for the Digital Addiction & Digital Well-Being Hackathon (28–30 August 2026).
What is this?
Digital Zen-Coach is a gentle, judgment-free check-in tool. A user describes the platform(s) they use, their daily hours, how it makes them feel, and a hobby they wish they had more time for. A Gemini-powered coach reflects this back as a structured, four-part action plan — never a diagnosis.
Prerequisites
●	Python 3.10 or later
●	A free Google Gemini API key from aistudio.google.com
●	pip (or another Python package manager)

Setup
1. Get the project files
If you received this project as a ZIP, extract it to a folder of your choice. If you're cloning from a Git repository instead:
git clone <your-repository-url>
cd <repository-folder>

2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

3. Install dependencies
pip install -r requirements.txt

4. Run the app
streamlit run app.py

Streamlit opens the app automatically at http://localhost:8501. If it doesn't, open that URL manually.
5. Configure your Gemini API key
1. In the running app, open the ⚙️ Setup panel in the left sidebar.
2. Paste your Gemini API key into the Google Gemini API key field — it is only kept for the current session and is never stored or logged.
3. Alternatively, set it as an environment variable before launching so the field is pre-filled:
export GOOGLE_API_KEY="your-api-key-here"    # macOS/Linux
set GOOGLE_API_KEY=your-api-key-here         # Windows
streamlit run app.py

Using the app
1. Select the app/platform(s) you'd like to focus on and your daily hours.
2. Optionally name another platform not in the list.
3. Choose how the habit makes you feel.
4. Name a hobby or offline activity you wish you had more time for.
5. Click ✨ Generate My Digital Well-Being Action Plan.
The app calls Gemini through a 3-tier fallback cascade (gemini-2.5-flash → gemini-2.5-flash-lite → gemini-3.5-flash) and displays your plan as four cards: Acknowledgment, Pattern Insight, Micro-Challenge, and Offline Alternative.
Safety notes
●	This is a well-being coaching prototype, not a medical device or diagnostic tool.
●	Crisis/self-harm language in any input field skips the AI call entirely and shows real crisis resources (988, 112, 911/999, findahelpline.com) instead.
●	Ordinary medical language (medication, illness, symptoms, etc.) skips the AI call and asks the user to consult a healthcare professional instead.

Troubleshooting
Issue	Fix
"That API key was rejected"	Double-check the key in the sidebar; regenerate it at aistudio.google.com if needed.
"None of the expected Gemini models are available"	Your API key/region may not have access to one of MODEL_CANDIDATES. Run the model-listing snippet shown in the app's error message to see which models your key can reach, then update MODEL_CANDIDATES in app.py.
Styling looks off	Hard-refresh the browser tab (Ctrl/Cmd+Shift+R) — Streamlit sometimes caches old CSS.

Project structure
.
├── app.py              # Streamlit application (UI, prompts, Gemini calls, safety gates)
├── requirements.txt    # Python dependencies
└── README.md            # This file

Disclaimer
Digital Zen-Coach is a hackathon prototype. It does not diagnose, treat, or replace professional medical or mental health care.
