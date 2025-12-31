import os
import json
import time
import re
import base64
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Import for secure password hashing
from werkzeug.security import generate_password_hash, check_password_hash

import streamlit as st
from retell import Retell

# ==============================
# ENV / CREDENTIALS
# ==============================
ADMIN_EMAIL = os.getenv("ASPECT_ADMIN_EMAIL", "Alex.Bacon@aspect.co.uk")
ADMIN_PASSWORD = os.getenv("ASPECT_ADMIN_PASSWORD", "Alex.Bacon#123")

# --- USER STORAGE ---
USERS_FILE = Path("users.json")

# --- API KEY & AGENT CONFIGURATION ---
FROM_NUMBER = os.getenv("RETELL_FROM_NUMBER", "+441479787918")

# --- AGENT CONFIGURATION ---
CHAIN_START_AGENT_IDS = {
    "Female Voice Start": os.getenv("RETELL_AGENT_ID_FEMALE", "agent_c3f46c38e6348846dc844fe9d1"), # Agent with Amy's voice
    "Male Voice Start": os.getenv("RETELL_AGENT_ID_MALE", "agent_adbd2014e4adf09638ffa0f5f6"),   # Agent with Anthony's voice
}

# Agent ID specifically for post-call evaluation and scoring
EVALUATION_AGENT_ID = os.getenv("RETELL_EVALUATION_AGENT_ID", "agent_aa0cc8b0f8cd9dcb7d797acac9")


# --- Branding / Footer ---
COMPANY_NAME = os.getenv("ASPECT_COMPANY_NAME", "Aspect Maintenance Services Ltd.")
SUPPORT_EMAIL = os.getenv("ASPECT_SUPPORT_EMAIL", "support@aspect.co.uk")
SUPPORT_PHONE = os.getenv("ASPECT_SUPPORT_PHONE", "+44 20 1234 5678")

# --- Logo ---
LOGO_FILE = Path("images.png")

# =================================
# PAGE CONFIG
# =================================
st.set_page_config(
    page_title="Aspect Training Portal",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =================================
# COMPANY UI - CUSTOM CSS THEME
# =================================
st.markdown("""
<style>
    /* Your Company Theme Variables */
    :root {
        --color-primary: #27549D;      /* Main brand blue */
        --color-background: #f7f9fd;  /* Light page background */
        --color-secondary: #7099DB;   /* Lighter blue for gradients/accents */
        --color-accent: #F1FF24;      /* Bright yellow for highlights */
        --color-light-grey: #FFFFFF4D; /* Transparent white */
        --text-main: #1f2937;         /* Primary text color */
        --text-muted: #6b7280;        /* Muted text color */
        --card-bg: #ffffff;           /* Card background */
        --border: #e5e7eb;            /* Border color */
        --success: #22c55e;
        --error: #ef4444;
        --warning: #f59e0b;
    }
    
    /* General Body Styling */
    .stApp {
        background-color: var(--color-background);
        color: var(--text-main); /* Using a standard dark text for better readability */
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    }
    a {
        text-decoration: none;
        color: var(--color-primary);
        cursor: pointer;
    }
    
    /* Hero Header */
    .hero {
        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        border-radius: 18px;
        padding: 1.8rem;
        color: #fff;
        box-shadow: 0 18px 40px rgba(39, 84, 157, 0.2);
        margin: 1.2rem 0;
        display: flex;
        align-items: center;
    }
    .hero img {
        height: 50px;
        margin-right: 20px;
        border-radius: 8px;
    }
    .hero h1 { margin: 0; font-size: 2.2rem; font-weight: 800; letter-spacing: .2px; }
    .hero p { margin: .35rem 0 0 0; opacity: .95; font-weight: 500; }
    
    /* Cards and Panels */
    .card, .panel {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.06);
        transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
    }
    .panel {
        margin-top: 8px;
    }
    .card h3 { margin: 0 0 6px 0; font-weight: 800; color: var(--text-main); }
    
    /* Title Container */
    .title-container {
        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        padding: 2rem; border-radius: 18px; margin: 1.2rem auto 1.4rem auto;
        box-shadow: 0 16px 40px rgba(39, 84, 157, 0.25); max-width: 1100px; color:#fff;
    }
    .title-text { text-align: center; font-size: 2.4rem; font-weight: 800; margin: 0; letter-spacing: 0.5px; }
    .subtitle-text { color: rgba(255,255,255,0.92); text-align: center; font-size: 1rem; margin-top: 0.45rem; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
        color: white; border: none; border-radius: 999px; padding: 0.6rem 1.3rem;
        font-weight: 700; transition: all 0.2s ease; letter-spacing: .3px;
    }
    .stButton > button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 10px 24px rgba(39, 84, 157, 0.3); 
    }
    .stButton > button:disabled {
        background: #ccc;
        color: #888;
    }

    /* Score and Training Cards */
    .level-card {
        background: linear-gradient(135deg, var(--color-secondary) 0%, var(--color-primary) 100%);
        color: white; padding: 1rem; border-radius: 12px; margin: 1rem 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.18);
    }
    .score-card { 
        background: white; padding: 1rem; border-radius: 12px; margin: 0.5rem 0; 
        box-shadow: 0 2px 12px rgba(0,0,0,0.12); text-align: center; 
    }
    .score-card h2 {
        color: var(--color-primary);
    }
    .trainee-name-card {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white; padding: 1.1rem; border-radius: 14px; margin: .8rem 0 .6rem; text-align: center;
        box-shadow: 0 10px 24px rgba(0,0,0,0.22);
    }
    .trainee-name-text { font-size: 1.2rem; font-weight: 800; margin: 0; }
    
    /* Transcript Box */
    .transcript-box { background: white; padding: 1rem; border-radius: 12px; max-height: 420px; overflow-y: auto; margin: 1rem 0; }
    .customer-msg { color: #e74c3c; font-weight: 700; }
    .trainee-msg { color: var(--color-primary); font-weight: 700; }
    
    /* Misc */
    .muted { color: var(--text-muted); font-size: .95rem; line-height: 1.4; }
    .footer {
        margin-top: 32px;
        padding: 24px 12px;
        text-align: center;
        color: var(--text-muted);
        border-top: 1px solid var(--border);
    }
    .footer a { color: var(--color-primary); text-decoration: none; font-weight: 600; }
    /* Change progress bar color to brand color */
    .stProgress > div > div > div > div {
        background-color: var(--color-secondary);
    }
</style>
""", unsafe_allow_html=True)

# =========================
# AUTH STATE & HELPERS
# =========================
if "auth_role" not in st.session_state:
    st.session_state.auth_role = None
if "auth_email" not in st.session_state:
    st.session_state.auth_email = None
if "auth_name" not in st.session_state:
    st.session_state.auth_name = None

def load_users() -> Dict:
    """Loads the user database from a JSON file."""
    if not USERS_FILE.exists():
        initial_admin = {
            ADMIN_EMAIL.lower(): {
                "name": "Admin",
                "password_hash": generate_password_hash(ADMIN_PASSWORD),
                "role": "admin"
            }
        }
        with open(USERS_FILE, "w") as f:
            json.dump(initial_admin, f, indent=4)
        return initial_admin
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users: Dict):
    """Saves the user database to a JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


# ==============
# RETELL CLIENT
# ==============
@st.cache_resource
def init_retell():
    if not RETELL_API_KEY:
        st.error("❌ RETELL_API_KEY is missing!")
        st.stop()
    try:
        client = Retell(api_key=RETELL_API_KEY)
        return client
    except Exception as e:
        st.error(f"❌ Error initializing Retell client: {e}")
        st.stop()

# ===========================
# UI & LOGIN HELPERS
# ===========================
def get_logo_base64(logo_file: Path) -> Optional[str]:
    """Reads a logo file and returns its base64 encoded string."""
    if logo_file.is_file():
        try:
            with open(logo_file, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode("utf-8")
        except Exception:
            return None
    return None

def render_logo_header():
    """Renders the main header with logo and company name."""
    logo_b64 = get_logo_base64(LOGO_FILE)
    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="{COMPANY_NAME} Logo">'
    
    st.markdown(
        f"""
        <div class='hero'>
            {logo_html}
            <div>
                <h1>{COMPANY_NAME}</h1>
                <p>Training & Evaluation Portal</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def email_valid(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))

