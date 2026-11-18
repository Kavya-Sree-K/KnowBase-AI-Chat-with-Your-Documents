"""
ui_styles.py - the custom CSS for the Streamlit app, kept out of app.py
so the main file stays readable.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Inter:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: radial-gradient(circle at 20% 20%, #1b1035 0%, #0d0d1f 45%, #06060f 100%); color: #e8e8f5; }
.gradient-title {
    font-family: 'Poppins', sans-serif; font-size: 2.6rem; font-weight: 700;
    background: linear-gradient(90deg, #8e6bff, #ff6bcb, #6bd4ff);
    background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    animation: shine 6s linear infinite; margin-bottom: 0;
}
@keyframes shine { to { background-position: 200% center; } }
.subtitle { color: #a7a7c9; margin-top: -8px; margin-bottom: 1.2rem; }
.bubble-user, .bubble-bot {
    padding: 14px 18px; border-radius: 16px; margin: 8px 0; max-width: 90%;
    line-height: 1.5; box-shadow: 0 4px 18px rgba(0,0,0,0.25);
}
.bubble-user { background: linear-gradient(135deg, #6b4bff, #9b6bff); color: white;
    margin-left: auto; border-bottom-right-radius: 4px; }
.bubble-bot { background: rgba(255,255,255,0.06); backdrop-filter: blur(6px);
    border: 1px solid rgba(255,255,255,0.08); margin-right: auto; border-bottom-left-radius: 4px; }
.score-bar-bg { background: rgba(255,255,255,0.08); border-radius: 6px; height: 8px; width: 100%; }
.score-bar-fill { background: linear-gradient(90deg,#8e6bff,#6bd4ff); height: 8px; border-radius: 6px; }
.hist-btn button { text-align: left !important; white-space: normal !important;
    background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.06) !important;
    color: #dcdcff !important; border-radius: 10px !important; margin-bottom: 4px !important; }
.hist-btn button:hover { background: rgba(139,107,255,0.18) !important; }
</style>
"""