def mask_email(email: str) -> str:
    try:
        name, domain = email.split("@")
        if len(name) <= 2: name_mask = name[0] + "•"
        else: name_mask = name[0] + "•"*(len(name)-2) + name[-1]
        domain_parts = domain.split(".")
        domain_mask = domain_parts[0][0] + "•"*(len(domain_parts[0])-1)
        return f"{name_mask}@{domain_mask}.{'.'.join(domain_parts[1:])}"
    except Exception:
        return email

def success_card(title: str, subtitle: str = "", details: str = ""):
    st.markdown(
        f"""
        <div class="panel" style="border-left: 4px solid var(--success);">
            <h3 style="margin:0 0 4px 0;">{title}</h3>
            <div class="muted">{subtitle}</div>
            <div style="margin-top:8px;">{details}</div>
        </div>
        """, unsafe_allow_html=True
    )

def error_card(title: str, subtitle: str = "", details: str = ""):
    st.markdown(
        f"""
        <div class="panel" style="border-left: 4px solid var(--error);">
            <h3 style="margin:0 0 4px 0;">{title}</h3>
            <div class="muted">{subtitle}</div>
            <div style="margin-top:8px;">{details}</div>
        </div>
        """, unsafe_allow_html=True
    )

def warn_card(title: str, subtitle: str = "", details: str = ""):
    st.markdown(
        f"""
        <div class="panel" style="border-left: 4px solid var(--warning);">
            <h3 style="margin:0 0 4px 0;">{title}</h3>
            <div class="muted">{subtitle}</div>
            <div style="margin-top:8px;">{details}</div>
        </div>
        """, unsafe_allow_html=True
    )


# ===========================
# UNIFIED LOGIN SYSTEM
# ===========================
def render_login_screen():
    render_logo_header()
    login_tab, signup_tab = st.tabs(["**Sign In**", "**Create Account**"])

    with login_tab:
        st.markdown("### Sign In to Your Account")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email address")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In")
        if submitted:
            if not email_valid(email):
                error_card("Invalid email", details="Please enter a valid email address.")
                return
            if not password:
                error_card("Password required", details="Please enter your password.")
                return

            with st.spinner("Authenticating..."):
                time.sleep(0.5)
                users = load_users()
                user_email_lower = email.strip().lower()

                if user_email_lower not in users:
                    error_card("Email not recognized", details="This email is not registered in the system.")
                    return

                user_data = users[user_email_lower]
                if not check_password_hash(user_data.get("password_hash", ""), password):
                    error_card("Invalid credentials", details="The password you entered is incorrect.")
                    return

                st.session_state.auth_role = user_data["role"]
                st.session_state.auth_email = user_email_lower
                st.session_state.auth_name = user_data["name"]
                
                welcome_title = f"Welcome back, {user_data['name']}!"
                if user_data["role"] == "admin":
                    welcome_title = f"Admin access granted for {user_data['name']}"
                    
                success_card(welcome_title, f"Signed in as {mask_email(user_email_lower)}")
                st.rerun()

    with signup_tab:
        st.markdown("### Create a New Trainee Account")
        
        msg_placeholder = st.empty() 
        
        with st.form("create_user_form", clear_on_submit=True):
            new_name = st.text_input("Full Name (Trainee Name)")
            new_email = st.text_input("Email (this will be your username)")
            new_password = st.text_input("Create a Password", type="password")
            create_user_submitted = st.form_submit_button("Create Account")

        if create_user_submitted:
            if not all([new_name, new_email, new_password]):
                msg_placeholder.error("All fields are required.") 
            elif not email_valid(new_email):
                msg_placeholder.error("Please enter a valid email address.")
            else:
                users = load_users()
                if new_email.lower() in users:
                    msg_placeholder.error("An account with this email already exists. Please Sign In instead.")
                else:
                    users[new_email.lower()] = {
                        "name": new_name.strip(),
                        "password_hash": generate_password_hash(new_password),
                        "role": "user"
                    }
                    save_users(users)
                    msg_placeholder.success(f"Account for '{new_name}' created! You can now sign in using the 'Sign In' tab.")


# ===========================
# EVALUATION PARSING HELPERS
# ===========================
def extract_structured_evaluation(evaluation_data: Any) -> Optional[Dict[str, Any]]:
    def parse_text_scores(text: str) -> Dict[str, float]:
        scores = {}
        patterns = [
            r'Product Knowledge[:\s]+(\d+(?:\.\d+)?)', r'Costs?\s*(?:&|and)?\s*Booking[:\s]+(\d+(?:\.\d+)?)',
            r'Tone\s*(?:of)?\s*Voice[:\s]+(\d+(?:\.\d+)?)', r'Objection\s*Handling[:\s]+(\d+(?:\.\d+)?)',
            r'Call\s*Control\/Flow[:\s]+(\d+(?:\.\d+)?)'
        ]
        score_keys = ['product_knowledge', 'costs_booking', 'tone_voice', 'objection_handling', 'call_control']
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try: scores[score_keys[i]] = float(match.group(1))
                except (ValueError, IndexError): pass
        json_match = re.search(r'\{[^}]*"product_knowledge"[^}]*\}', text, re.IGNORECASE | re.DOTALL)
        if json_match:
            try: scores.update(json.loads(json_match.group()))
            except json.JSONDecodeError: pass
        return scores
    def validate_scores(scores: Dict[str, float]) -> Dict[str, float]:
        validated = {}
        for key, value in scores.items():
            if isinstance(value, (int, float)):
                if value > 10: value = value / 10 if value <= 100 else 10
                validated[key] = max(0, min(10, float(value)))
        return validated
    text_to_parse = ""
    temp_eval_data = evaluation_data
    if isinstance(temp_eval_data, str):
        try: temp_eval_data = json.loads(temp_eval_data)
        except json.JSONDecodeError: text_to_parse = temp_eval_data
    if not text_to_parse and isinstance(temp_eval_data, dict):
        if 'detailed_feedback' in temp_eval_data and isinstance(temp_eval_data['detailed_feedback'], str):
            text_to_parse = temp_eval_data['detailed_feedback']
        elif 'Evaluation Score' in temp_eval_data and isinstance(temp_eval_data['Evaluation Score'], str):
            text_to_parse = temp_eval_data['Evaluation Score']
        elif 'evaluation' in temp_eval_data and isinstance(temp_eval_data['evaluation'], str):
            text_to_parse = temp_eval_data['evaluation']
    if not text_to_parse: text_to_parse = str(evaluation_data)
    parsed_scores = parse_text_scores(text_to_parse)
    if isinstance(temp_eval_data, dict):
        if 'evaluation_score' in temp_eval_data and isinstance(temp_eval_data['evaluation_score'], dict):
            parsed_scores.update(temp_eval_data['evaluation_score'])
        fields = ['product_knowledge', 'costs_booking', 'tone_voice', 'objection_handling', 'call_control']
        if any(f in temp_eval_data for f in fields):
            structured_scores = {f: temp_eval_data.get(f, 0) for f in fields}
            parsed_scores.update(structured_scores)
    if not parsed_scores and not re.search(r'\d/10', text_to_parse): return None
    
    return {
        'scores': validate_scores(parsed_scores), 'source': 'parsed_payload',
        'additional_data': {'detailed_feedback': text_to_parse, 'coaching_tips': []}
    }
def generate_detailed_feedback(evaluation_data: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    parsed_feedback: Dict[str, Dict[str, Any]] = {}
    
    score_reasoning_pattern = re.compile(
        r"[-\*\s]*\*?\*?(Product Knowledge|Costs?[\s&]*Booking|Tone(?:\s*of)?\s*Voice|Objection Handling|Call Control[/\s]*Flow)\*?\*?\s*:\s*\*?\*?(\d+(?:\.\d+)?)\/10\*?\*?"
        r"([\s\S]*?)"
        r"(?=[-\*\s]*\*?\*?(?:Product Knowledge|Costs?[\s&]*Booking|Tone(?:\s*of)?\s*Voice|Objection Handling|Call Control[/\s]*Flow)\*?\*?\s*:|\*\*Critical Misses:\*\*|\*\*Conversion Potential:\*\*|\*\*Weighted Overall Score:\*\*|\Z)",
        re.IGNORECASE
    )
    
    score_matches = score_reasoning_pattern.findall(evaluation_data or "")
    
    score_mapping = {
        'product knowledge': 'product_knowledge', 
        'costs & booking': 'costs_booking', 
        'costs and booking': 'costs_booking',
        'costs booking': 'costs_booking', 
        'tone of voice': 'tone_voice', 
        'tone voice': 'tone_voice',
        'objection handling': 'objection_handling', 
        'call control/flow': 'call_control',
        'call control flow': 'call_control'
    }
    
    for title_raw, score_text, reasoning in score_matches:
        key_cleaned = re.sub(r'[\s&/]+', ' ', title_raw.strip().lower())
        key = score_mapping.get(key_cleaned, key_cleaned.replace(' ', '_'))
        
        try: 
            score_value = float(score_text)
        except: 
            score_value = 0.0
        
        reasoning_cleaned = reasoning.strip()
        reasoning_cleaned = re.sub(r'^\s*→\s*', '', reasoning_cleaned)
        reasoning_cleaned = re.sub(r'\n\s*', ' ', reasoning_cleaned)
        reasoning_cleaned = re.sub(r'\s+', ' ', reasoning_cleaned)
        
        bullets = re.findall(r'(?:•|-|\*|\d+\.)\s+(.*?)(?=(?:•|-|\*|\d+\.)|$)', reasoning_cleaned, re.MULTILINE)
        
        if bullets: 
            html = "<ul>" + "".join([f"<li>{re.sub(r'<[^>]*>', '', b).strip()}</li>" for b in bullets if b.strip()]) + "</ul>"
        else: 
            html = f"<p>{reasoning_cleaned}</p>"
        
        parsed_feedback[key] = {'score_text': f"{score_value}", 'reasoning': html}
    
    coaching_tips = []
    coaching_patterns = [
        r'\*\*💡\s*Coaching Tips.*?:\*\*\s*\n(.*?)(?=\*\*.*?:\*\*|\Z)',
        r'💡\s*COACHING TIPS.*?\n(.*?)(?=\*\*.*?:\*\*|\Z)',
        r'\*\*COACHING TIPS.*?:\*\*\s*\n(.*?)(?=\*\*.*?:\*\*|\Z)'
    ]
    
    for pattern in coaching_patterns:
        coaching_match = re.search(pattern, evaluation_data, re.IGNORECASE | re.DOTALL)
        if coaching_match:
            coaching_section = coaching_match.group(1).strip()
            tip_items = re.findall(r'^\s*(?:\d+\.|\*|-|•)\s*\*?\*?(.*?)(?=\n\s*(?:\d+\.|\*|-|•)|\Z)', 
                                    coaching_section, re.MULTILINE | re.DOTALL)
            
            for tip in tip_items:
                tip_cleaned = re.sub(r'\n\s*', ' ', tip.strip())
                tip_cleaned = re.sub(r'\s+', ' ', tip_cleaned)
                tip_cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', tip_cleaned)
                tip_cleaned = tip_cleaned.strip()
                
                if tip_cleaned and len(tip_cleaned) > 10:
                    coaching_tips.append(tip_cleaned)
            
            if coaching_tips:
                break
    
    overall_data = {'coaching_tips': coaching_tips}
    
    return parsed_feedback, overall_data
def calc_overall_score(scores: Dict[str, float]) -> float:
    weights = {'product_knowledge': 0.3, 'costs_booking': 0.25, 'tone_voice': 0.2, 'objection_handling': 0.15, 'call_control': 0.1}
    return sum(scores.get(k, 0) * w for k, w in weights.items())
def extract_real_call_score_and_tips(evaluation_data: Any) -> Tuple[Optional[float], List[str]]:
    se = extract_structured_evaluation(evaluation_data)
    tips: List[str] = []
    if se:
        add = se.get("additional_data", {})
        if isinstance(add, dict) and isinstance(add.get("coaching_tips"), list) and add["coaching_tips"]:
            tips.extend([t for t in add["coaching_tips"] if isinstance(t, str) and t.strip()])
        if not tips and isinstance(add, dict) and isinstance(add.get("detailed_feedback"), str):
            _, overall_tips_from_generate = generate_detailed_feedback(add["detailed_feedback"])
            if isinstance(overall_tips_from_generate.get("coaching_tips"), list):
                tips.extend([t for t in overall_tips_from_generate["coaching_tips"] if isinstance(t, str) and t.strip()])
        overall = calc_overall_score(se.get("scores", {})) if se.get("scores") else None
        seen = set(); tips_dedup = []
        for t in tips:
            tt = t.strip()
            if tt and tt not in seen: tips_dedup.append(tt); seen.add(tt)
        return overall, tips_dedup
    return None, []

def display_evaluation_scores_improved(evaluation_data: Any, trainee_name: str = ""):
    structured_eval = extract_structured_evaluation(evaluation_data)
    if structured_eval and structured_eval.get('scores'):
        scores = structured_eval['scores']
        additional_data = structured_eval.get('additional_data', {})
        per_category_feedback, _ = {}, {}
        if 'detailed_feedback' in additional_data: per_category_feedback, _ = generate_detailed_feedback(additional_data['detailed_feedback'])
        st.markdown("### Training Evaluation Scores")
        if trainee_name: st.markdown(f"""<div class="trainee-name-card"><h3 class="trainee-name-text">Trainee: {trainee_name}</h3><p style="margin: 0; opacity: 0.9;">Evaluation Results</p></div>""", unsafe_allow_html=True)
        st.success(f"Scores successfully extracted from: {structured_eval['source']}")
        required_scores = ['product_knowledge', 'costs_booking', 'tone_voice', 'objection_handling', 'call_control']
        missing_scores = [s for s in required_scores if s not in scores or scores.get(s) == 0]
        if missing_scores: st.warning(f"Missing or zero scores for: {', '.join(missing_scores)}")
        
        score_configs = [
            ('product_knowledge', 'Product Knowledge', '30%'), ('costs_booking', 'Costs & Booking', '25%'),
            ('tone_voice', 'Tone of Voice', '20%'), ('objection_handling', 'Objection Handling', '15%'),
            ('call_control', 'Call Control/Flow', '10%')
        ]

        if "show_dialog" not in st.session_state:
            st.session_state.show_dialog = False

        score_cols = st.columns(5, gap="medium")
        for idx, (score_key, label, weight) in enumerate(score_configs):
            score_value = scores.get(score_key, 0.0)
            with score_cols[idx]:
                st.markdown(f"""<div class="score-card"><h6>{label}</h6><h2>{score_value:.1f}/10</h2><p>Weight: {weight}</p></div>""", unsafe_allow_html=True)
                st.progress(score_value / 10)
                if score_key in per_category_feedback:
                    button_key = f"dialog_{score_key}_{idx}"
                    if st.button("Why this score?", key=button_key):
                        st.session_state.show_dialog = True
                        st.session_state.dialog_content = {
                            "label": label, 
                            "value": score_value, 
                            "reasoning": per_category_feedback[score_key]['reasoning']
                        }
        
        @st.dialog("Detailed Evaluation")
        def show_evaluation_dialog(score_label, score_value, reasoning, has_reasoning: bool):
            st.markdown(f"### {score_label}: {score_value:.1f}/10")
            st.markdown("---")
            if has_reasoning: 
                st.markdown(reasoning, unsafe_allow_html=True)
            else: 
                st.warning("No detailed reasoning was provided by the evaluator for this criterion.")
            if st.button("Close"): 
                st.session_state.show_dialog = False
                st.rerun()

        if st.session_state.get("show_dialog", False):
            dialog_content = st.session_state.get("dialog_content", {})
            show_evaluation_dialog(
                dialog_content.get("label", ""), 
                dialog_content.get("value", 0.0), 
                dialog_content.get("reasoning", ""), 
                bool(dialog_content.get("reasoning"))
            )

        overall_score = calc_overall_score(scores)
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Overall Training Score")
            if overall_score >= 8: grade, color = "Excellent", "#28a745"
            elif overall_score >= 6: grade, color = "Good", "#ffc107"
            else: grade, color = "Needs Work", "#dc3545"
            st.markdown(f"""<div style="text-align: center; padding: 2rem; border-radius: 10px; background: linear-gradient(135deg, {color} 0%, {color}aa 100%); margin: 1rem 0;"><h1 style="color: white; font-size: 4rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{overall_score:.1f}/10</h1><h3 style="color: white; margin: 0;">{grade}</h3></div>""", unsafe_allow_html=True)
        st.markdown("### Detailed Score Breakdown")
        breakdown_data = []
        for (key, label, weight_str), weight in zip(score_configs, [0.3, 0.25, 0.2, 0.15, 0.1]):
            score_value = scores.get(key, 0)
            weighted_contribution = score_value * weight
            breakdown_data.append({'Criteria': label, 'Raw Score': f"{score_value:.1f}/10", 'Weight': weight_str, 'Weighted Score': f"{weighted_contribution:.2f}", 'Performance': "Good" if score_value >= 7 else "Average" if score_value >= 5 else "Needs Work"})
        st.table(breakdown_data)
        st.markdown("### Full Detailed Evaluation")
        with st.expander("View Complete Evaluation", expanded=True):
            raw_text_content = additional_data.get('detailed_feedback', '')
            if raw_text_content: st.markdown(raw_text_content, unsafe_allow_html=True)
            else: st.warning("No detailed text feedback found in the evaluation payload.")
        return True
    else:
        st.markdown("### Evaluation Scores Not Found")
        st.error("Unable to extract structured evaluation scores from the provided data.")
        st.info("This can happen if the post-call analysis is still running or was not configured correctly for the agent.")
        st.code(str(evaluation_data), language="text")
        return False
def _coerce_start_dt(call) -> Optional[datetime]:
    ts = None
    if hasattr(call, "start_timestamp") and call.start_timestamp:
        ts = int(call.start_timestamp)
        if ts > 1_000_000_000_000: ts //= 1_000
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if hasattr(call, "start_time") and call.start_time:
        ts = int(call.start_time)
        if ts > 1_000_000_000_000: ts //= 1_000
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if hasattr(call, "created_at") and call.created_at:
        v = call.created_at
        try:
            if isinstance(v, (int, float)):
                ts = int(v)
                if ts > 1_000_000_000_000: ts //= 1_000
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            elif isinstance(v, str):
                if v.isdigit():
                    ts = int(v)
                    if ts > 1_000_000_000_000: ts //= 1_000
                    return datetime.fromtimestamp(ts, tz=timezone.utc)
                else:
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception: pass
    return None

# ===============================================
# OPTIMIZED DATA FETCHING SECTION
# ===============================================
@st.cache_data(ttl=600, show_spinner="Fetching call history from Retell API...")
def list_all_calls(_client: Retell, start_timestamp: int, end_timestamp: int):
    """
    Optimized function to fetch all calls within a specific timestamp range.
    """
    out = []
    page_size = 100
    cursor = None
    
    filter_payload = {
        "start_timestamp": {
            "gte": start_timestamp,
            "lte": end_timestamp
        }
    }

    while True:
        try:
            kwargs = {
                "limit": page_size,
                "filter_criteria": filter_payload,
                "sort_order": "descending" 
            }
            if cursor:
                kwargs["cursor"] = cursor
                
            resp = _client.call.list(**kwargs)
            
            calls = getattr(resp, "data", None)
            if calls is None:
                calls = resp or []

            if not calls:
                break
            
            out.extend(calls)
            
            has_more = bool(getattr(resp, "has_more", False))
            next_cur = getattr(resp, "next_cursor", None) or getattr(resp, "cursor", None)
            
            if not has_more or not next_cur:
                break
                
            cursor = next_cur
            
        except Exception as e:
            st.warning(f"API call failed: {str(e)}. This might happen if the API doesn't support 'filter_criteria' as expected.")
            break
            
    out.sort(key=lambda c: _coerce_start_dt(c) or datetime.fromtimestamp(0, tz=timezone.utc), reverse=True)
    return out

def get_time_range_for_caching(days: int, round_to_minutes: int = 15) -> Tuple[int, int]:
    """
    Creates stable start/end timestamps for effective caching.
    """
    now = datetime.now(timezone.utc)
    discard = timedelta(
        minutes=now.minute % round_to_minutes,
        seconds=now.second,
        microseconds=now.microsecond
    )
    rounded_end_dt = now - discard
    start_dt = rounded_end_dt - timedelta(days=days)
    
    return int(start_dt.timestamp()), int(rounded_end_dt.timestamp())

# =========================
# USER VIEW
# =========================
def render_user_view(client: Retell):
    trainee_name = st.session_state.get("auth_name", "Unknown User")
    
    st.markdown("""<div class="title-container"><h1 class="title-text">Aspect AI Training Agent</h1><p class="subtitle-text">Advanced Role-Play Simulation for Booking Agents</p></div>""", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown(f"## Welcome, {trainee_name}")
        st.markdown("### Training Configuration")
        level_options = {
            "1": {"name": "Level 1: Foundation", "description": "Cooperative customers with basic booking needs", "details": "Basic plumbing, electrical, heating issues. Customers are cooperative but cautious."},
            "2": {"name": "Level 2: Objection Handling", "description": "Pushy customers with competitive comparisons", "details": "Customers compare prices, challenge guarantees, resist giving information."},
            "3": {"name": "Level 3: Advanced", "description": "Complex scenarios with multiple trade requirements", "details": "Confused customers, multiple trades needed, commercial scenarios."}
        }
        selected_level = st.selectbox("Choose Training Level:", options=list(level_options.keys()), format_func=lambda x: f"{level_options[x]['name']}")
        level_info = level_options[selected_level]
        st.markdown(f"""<div class="level-card"><h4>{level_info['name']}</h4><p><strong>Focus:</strong> {level_info['description']}</p><p><small>{level_info['details']}</small></p></div>""", unsafe_allow_html=True)
        
        st.markdown("### Voice Selection")
        voice_options = ["Alternate Each Call"] + list(CHAIN_START_AGENT_IDS.keys())
        default_voice = "Female Voice Start"
        default_index = voice_options.index(default_voice) if default_voice in voice_options else 0
        
        selected_voice_option = st.selectbox(
            "Choose Starting Agent Voice:",
            options=voice_options,
            index=default_index,
            help="Select which voice starts the training. The voice will switch mid-call based on agent configuration."
        )

        st.markdown("---")
        st.markdown("### Training Parameters")
        session_duration = st.selectbox("Session Duration", options=[5, 10, 15, 20, 30], index=2, format_func=lambda x: f"{x} minutes")
        scenario_count = st.selectbox("Number of Scenarios", options=[3, 5, 7, 10], index=1, help="Number of customer scenarios to practice")
        difficulty_focus = st.multiselect("Focus Areas", options=["Plumbing & Cold Water","Heating & Hot Water","Electrical work","Drainage","Leak Detection","Roofing", "HVAC","Multi-Trade","Decoration","Fire Safety","Insurance","Commercial"], default=["Plumbing & Cold Water", "Electrical work", "Heating & Hot Water"])
        st.markdown("### Call Settings")
        enable_recording = st.checkbox("Enable Call Recording", value=True)
        enable_transcript = st.checkbox("Generate Live Transcript", value=True)
        enable_analysis = st.checkbox("Post-Call Analysis", value=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("## Voice Training Session")
        st.markdown(f"""<div class="trainee-name-card"><h3 class="trainee-name-text">Current Trainee: {trainee_name}</h3><p style="margin: 0; opacity: 0.9;">Ready to begin your training session</p></div>""", unsafe_allow_html=True)
        
        phone_number = st.text_input("Enter your phone number:", placeholder="+447123456789", help="Include country code (e.g., +44 for UK)")
        
        def is_valid_phone(phone): return phone and phone.startswith('+') and len(phone.replace('+', '').replace('-', '').replace(' ', '')) >= 10
        
        if phone_number and not is_valid_phone(phone_number):
            st.warning("Please enter a valid phone number with country code")
        
        session_metadata = {
            "training_level": selected_level, "level_name": level_info['name'],
            "trainee_name": trainee_name, "session_duration_minutes": session_duration,
            "scenario_count": scenario_count, "focus_areas": ", ".join(difficulty_focus) if difficulty_focus else "General",
            "session_id": f"session_{int(time.time())}", "timestamp": datetime.now().isoformat(),
            "settings": {"recording_enabled": enable_recording, "transcript_enabled": enable_transcript, "analysis_enabled": enable_analysis}
        }
        llm_dynamic_variables = {
            "training_level": str(selected_level), "level_description": str(level_info['description']),
            "scenario_count": str(scenario_count), "focus_areas": ", ".join(difficulty_focus) if difficulty_focus else "General",
            "trainee_name": str(trainee_name), "session_type": "booking_practice"
        }
        
        if st.button("Start Training Session", disabled=not is_valid_phone(phone_number)):
            try:
                with st.spinner("Initiating training session..."):
                    
                    if "voice_idx" not in st.session_state:
                        st.session_state.voice_idx = 0
                    
                    agent_id_to_use = None
                    if selected_voice_option == "Alternate Each Call":
                        voice_keys = sorted(list(CHAIN_START_AGENT_IDS.keys()))
                        key_to_use = voice_keys[st.session_state.voice_idx % len(voice_keys)]
                        agent_id_to_use = CHAIN_START_AGENT_IDS[key_to_use]
                        st.session_state.voice_idx += 1
                    else:
                        agent_id_to_use = CHAIN_START_AGENT_IDS[selected_voice_option]

                    call_params = {
                        "from_number": FROM_NUMBER,
                        "to_number": phone_number,
                        "override_agent_id": agent_id_to_use,
                        "retell_llm_dynamic_variables": llm_dynamic_variables,
                        "metadata": session_metadata
                    }
                    
                    # --- IMMEDIATE FIX ---
                    # The lines below for 'post_call_analysis' were causing the crash because your
                    # retell-python library is outdated. I have commented them out so the app will run.
                    #
                    # --- PERMANENT SOLUTION ---
                    # 1. Open your terminal/command prompt.
                    # 2. Run this command:   pip install --upgrade retell-python
                    # 3. After it finishes, UNCOMMENT the three lines below to re-enable analysis.
                    
                    # if EVALUATION_AGENT_ID and enable_analysis:
                    #     call_params["post_call_analysis"] = True
                    #     call_params["post_call_analysis_agent_id"] = EVALUATION_AGENT_ID
                    
                    response = client.call.create_phone_call(**call_params)

                    st.session_state.current_call_id = response.call_id
                    st.session_state.session_metadata = session_metadata
                    st.session_state.training_active = True
                    st.success("🎯 Training session initiated!")
                    st.info(f"📞 Expect a call shortly. **Level {selected_level}** with {scenario_count} scenarios.")
                    with st.expander("Session Summary", expanded=True):
                        st.write(f"**Call ID:** {response.call_id}")
                        st.write(f"**Trainee:** {trainee_name}")
                        st.write(f"**Training Level:** {level_info['name']}")
                        st.write(f"**Voice Used:** {selected_voice_option}")
                        st.write(f"**Scenarios:** {scenario_count}")
                        st.write(f"**Focus Areas:** {', '.join(difficulty_focus) if difficulty_focus else 'General'}")
                        st.write(f"**Duration:** {session_duration} minutes")
            except Exception as e:
                st.error(f"❌ Error starting training session: {e}")
                st.info("Check your phone format and that you have assigned a default agent to your number in the Retell Dashboard.")

    if hasattr(st.session_state, 'training_active') and st.session_state.training_active:
        if hasattr(st.session_state, 'current_call_id'):
            st.markdown("---")
            st.markdown("## Live Training Session")
            try:
                call_details = client.call.retrieve(st.session_state.current_call_id)
                colA, colB, colC = st.columns(3)
                with colA: st.metric("Call Status", call_details.call_status.title())
                with colB:
                    if hasattr(call_details, 'duration') and call_details.duration:
                        duration_sec = call_details.duration
                        st.metric("Duration", f"{int(duration_sec//60)}:{int(duration_sec%60):02d}")
                    else: st.metric("Duration", "Active")
                with colC:
                    if st.button("End Session"):
                        try:
                            client.call.cancel(call_id=st.session_state.current_call_id)
                            st.session_state.training_active = False
                            st.success("Training session ended!")
                            st.rerun()
                        except Exception as e: st.error(f"Error ending call: {e}")
                if enable_transcript and hasattr(call_details, 'transcript_object') and call_details.transcript_object:
                    st.markdown("### Live Transcript")
                    transcript_html = '<div class="transcript-box">'
                    for entry in call_details.transcript_object[-15:]:
                        role = "Customer" if entry.role == "user" else "Trainee"
                        content = entry.content if hasattr(entry, 'content') else str(entry)
                        if role == "Customer": transcript_html += f'<p><span class="customer-msg">{role}:</span> {content}</p>'
                        else: transcript_html += f'<p><span class="trainee-msg">{role}:</span> {content}</p>'
                    transcript_html += '</div>'
                    st.markdown(transcript_html, unsafe_allow_html=True)
            except Exception as e: st.warning(f"Unable to fetch live call data: {e}")
    
    if hasattr(st.session_state, 'current_call_id'):
        try:
            call_status_check = client.call.retrieve(st.session_state.current_call_id)
            if call_status_check.call_status == "ended":
                if st.session_state.get('training_active', False):
                    st.session_state.training_active = False
                    st.session_state.show_latest_evaluation = True
                    st.rerun()
        except Exception:
            pass
            
    if st.session_state.get('show_latest_evaluation', False) and 'current_call_id' in st.session_state:
        display_call_analysis_for_user(client, st.session_state.current_call_id)
        st.session_state.show_latest_evaluation = False

    st.markdown("---")
    st.markdown("## Your Performance & Attempts")
    st.caption("Summary of your past sessions. Click 'View Evaluation' for full details.")
    perf_days = st.number_input("Look back (days)", min_value=1, max_value=180, value=30, step=1, key="user_perf_days")
    max_rows = st.number_input("Max sessions to show", min_value=1, max_value=50, value=10, step=1, key="user_perf_max")
    
    if 'performance_data' not in st.session_state:
        st.session_state.performance_data = None

    if st.button("Load My Performance"):
        with st.spinner("Loading your performance history..."):
            start_ts, end_ts = get_time_range_for_caching(days=int(perf_days))
            all_calls = list_all_calls(client, start_ts, end_ts)
            
            calls = [c for c in all_calls if (getattr(c, "metadata", {}) or {}).get("trainee_name", "").strip().lower() == trainee_name.strip().lower()]
            ended = [c for c in calls if getattr(c, "call_status", "") == "ended"]
            per_call_score = {}
            rows = []
            for c in ended[:int(max_rows)]:
                ev = None
                call_analysis = getattr(c, 'call_analysis', None)
                if call_analysis: ev = getattr(call_analysis, 'custom_analysis_data', None)
                if ev is None:
                    metadata = getattr(c, 'metadata', None)
                    if isinstance(metadata, dict): ev = metadata.get("evaluation") or (metadata if "evaluation_score" in metadata else None)
                if ev is None: ev = getattr(c, 'transcript', None)
                se = extract_structured_evaluation(ev) if ev else None
                overall = calc_overall_score(se["scores"]) if se and se.get("scores") else None
                per_call_score[c.call_id] = overall
                dt = _coerce_start_dt(c)
                dt_str = dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M') if dt else "N/A"
                level = (getattr(c, "metadata", {}) or {}).get("training_level", "—")
                rows.append({"Date (UTC)": dt_str, "Call ID": c.call_id[:10], "Level": level, "Overall": f"{overall:.1f}" if isinstance(overall, (int, float)) else "—", "Action": f"view_{c.call_id}"})
            
            valid_scores = [v for v in per_call_score.values() if isinstance(v, (int, float))]
            avg_score_val = (sum(valid_scores)/len(valid_scores)) if valid_scores else "—"

            st.session_state.performance_data = {
                "rows": rows,
                "attempts": len(calls),
                "ended_count": len(ended),
                "avg_score": avg_score_val
            }

    if st.session_state.performance_data:
        perf_data = st.session_state.performance_data
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Attempts (range)", perf_data["attempts"])
        with c2: 
            avg_score = perf_data["avg_score"]
            st.metric("Avg Score", f"{avg_score:.2f}" if isinstance(avg_score, (int, float)) else "—")
        with c3: st.metric("Ended Sessions", perf_data["ended_count"])
        
        if perf_data["rows"]:
            st.markdown("### Past Sessions")
            for r in perf_data["rows"]:
                colA, colB, colC, colD, colE = st.columns([2,2,1,1,1])
                with colA: st.write(r["Date (UTC)"])
                with colB: st.write(f"Call {r['Call ID']}...")
                with colC: st.write(f"Level {r['Level']}")
                with colD: st.write(f"Score: {r['Overall']}")
                with colE:
                    if st.button("View Evaluation", key=r["Action"]):
                        st.session_state.current_call_id = r["Action"].replace("view_", "")
                        st.session_state.training_active = False
                        st.session_state.show_latest_evaluation = True
                        st.rerun()
        else: 
            st.info("No ended sessions in the selected range found for your user.")

    st.markdown("---")
    st.markdown("## Coaching Tips")
    st.caption("Pulled from your real evaluation output.")
    tips_days = st.number_input("Look back (days)", min_value=1, max_value=90, value=14, step=1, key="tips_days")
    tips_limit = st.number_input("Max sessions to include", min_value=1, max_value=20, value=5, step=1, key="tips_limit")
    
    if 'coaching_tips_data' not in st.session_state:
        st.session_state.coaching_tips_data = None

    if st.button("Load Coaching Tips"):
        with st.spinner("Loading coaching tips..."):
            start_ts, end_ts = get_time_range_for_caching(days=int(tips_days))
            all_calls = list_all_calls(client, start_ts, end_ts)

            calls = [c for c in all_calls if getattr(c, "call_status", "") == "ended" and (getattr(c, "metadata", {}) or {}).get("trainee_name", "").strip().lower() == trainee_name.strip().lower()]
            calls = calls[:int(tips_limit)]
            
            tips_results = []
            if calls:
                for c in calls:
                    ev = None; full = None
                    try: full = client.call.retrieve(c.call_id)
                    except Exception: pass
                    if full:
                        if hasattr(full, 'call_analysis') and full.call_analysis and getattr(full.call_analysis, 'custom_analysis_data', None): ev = full.call_analysis.custom_analysis_data
                        if ev is None and hasattr(full, 'metadata') and full.metadata: ev = full.metadata.get("evaluation") or (full.metadata if "coaching_tips" in full.metadata or "evaluation_score" in full.metadata else None)
                        if ev is None and hasattr(full, 'transcript'): ev = full.transcript
                    overall, tips = extract_real_call_score_and_tips(ev) if ev is not None else (None, [])
                    dt = _coerce_start_dt(c)
                    dt_str = dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M') if dt else "N/A"
                    tips_results.append({
                        "call_id": c.call_id,
                        "dt_str": dt_str,
                        "overall": overall,
                        "tips": tips
                    })
            st.session_state.coaching_tips_data = tips_results
    
    if st.session_state.coaching_tips_data is not None:
        tips_data = st.session_state.coaching_tips_data
        if not tips_data:
            st.info("No recent ended sessions found to pull coaching tips from.")
        else:
            found_any = False
            for result in tips_data:
                st.markdown(f"**Session #{result['call_id'][:8]} • {result['dt_str']} UTC**")
                if result['overall'] is not None: 
                    st.caption(f"Overall Score: **{result['overall']:.1f}/10**")
                if result['tips']:
                    found_any = True
                    for i, tip in enumerate(result['tips'], 1): st.info(f"**{i}.** {tip}")
                else: 
                    st.warning("No coaching tips found in the evaluation payload for this session.")
            
            if not found_any:
                with st.expander("Why no tips? Click for setup checklist.", expanded=False):
                    st.markdown("""**To receive real coaching tips, ensure your evaluation payload includes them:**\n- Include a `COACHING TIPS:` section in your agent's evaluation output.\n- The parser looks for that heading and extracts bullet points or numbered lists that follow.""")
                    
    st.markdown("""<div style='text-align: center; color: #6c757d; padding: 1.2rem;'><p>Powered by Aspect AI Training System | Built with Streamlit & Retell AI</p></div>""", unsafe_allow_html=True)

def display_call_analysis_for_user(client, call_id):
    try:
        with st.spinner("Fetching latest evaluation data..."):
            call_details = client.call.retrieve(call_id)
        if call_details.call_status != "ended": return
        
        st.markdown("---")
        st.markdown("## Your Training Session Results")
        
        trainee_name = (getattr(call_details, 'metadata', {}) or {}).get('trainee_name', st.session_state.get('auth_name', ''))
        
        evaluation_data = None
        if hasattr(call_details, 'call_analysis') and call_details.call_analysis and hasattr(call_details.call_analysis, 'custom_analysis_data') and call_details.call_analysis.custom_analysis_data:
            evaluation_data = call_details.call_analysis.custom_analysis_data
        if not evaluation_data and hasattr(call_details, 'metadata') and call_details.metadata:
            evaluation_data = call_details.metadata.get("evaluation") or (call_details.metadata if "evaluation_score" in call_details.metadata else None)
        if not evaluation_data and hasattr(call_details, 'transcript'):
            evaluation_data = call_details.transcript
        
        if evaluation_data: 
            display_evaluation_scores_improved(evaluation_data, trainee_name)
        else: 
            st.info("No structured evaluation data found for this session yet.")
    except Exception as e:
        st.error(f"Failed to display call analysis for call ID {call_id}.")
        st.exception(e)


# =========================
# ADMIN VIEW
# =========================
def render_admin_view(client: Retell):
    st.markdown("""<div class="title-container"><h1 class="title-text">Aspect AI — Admin Console</h1><p class="subtitle-text">Per-Trainee Dashboards, Evaluation & Performance</p></div>""", unsafe_allow_html=True)

    st.markdown("### Trainee Search")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_name = st.text_input("Enter Trainee Name to Search", placeholder="e.g., Jane Doe", key="admin_search_name", label_visibility="collapsed")
    with col2:
        search_button = st.button("🔍 Search History", type="primary")
    with col3:
        show_recent_n = st.number_input("Sessions to show", min_value=1, max_value=100, value=10, step=1, key="admin_recent_n", help="Number of recent sessions to display for the searched trainee.")

    if 'last_searched_name' not in st.session_state:
        st.session_state.last_searched_name = None

    if not search_button and not st.session_state.last_searched_name:
       st.info("Enter a trainee's name and click 'Search History' to load their performance data.")
       return

    if search_button:
        st.session_state.last_searched_name = search_name
        if 'current_call_id' in st.session_state:
            del st.session_state['current_call_id']

    current_search = st.session_state.last_searched_name
    if not current_search:
        return

    start_ts, end_ts = get_time_range_for_caching(days=90)
    all_calls_in_range = list_all_calls(client, start_ts, end_ts)

    trainee_calls = [
        c for c in all_calls_in_range
        if (getattr(c, "metadata", {}) or {}).get("trainee_name", "").strip().lower() == current_search.strip().lower()
    ]

    if not trainee_calls:
        st.warning(f"No calls found for trainee '{current_search}' in the last 90 days.")
        return

    ended_calls = [c for c in trainee_calls if getattr(c, "call_status", "") == "ended"]
    per_call_score: Dict[str, Optional[float]] = {}
    
    with st.spinner(f"Analyzing {len(ended_calls)} completed session(s) for {current_search}..."):
        for c in ended_calls:
            ev = None; full = None
            try:
                if hasattr(c, 'call_analysis') and c.call_analysis and getattr(c.call_analysis, 'custom_analysis_data', None):
                    ev = c.call_analysis.custom_analysis_data
                else:
                    full = client.call.retrieve(c.call_id)
            except Exception: pass
            
            if ev is None and full and hasattr(full, 'call_analysis') and full.call_analysis and getattr(full.call_analysis, 'custom_analysis_data', None): ev = full.call_analysis.custom_analysis_data
            if ev is None:
                source_obj = full if full else c
                if hasattr(source_obj, 'metadata') and source_obj.metadata: ev = source_obj.metadata.get("evaluation") or (source_obj.metadata if "evaluation_score" in source_obj.metadata else None)
            if ev is None:
                source_obj = full if full else c
                if hasattr(source_obj, 'transcript'): ev = source_obj.transcript
                
            se = extract_structured_evaluation(ev) if ev is not None else None
            overall = calc_overall_score(se["scores"]) if se and se.get("scores") else None
            per_call_score[c.call_id] = overall
        
    st.markdown("---")
    st.markdown(f"## Dashboard for: {current_search}")
    st.caption("Showing data from the last 90 days. Click 'Open Full Evaluation' to see details.")

    vals = [v for v in per_call_score.values() if isinstance(v, (int, float))]
    avg_score = sum(vals) / len(vals) if vals else None
    
    sub1, sub2, sub3 = st.columns(3)
    with sub1: st.metric("Total Attempts", len(trainee_calls))
    with sub2: st.metric("Completed Sessions", len(ended_calls))
    with sub3: st.metric("Average Score", f"{avg_score:.2f}" if avg_score is not None else "—")

    st.markdown("#### Recent Sessions")
    for c in trainee_calls[:int(show_recent_n)]:
        dt = _coerce_start_dt(c)
        dt_str = dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M') if dt else "N/A"
        level = (getattr(c, "metadata", {}) or {}).get("training_level", "—")
        overall = per_call_score.get(c.call_id)
        call_status = getattr(c, "call_status", "unknown").title()

        colA, colB, colC, colD, colE = st.columns([2, 2, 2, 2, 2])
        with colA: st.write(dt_str)
        with colB: st.code(f"{c.call_id}")
        with colC: st.write(f"Lvl: **{level}**")
        with colD:
            if call_status == "Ended":
                score_str = f"Score: **{overall:.1f}**" if isinstance(overall, (int, float)) else "Score: N/A"
                st.write(score_str)
            else:
                st.write(f"Status: *{call_status}*")
        with colE:
            if call_status == "Ended":
                if st.button("Open Full Evaluation", key=f"open_eval_{c.call_id}"):
                    st.session_state.current_call_id = c.call_id
                    st.rerun()

    if st.session_state.get("current_call_id"):
        st.markdown("---")
        st.markdown("## Full Evaluation View (Admin)")
        display_call_analysis_admin(client, st.session_state.current_call_id)

def _maybe_get_recording_url(call_details):
    for attr in ["recording_url", "audio_url", "url"]:
        if hasattr(call_details, attr) and getattr(call_details, attr):
            return getattr(call_details, attr)

    if hasattr(call_details, "recording") and getattr(call_details, "recording"):
        rec = getattr(call_details, "recording")
        for attr in ["url", "recording_url", "audio_url"]:
            if hasattr(rec, attr) and getattr(rec, attr):
                return getattr(rec, attr)

    if hasattr(call_details, "metadata") and isinstance(call_details.metadata, dict):
        for k in ["recording_url", "audio_url", "recordingUri", "recording"]:
            v = call_details.metadata.get(k)
            if isinstance(v, str) and v.startswith(("http://", "https://")):
                return v
            if isinstance(v, dict):
                for kk in ["url", "recording_url", "audio_url"]:
                    if isinstance(v.get(kk), str) and v[kk].startswith(("http://", "https://")):
                        return v[kk]
    return None

def display_call_analysis_admin(client, call_id):
    try:
        with st.spinner("Fetching evaluation details..."):
            call_details = client.call.retrieve(call_id)
            if call_details.call_status != "ended":
                st.info("Call analysis will be available once the call is completed.")
                return
            trainee_name = (getattr(call_details, 'metadata', {}) or {}).get('trainee_name', '')

            evaluation_data = None
            if hasattr(call_details, 'call_analysis') and call_details.call_analysis and hasattr(call_details.call_analysis, 'custom_analysis_data') and call_details.call_analysis.custom_analysis_data:
                evaluation_data = call_details.call_analysis.custom_analysis_data
            if not evaluation_data and hasattr(call_details, 'metadata') and call_details.metadata:
                evaluation_data = call_details.metadata.get("evaluation") or (call_details.metadata if "evaluation_score" in call_details.metadata else None)
            if not evaluation_data and hasattr(call_details, 'transcript'):
                evaluation_data = call_details.transcript
        
        if evaluation_data:
            display_evaluation_scores_improved(evaluation_data, trainee_name)
        else:
            st.info("No structured evaluation data found for this session.")
        
        st.markdown("### Session Artifacts")
        colA, colB = st.columns(2)
        with colA:
            with st.expander("Full Transcript", expanded=False):
                if hasattr(call_details, 'transcript_object') and call_details.transcript_object:
                    html = '<div class="transcript-box">'
                    for entry in call_details.transcript_object:
                        role = "Customer" if getattr(entry, "role", "") == "user" else "Trainee"
                        content = getattr(entry, "content", "") or str(entry)
                        cls = "customer-msg" if role == "Customer" else "trainee-msg"
                        html += f'<p><span class="{cls}">{role}:</span> {content}</p>'
                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)
                elif hasattr(call_details, 'transcript') and call_details.transcript:
                    st.text_area("Transcript (Raw)", call_details.transcript, height=300, label_visibility="collapsed")
                else:
                    st.info("No transcript available for this call.")
        with colB:
            recording_url = _maybe_get_recording_url(call_details)
            if recording_url:
                st.markdown(f"**Recording:** [Open audio]({recording_url})")
                st.audio(recording_url)
            else:
                st.info("No recording URL found in this call object or metadata.")
    except Exception as e:
        st.error(f"Unable to load evaluation: {e}")

def main():
    if not st.session_state.auth_role:
        render_login_screen()
        st.markdown(
            f"""
            <div class="footer">
                <div><strong>{COMPANY_NAME}</strong></div>
                <div>© {datetime.now().year} {COMPANY_NAME}. All rights reserved.</div>
                <div style="margin-top:6px;">Support: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a> · {SUPPORT_PHONE}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    client = init_retell()
    topbar = st.columns([7,1])
    with topbar[1]:
        if st.button("Sign out", key="main_signout"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()
            
    if st.session_state.auth_role == "admin":
        render_admin_view(client)
    else:
        render_user_view(client)
        
    st.markdown(
        f"""
        <div class="footer">
            <div><strong>{COMPANY_NAME}</strong></div>
            <div>© {datetime.now().year} {COMPANY_NAME}. All rights reserved.</div>
            <div style="margin-top:6px;">Support: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a> · {SUPPORT_PHONE}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
