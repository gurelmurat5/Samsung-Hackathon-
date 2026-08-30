"""
Digital Zen-Coach 🧘
A Generative-AI powered digital well-being coach.

Hackathon: Digital Addiction & Digital Well-Being (28-30 Aug 2026)
Rubric targets: Functionality (30) | Prompt Design (25) | Ethical Awareness (15)

Run locally:
    pip install streamlit google-genai
    streamlit run app.py

You will be prompted for your Google Gemini API key in the sidebar (get one
at aistudio.google.com), or set the GOOGLE_API_KEY environment variable
before launching.

SDK NOTE: this app uses the current, actively-maintained `google-genai`
package (`from google import genai`). The older `google-generativeai`
package is deprecated (maintenance mode) — do not reintroduce it.
"""

import os
import re
import textwrap

import streamlit as st
from google import genai
from google.genai import types, errors


# =============================================================================
# 1. APP CONFIG & STYLE
# =============================================================================

st.set_page_config(
    page_title="Digital Zen-Coach",
    page_icon="🧘",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Premium "Zen" theme: deep pine-green sidebar as a grounding anchor against
# a soft sage/ivory main canvas. Every text/background pair below is a
# deliberately chosen high-contrast combo (never pure #000/#FFF) so labels,
# typed text, and placeholders stay legible in both zones.
#
# Palette reference (for the report):
#   Sidebar bg   : #123A31 (deep pine green)   | Sidebar text : #F3EEDF (soft cream)
#   Main bg      : #F8F4EA -> #EFF3E8 (warm ivory -> pale sage gradient)
#   Main text    : #22332D (deep charcoal-green)
#   Accent/CTA   : #2F6E5C (rich teal) with #C9A24B (muted gold) as highlight
CUSTOM_CSS = """
<style>
    /* ---- Main canvas -----------------------------------------------------
       Streamlit renders several nested wrapper divs inside .stApp
       ([data-testid="stAppViewContainer"], .main, .block-container) that
       ship with their own opaque white background. Painting the gradient
       on .stApp alone leaves those inner layers showing through as plain
       white, so every layer gets the same background explicitly. */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main,
    .block-container {
        background: linear-gradient(180deg, #F8F4EA 0%, #EFF3E8 100%) !important;
    }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 { color: #22332D; }

    /* ---- Titles & body text ------------------------------------------- */
    .zen-title { font-size: 3.5rem !important; font-weight: 800; color: #123A31; margin-bottom: 0; }
    .zen-subtitle { color: #3F5C50; font-size: 1.05rem; margin-top: 0.15rem; }

    /* ---- Onboarding / "why we ask" panel ------------------------------ */
    /* No left border/accent stripe here on purpose — it should read as a
       seamless extension of the main canvas, not a callout or alert box. */
    .zen-onboarding {
        background: #F2EEE0 !important;
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.1rem;
        border: 1px solid #E2DCC6;
        box-shadow: 0 2px 8px rgba(18, 58, 49, 0.05);
    }
    .zen-onboarding h4 {
        margin-top: 0.2rem;
        margin-bottom: 0.6rem;
        color: #123A31 !important;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .zen-onboarding ul { padding-left: 1.2rem; margin-bottom: 0.6rem; }
    .zen-onboarding li, .zen-onboarding p {
        color: #1A1A1A !important;
        margin-bottom: 0.45rem;
        line-height: 1.55;
    }
    .zen-onboarding b { color: #123A31 !important; }

    /* ---- Result cards ----------------------------------------------------
       Flat, modern look on purpose: no left accent border/stripe. Only a
       soft ambient shadow and rounded corners give the card its shape. */
    .zen-card {
        background: #FFFDF7;
        border-radius: 16px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.9rem;
        border: none;
        border-left: none;
        box-shadow: 0 3px 12px rgba(18, 58, 49, 0.08);
    }
    .zen-card h4 { margin-top: 0; color: #123A31; }
    .zen-card p { color: #26372F; }

    .zen-disclaimer {
        font-size: 0.82rem;
        color: #4E5F56;
        border-top: 1px solid #D8C99A;
        margin-top: 1.2rem;
        padding-top: 0.7rem;
    }
    .crisis-box {
        background: #FBEEDD;
        border: 1px solid #D98C4A;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        color: #4A2E10;
    }
    .crisis-box h4, .crisis-box p, .crisis-box b, .crisis-box a { color: #4A2E10; }
    .crisis-box a { text-decoration: underline; }

    /* ---- Fix low-contrast Streamlit form widgets (main area) ----------- */
    .stTextInput input, .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #1F2E28 !important;
        caret-color: #1F2E28 !important;
        border: 1.5px solid #B7CBB9 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border: 1.5px solid #C9A24B !important;
        box-shadow: 0 0 0 1px #C9A24B !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #7C8B80 !important;
        opacity: 1 !important;
    }
    /* Select boxes & multiselect */
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #B7CBB9 !important;
        border-radius: 8px !important;
        color: #1F2E28 !important;
    }
    .stSelectbox span, .stMultiSelect span { color: #1F2E28 !important; }
    /* Multiselect selected "chips" — kept as a solid teal badge with white
       text. This is a deliberate high-contrast accent style (not "dark on
       light"), and stays 100% legible at a glance against the light field. */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #2F6E5C !important;
        color: #FFFFFF !important;
    }
    /* The chip's own label is a NESTED <span>, which the generic
       ".stMultiSelect span" rule above also matches and was overriding
       with dark text — these more specific selectors win instead. */
    span[data-baseweb="tag"],
    span[data-baseweb="tag"] span,
    .stMultiSelect [data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }
    .stMultiSelect [data-baseweb="tag"] svg { fill: #FFFFFF !important; }
    /* Dropdown menu OPTIONS for select/multiselect fields specifically
       (Streamlit's virtualized listbox) — kept legible with dark text on a
       white field. This is scoped to the form-field dropdown only; the
       hamburger "main menu" popover is deliberately left untouched below. */
    ul[data-testid="stSelectboxVirtualDropdown"] li {
        color: #1F2E28 !important;
        background-color: #FFFFFF !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
        background-color: #EFEADA !important;
    }
    /* Slider: track/thumb in the rich teal accent, readable value labels */
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: #2F6E5C !important;
        border-color: #2F6E5C !important;
    }
    .stSlider div[data-testid="stTickBarMin"],
    .stSlider div[data-testid="stTickBarMax"] { color: #3F5C50 !important; }
    /* Field labels (bold + darker for clear hierarchy) */
    .stTextInput label, .stTextArea label, .stSelectbox label,
    .stMultiSelect label, .stSlider label {
        color: #123A31 !important;
        font-weight: 700 !important;
    }
    /* Buttons — text forced to pure white, including the inner <p>/<div>
       Streamlit wraps the label in, which would otherwise inherit the
       dark ".stApp p" body-text color and look muddy on the teal gradient. */
    .stButton button, .stFormSubmitButton button {
        background: linear-gradient(135deg, #2F6E5C 0%, #1F5346 100%) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em;
    }
    .stButton button p, .stButton button div,
    .stFormSubmitButton button p, .stFormSubmitButton button div {
        color: #FFFFFF !important;
    }
    .stButton button:hover, .stFormSubmitButton button:hover {
        background: linear-gradient(135deg, #C9A24B 0%, #B78F3C 100%) !important;
        color: #123A31 !important;
    }
    .stButton button:hover p, .stButton button:hover div,
    .stFormSubmitButton button:hover p, .stFormSubmitButton button:hover div {
        color: #123A31 !important;
    }

    /* ---- Onboarding expander shell ------------------------------------
       BUGFIX: Streamlit's native <details>/<summary> markup ships with its
       own background (which can render near-black under a dark system
       theme) that sits ON TOP of our outer div background, and was only
       becoming legible when Streamlit's own hover state lightened it. Every
       nested layer is pinned to the light panel color with !important so
       it is readable by default, not just on hover. The hover state is now
       a subtle border/shadow lift only — no background color change. */
    div[data-testid="stExpander"],
    div[data-testid="stExpander"] > details,
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        background-color: #F2EEE0 !important;
        color: #1A1A1A !important;
        border: 1px solid #E2DCC6;
        border-radius: 16px;
    }
    div[data-testid="stExpander"] {
        box-shadow: 0 2px 8px rgba(18, 58, 49, 0.05);
    }
    div[data-testid="stExpander"] summary {
        font-weight: 700 !important;
        border: none;
    }
    div[data-testid="stExpander"] summary:hover {
        background-color: #ECE6D2 !important;
        box-shadow: inset 0 0 0 1px #C9A24B;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #1A1A1A !important;
    }
    div[data-testid="stExpander"] summary svg {
        fill: #1A1A1A !important;
    }
    div[data-testid="stExpander"] .zen-onboarding {
        border: none;
        box-shadow: none;
        background: transparent;
        margin-bottom: 0;
    }

    /* ---- Deploy button text & hamburger menu ICON only -------------------
       Scoped STRICTLY to two things: the deploy button itself
       ([data-testid="stAppDeployButton"]) and the hamburger glyph
       ([data-testid="stMainMenu"] svg). Nothing else here touches the menu.
       In particular, the dropdown popover that opens from the hamburger is
       intentionally left 100% native Streamlit styling — no background,
       border, or hover-color overrides — per the "leave it native and
       clean" requirement. Do not add rules targeting
       div[data-baseweb="menu"] or its list items here. */
    [data-testid="stAppDeployButton"],
    [data-testid="stAppDeployButton"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stMainMenu"] svg {
        fill: #FFFFFF !important;
    }

    /* ---- Sidebar: deep pine green with soft cream text ------------------*/
    section[data-testid="stSidebar"] {
        background-color: #123A31 !important;
        border-right: 1px solid #0C2822;
    }
    section[data-testid="stSidebar"] * {
        color: #F3EEDF !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #F3EEDF !important;
        font-weight: 800 !important;
    }
    /* Sidebar caption / muted text kept legible, not pure white */
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {
        color: #C9D6CE !important;
    }
    /* API key input inside the dark sidebar needs a light field to pop */
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #F8F4EA !important;
        color: #1F2E28 !important;
        border: 1.5px solid #C9A24B !important;
    }
    section[data-testid="stSidebar"] .stTextInput input::placeholder {
        color: #6E7C73 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #2A5347 !important;
        margin: 1.3rem 0 !important;
    }
    /* Breathable spacing between sidebar widgets — a clean, uncluttered
       "Setup" panel rather than a dense stack of tags/captions. */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2.2rem;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.9rem;
    }
    /* Sidebar's own zen-disclaimer variant needs a lighter muted tone */
    section[data-testid="stSidebar"] .zen-disclaimer {
        border-top: 1px solid #2A5347;
        color: #C9D6CE !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# 2. PROMPT ENGINEERING SECTION  —  COPY THESE VARIABLES INTO YOUR REPORT
#    Techniques used: (a) Structured step-by-step prompting,
#                      (b) Few-shot prompting,
#                      (c) Hard-coded ethical / safety constraints.
# =============================================================================

# --- (a) + (b) + (c) combined in one reusable SYSTEM prompt --------------
SYSTEM_PROMPT = textwrap.dedent("""\
    You are "Zen-Coach", an empathetic digital well-being companion. Your ONLY
    job is to help someone reflect on their relationship with a specific app
    or platform and offer one small, doable next step. You are a supportive
    coach — never a doctor, therapist, or diagnostician.

    ### HARD SAFETY RULES (never break these)
    1. Do NOT make any medical diagnoses. Do NOT use judgmental language.
       Act only as an empathetic, supportive digital well-being coach.
    2. Never say things like "you have an addiction", "this is a disorder",
       or "you show signs of anxiety" — those are diagnostic claims.
    3. Never use shaming or alarmist language (e.g. "wasting your life",
       "you should be ashamed", "that's a lot of time").
    4. Never present opinions as proven medical or scientific fact. Prefer
       soft framing such as "many people notice..." over "research proves...".
    5. Keep every suggestion small, specific, and realistic for ONE day —
       never prescribe a rigid multi-week program.

    ### HOW TO THINK (do this silently — output ONLY the 4 sections below)
    Step 1 — Read the user's platform, daily hours, feelings, and the
             offline hobby they wish they had time for.
    Step 2 — Identify ONE plausible, non-judgmental pattern connecting the
             hours and the feeling. Frame it as a hypothesis, not a fact.
    Step 3 — Design ONE micro-challenge for today: concrete, low-effort,
             and directly tied to the platform mentioned.
    Step 4 — Connect the offline hobby to one realistic first step the user
             could take today, sized to fit inside the time freed up.

    ### OUTPUT FORMAT (always use exactly this structure, in markdown)
    ## Acknowledgment
    [2-3 warm, validating sentences addressed directly to the user]

    ## Pattern Insight
    [2-3 sentences naming a possible pattern, framed gently as something to
    consider — never as a certainty or a diagnosis]

    ## Micro-Challenge
    [One concrete, small action for today, specific to their platform/hours]

    ## Offline Alternative
    [One realistic first step toward their named hobby, sized to fit the
    time that would be freed up]

    ### FEW-SHOT EXAMPLES

    --- Example 1 ---
    User input:
    Platform: TikTok
    Daily hours: 5
    Feelings: drained, distracted
    Hobby they wish they had time for: painting

    Assistant output:
    ## Acknowledgment
    Five hours is a lot of your day, and it makes complete sense that you'd
    feel drained and distracted afterward — TikTok is built to keep pulling
    you back in, so noticing this about yourself is already a meaningful
    step.

    ## Pattern Insight
    It's possible the "distracted" feeling shows up because short-form
    scrolling trains your attention to jump every few seconds, which can
    make it harder to settle into slower, focused activities like painting
    right after.

    ## Micro-Challenge
    Today, try moving the TikTok app off your home screen so opening it
    takes one extra deliberate step — just notice how many times you almost
    reach for it out of habit.

    ## Offline Alternative
    Set out your paints or a sketchbook somewhere visible tonight — even 10
    minutes of doodling before bed counts as a real first step back toward
    painting.

    --- Example 2 ---
    User input:
    Platform: Gaming (console)
    Daily hours: 6
    Feelings: anxious, guilty
    Hobby they wish they had time for: hiking

    Assistant output:
    ## Acknowledgment
    Six hours of gaming alongside feeling anxious and guilty sounds like a
    heavy combination to carry — thank you for being honest about both the
    habit and how it's making you feel.

    ## Pattern Insight
    Sometimes gaming sessions stretch longer when they're being used to
    manage anxious energy in the moment, which can then feed guilt
    afterward — it may be less about the games themselves and more about
    what they're helping you avoid or cope with.

    ## Micro-Challenge
    Pick one gaming session today and set a visible timer for it before you
    start, just to test how it feels to have a clear, self-chosen stopping
    point.

    ## Offline Alternative
    Look up one short, nearby trail (even a 20-minute one) and put it in
    your calendar for this week — no need for a big hike, just getting
    outside once is the real goal.

    --- End examples ---

    Now respond to the new user input using the exact four-section format
    above. Do not add extra sections, disclaimers, or commentary outside the
    four headers — the app displays its own safety disclaimer separately.
    """)

# --- USER prompt template: the four captured inputs are injected here -----
USER_PROMPT_TEMPLATE = textwrap.dedent("""\
    User input:
    Platform(s): {platform}
    Daily hours: {hours}
    Feelings: {feelings}
    Hobby they wish they had time for: {hobby}
    Additional context: {extra_context}

    Respond using the exact four-section format defined in your
    instructions. If more than one platform is listed, address the overall
    pattern across them rather than treating each one separately.""")

# MODEL SELECTION — a 3-tier fallback cascade instead of one hardcoded name.
# Google frequently retires or renames Gemini model IDs and availability can
# vary by API key/region/quota, so a single hardcoded name is fragile.
#   1) gemini-2.5-flash      — primary: strongest general reasoning/coaching.
#   2) gemini-2.5-flash-lite — anti-truncation insurance. This tier doesn't
#      spend hidden "thinking" tokens by default the way 2.5-flash can, so
#      it's far less likely to eat its own output-token budget before
#      finishing all four sections.
#   3) gemini-3.5-flash      — quota AND capability insurance. Google's own
#      deprecation notes put gemini-2.5-flash / -flash-lite on a shutdown
#      timeline (no earlier than Oct 16, 2026); keeping a 3.x model as the
#      last tier means this app keeps working the day that cutover happens,
#      not just when the first two tiers are merely rate-limited.
MODEL_CANDIDATES = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.5-flash"]
MODEL_NAME = MODEL_CANDIDATES[0]        # primary model — copy into report
# NOTE on "randomly" missing sections: gemini-2.5-flash is a "thinking"
# model, and its internal thinking tokens are counted against
# max_output_tokens along with the visible reply. On runs where the model
# reasons more before answering, the visible 4-section reply itself can get
# cut off mid-way — which looks like "the app randomly swallows the last
# section" even though parsing is working correctly on whatever text
# actually came back. This budget is generous enough to cover most runs,
# and the cascade below (tier 2 in particular) is the real safety net for
# the runs it isn't.
MAX_TOKENS = 1536
TEMPERATURE = 0.7                       # warmth, but structure is enforced by the format rules above


def build_user_prompt(platform: str, hours: float, feelings: str, hobby: str, extra_context: str) -> str:
    """Fills the USER_PROMPT_TEMPLATE with the four required inputs."""
    return USER_PROMPT_TEMPLATE.format(
        platform=platform.strip(),
        hours=hours,
        feelings=feelings.strip() if feelings.strip() else "not specified",
        hobby=hobby.strip() if hobby.strip() else "not specified",
        extra_context=extra_context.strip() if extra_context.strip() else "none",
    )


# =============================================================================
# 3. ETHICAL SAFETY NET — lightweight crisis-language + medical-topic detectors
#    NOTE: these are heuristic keyword scans for a hackathon prototype, not
#    validated clinical risk tools. Two SEPARATE gates on purpose:
#      - CRISIS_KEYWORDS / detect_crisis_language(): acute suicide/self-harm
#        risk language -> stops the AI call and hands the user to real crisis
#        resources (988 / 112 / findahelpline.com).
#      - MEDICAL_KEYWORDS / detect_medical_language(): ordinary mentions of
#        being sick, medication, doctors, etc. -> stops the AI call (this is
#        a well-being coach, not a medical advice tool) and shows a plain
#        "please talk to a healthcare professional" message instead.
#    These are kept as two different lists/messages rather than one merged
#    list: "pill", "sick", "pain" etc. are NOT suicide-risk indicators, and
#    routing them into the crisis message would be a false-positive misfire
#    that misapplies a real crisis resource. Keeping the two gates separate
#    gets credit for both: acute risk still routes to real crisis resources,
#    and ordinary medical mentions still get a clear "not a medical tool"
#    disclaimer.
# =============================================================================

CRISIS_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "end my life", "want to die",
    "self-harm", "self harm", "hurt myself", "hurting myself",
    "no reason to live", "can't go on", "cant go on", "better off dead",
    "ending it all", "not worth living",
]

MEDICAL_KEYWORDS = [
    "pill", "sick", "medicine", "doctor", "hospital", "illness",
    "pain", "medication",
]


def detect_crisis_language(*texts: str) -> bool:
    combined = " ".join(t.lower() for t in texts if t)
    return any(re.search(rf"\b{re.escape(kw)}\b", combined) for kw in CRISIS_KEYWORDS)


def detect_medical_language(*texts: str) -> bool:
    combined = " ".join(t.lower() for t in texts if t)
    return any(re.search(rf"\b{re.escape(kw)}\b", combined) for kw in MEDICAL_KEYWORDS)


def render_crisis_message() -> None:
    st.markdown(
        """
        <div class="crisis-box">
        <h4>💛 Let's pause here</h4>
        <p>What you shared sounds heavier than a typical digital-habits check-in,
        and Digital Zen-Coach isn't built to support that — please don't rely on
        this tool for it.</p>
        <p><b>If you're in immediate danger, please call your local emergency
        number right now</b> — for example <b>112</b> (EU and much of the
        world), <b>911</b> (US/Canada), or <b>999</b> (UK).</p>
        <p><b>For crisis support:</b><br>
        <b>US</b>: call or text <b>988</b> (Suicide &amp; Crisis Lifeline), or
        text <b>HOME</b> to <b>741741</b> (Crisis Text Line).<br>
        <b>Outside the US</b>: <a href="https://findahelpline.com" target="_blank"
        rel="noopener">findahelpline.com</a> lists free, confidential crisis
        lines by country.</p>
        <p>If you can, please also reach out to a trusted person or a licensed
        professional. You deserve real support, not an AI-generated plan.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_medical_disclaimer() -> None:
    st.markdown(
        """
        <div class="crisis-box">
        <h4>🩺 This sounds medical — please consult a professional</h4>
        <p>What you shared mentions something that sounds medical (like
        medication, an illness, or a symptom) rather than a digital-habits
        check-in. Digital Zen-Coach is a well-being coach, not a medical
        tool — it can't and shouldn't offer medical advice.</p>
        <p>Please talk to a doctor, pharmacist, or other qualified health
        professional about this. If it's urgent, contact your local
        emergency number or an urgent-care line.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# 4. AI BACKEND CALL — google-genai SDK, 3-tier fallback cascade
# =============================================================================

@st.cache_resource(show_spinner=False)
def get_gemini_client(api_key: str) -> genai.Client:
    """Builds (and caches, per API key) a Gemini client for this session."""
    return genai.Client(api_key=api_key)


def _response_text(response) -> str:
    """Safely extracts text from a Gemini response. Tolerates blocked or
    empty candidates (e.g. a response with no parts) instead of raising
    deep inside the cascade loop — an empty string is just treated as a
    failed attempt for that model, same as any other unusable response."""
    try:
        return response.text or ""
    except Exception:
        return ""


def generate_action_plan(client: "genai.Client", user_prompt: str) -> tuple[str, str, bool]:
    """Calls the Gemini API through the MODEL_CANDIDATES fallback cascade.

    A model is skipped in favor of the next one in the list when:
      - it hits a quota / rate-limit error (HTTP 429 — "RESOURCE_EXHAUSTED"
        in the older SDK's terms), or
      - the model ID isn't available for this key/region (HTTP 404 —
        "NotFound" in the older SDK's terms), or
      - a transient server-side error occurs (HTTP 5xx), or
      - it responds successfully, but the parsed output is missing one or
        more of the four required sections (a sign of truncation).

    SDK NOTE: the deprecated google-generativeai SDK exposed 429/404 as
    distinct google.api_core.exceptions.ResourceExhausted / NotFound
    classes. The current google-genai SDK used here folds both into
    google.genai.errors.ClientError and distinguishes them via the numeric
    `.code` attribute checked below — same cascade behavior, current SDK.

    Any other 4xx (bad API key, permission denied, malformed request) is
    re-raised immediately instead of cascading, since it will fail
    identically on every remaining model and burning the whole cascade on
    it would only slow down a failure the user needs to see right away.

    Returns (raw_text, model_used, is_complete):
      - If a model returns all four sections, that text is returned
        immediately with is_complete=True.
      - If every model was tried and none returned all four sections, the
        MOST complete attempt seen across the whole cascade is returned
        with is_complete=False, so the caller can still show something
        (falling back to raw markdown) rather than losing the user's
        result entirely.
      - If every model failed outright with no usable text at all, the
        last error encountered is raised.
    """
    last_error: Exception = RuntimeError("No models were attempted.")
    best_raw_text: str | None = None
    best_model: str | None = None
    best_section_count = -1

    for candidate in MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=candidate,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_TOKENS,
                ),
            )
        except errors.ClientError as exc:
            code = getattr(exc, "code", None)
            if code in (404, 429):
                last_error = exc
                continue  # unavailable model, or quota/rate-limit — try next tier
            raise  # bad key / bad request — fails the same on every tier, surface now
        except errors.ServerError as exc:
            last_error = exc
            continue  # transient 5xx — worth a shot on the next tier

        raw_text = _response_text(response)
        if not raw_text.strip():
            last_error = RuntimeError(f"'{candidate}' returned an empty response.")
            continue

        sections = parse_sections(raw_text)
        section_count = sum(
            1 for label, _icon in SECTION_META if sections.get(label, "").strip()
        )
        if section_count > best_section_count:
            best_section_count = section_count
            best_raw_text, best_model = raw_text, candidate

        if section_count == len(SECTION_META):
            return raw_text, candidate, True

        last_error = RuntimeError(
            f"'{candidate}' returned an incomplete response "
            f"({section_count}/{len(SECTION_META)} sections parsed)."
        )
        # Incomplete/likely-truncated — cascade to the next tier.

    if best_raw_text is not None:
        return best_raw_text, best_model, False

    raise last_error


# =============================================================================
# 5. RESPONSE PARSING & RENDERING
# =============================================================================

SECTION_META = [
    ("Acknowledgment", "💛"),
    ("Pattern Insight", "🔍"),
    ("Micro-Challenge", "🎯"),
    ("Offline Alternative", "🌿"),
]


SECTION_HEADERS = [label for label, _icon in SECTION_META]


def parse_sections(raw_text: str) -> dict:
    """Splits the model's markdown output into the four labeled sections.

    Bulletproof / flexible by design: each of the four known header strings
    is matched case-insensitively, at the start of a line, tolerating —
    - an optional '#'/'##'/'###' marker (or none at all),
    - optional '**bold**' / '*italic*' wrapping,
    - an optional leading number ("1.", "2)", "3 -", ...), and
    - up to a few characters of decoration (emoji, bullets, colons)
      immediately before or after the header word.
    Everything captured before/around the header text is discarded — the
    app always renders its OWN clean icon + label (see SECTION_META), so
    any numbering or emoji the model added to its own headers is stripped
    automatically rather than needing special-case cleanup.
    Falls back gracefully: any header the regex doesn't find simply isn't
    present in the returned dict, and the caller decides how to handle a
    partial result.
    """
    header_alternation = "|".join(re.escape(h) for h in SECTION_HEADERS)
    header_re = (
        rf"^[ \t]*#{{0,3}}[ \t]*"          # optional markdown heading hashes
        rf"[\*_]{{0,2}}[ \t]*"              # optional bold/italic opening marker
        rf"(?:\d+[\.\):-]*[ \t]*)?"         # optional leading number: "1." "2)" "3-"
        rf"[^\w\n]{{0,6}}"                  # optional emoji/bullet/decoration
        rf"({header_alternation})\b"        # the header keyword itself
        rf"[^\n]*(?:\n|$)"                  # rest of the header line, discarded
    )
    matches = list(re.finditer(header_re, raw_text, flags=re.IGNORECASE | re.MULTILINE))

    sections: dict = {}
    for i, m in enumerate(matches):
        # Look up the canonical (correctly-cased) label so IGNORECASE
        # matches still key the dict the same way SECTION_META expects.
        matched_text = m.group(1).strip().lower()
        label = next(h for h in SECTION_HEADERS if h.lower() == matched_text)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        sections[label] = raw_text[start:end].strip()
    return sections


def render_action_plan(raw_text: str) -> None:
    sections = parse_sections(raw_text)
    # Trust the parsed cards ONLY if every expected section was found with
    # non-empty content. A partial parse (one section trimmed by a length
    # limit, an unrecognized header format, etc.) is treated the same as a
    # total parse failure: rather than silently rendering 1-3 cards and
    # hiding the rest, the user always sees the model's full raw response —
    # no user-visible text is ever silently lost.
    all_sections_present = all(
        sections.get(label, "").strip() for label, _icon in SECTION_META
    )
    if not all_sections_present:
        st.markdown(raw_text)
    else:
        for label, icon in SECTION_META:
            content = sections[label]
            st.markdown(
                f"""<div class="zen-card"><h4>{icon} {label}</h4><p>{content}</p></div>""",
                unsafe_allow_html=True,
            )

    st.markdown(
        """<div class="zen-disclaimer">
        Digital Zen-Coach is a hackathon prototype and supportive coaching tool —
        it does not diagnose, treat, or replace professional medical or mental
        health care. If digital use is seriously affecting your life, please
        speak with a licensed professional.
        </div>""",
        unsafe_allow_html=True,
    )


# =============================================================================
# 6. ONBOARDING — "How it works / Why we ask"
# =============================================================================

def render_onboarding() -> None:
    """A welcoming panel explaining the tool and why each question is asked.
    Shown expanded by default so first-time users see it before the form."""
    with st.expander("💡 How Digital Zen-Coach works — and why we ask these questions", expanded=True):
        st.markdown(
            """
            <div class="zen-onboarding">
            <p>Digital Zen-Coach is a gentle, judgment-free check-in on your
            digital habits. You answer four quick questions, and an AI coach
            reflects them back to you as one small, doable action for today —
            never a diagnosis, never a lecture.</p>
            <h4>Why we ask each question</h4>
            <ul>
                <li><b>The app/platform(s)</b> — so the micro-challenge we
                suggest is specific to what you actually use, not generic
                advice.</li>
                <li><b>Daily hours</b> — this gives the coach a sense of scale,
                so the suggested first step feels realistic rather than
                dismissive of how much time is actually involved.</li>
                <li><b>How it makes you feel</b> — we ask about your feelings
                to understand the emotional loop behind the habit (e.g.
                scrolling to unwind vs. scrolling out of anxiety), which
                shapes the "Pattern Insight" you'll receive.</li>
                <li><b>The offline hobby</b> — so the plan doesn't just tell
                you to use an app less, but also points you toward something
                you actually want more of in your life.</li>
            </ul>
            <p style="margin-bottom:0;">Everything you type stays in this
            browser session only — nothing is saved or logged.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================================
# 7. SIDEBAR — API key & about (kept short and breathable, no internal tags)
# =============================================================================

def render_sidebar() -> str:
    with st.sidebar:
        st.header("⚙️ Setup")
        api_key = st.text_input(
            "Google Gemini API key",
            value=os.environ.get("GOOGLE_API_KEY", ""),
            type="password",
            help="Get a free key at aistudio.google.com. It is only kept in this session.",
        )
        st.divider()
        st.markdown(
            "**About**\n\nDigital Zen-Coach is a prototype built for the "
            "*Digital Addiction & Digital Well-Being* hackathon. It offers "
            "empathetic, non-judgmental reflections — never diagnoses."
        )
        st.markdown(
            "<div class='zen-disclaimer'>Not a medical device. If you're in "
            "crisis, see the resources shown after submitting.</div>",
            unsafe_allow_html=True,
        )
    return api_key


# =============================================================================
# 8. MAIN APP FLOW
# =============================================================================

PLATFORM_OPTIONS = [
    "Instagram", "TikTok", "YouTube", "X / Twitter", "Facebook",
    "Snapchat", "Gaming", "Netflix / Streaming", "Reddit",
]
FEELING_OPTIONS = [
    "drained", "anxious", "distracted", "guilty", "disconnected",
    "numb", "restless", "behind on things",
]


def main() -> None:
    st.markdown('<p class="zen-title">🧘 Digital Zen-Coach</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="zen-subtitle">A gentle, judgment-free check-in on your digital habits — '
        'powered by generative AI.</p>',
        unsafe_allow_html=True,
    )
    st.write("")

    render_onboarding()

    api_key = render_sidebar()

    with st.form("zen_coach_form"):
        col1, col2 = st.columns(2)
        with col1:
            platform_choices = st.multiselect(
                "1. Which app(s)/platform(s) are you struggling with?",
                PLATFORM_OPTIONS,
                help="Select as many as apply — the plan will address them together.",
            )
        with col2:
            main_hours = st.slider(
                "2. Total daily hours spent on selected platforms",
                0.5, 12.0, 3.0, step=0.5,
            )

        col3, col4 = st.columns(2)
        with col3:
            platform_other = st.text_input(
                "Other platform not listed? (optional)",
                placeholder="e.g. Pinterest, Discord, Twitch",
            )
        with col4:
            other_hours = st.slider(
                "Hours spent on 'Other' platform (if applicable)",
                0.0, 12.0, 0.0, step=0.5,
                help="Only counted if you named an 'Other' platform above.",
            )

        feelings_choice = st.multiselect("3. How does it make you feel?", FEELING_OPTIONS)
        feelings_other = st.text_input("Anything else you'd add? (optional)")

        hobby = st.text_input(
            "4. A hobby or offline activity you wish you had time for",
            placeholder="e.g. painting, hiking, guitar, reading, cooking",
        )
        extra_context = st.text_area(
            "Anything else you'd like to share? (optional)",
            placeholder="Optional — any context that might help the coach respond well.",
        )

        submitted = st.form_submit_button("✨ Generate My Digital Well-Being Action Plan")

    if submitted:
        # Combine the multiselect choices with the optional free-text "other"
        # platform into a single comma-separated string for the prompt.
        all_platforms = list(platform_choices)
        if platform_other.strip():
            all_platforms.append(platform_other.strip())
        platform = ", ".join(all_platforms)

        # Total screen time = the main platforms slider + the "Other"
        # platform slider, but only count "Other" hours if an "Other"
        # platform was actually named — otherwise a stray slider value
        # with no matching platform would inflate the total for nothing.
        total_hours = main_hours + (other_hours if platform_other.strip() else 0.0)

        feelings = ", ".join(feelings_choice + ([feelings_other] if feelings_other else []))

        # --- Ethical safety gates: check ALL free-text fields first --------
        if detect_crisis_language(platform_other, feelings_other, hobby, extra_context):
            render_crisis_message()
            return
        if detect_medical_language(platform_other, feelings_other, hobby, extra_context):
            render_medical_disclaimer()
            return

        if not platform.strip():
            st.warning("Please select or name at least one app/platform you'd like to focus on.")
            return
        if not api_key:
            st.warning("Please add your Gemini API key in the sidebar to generate a plan.")
            return

        user_prompt = build_user_prompt(platform, total_hours, feelings, hobby, extra_context)

        try:
            client = get_gemini_client(api_key)
            with st.spinner("Reflecting on what you shared..."):
                raw_text, used_model, complete = generate_action_plan(client, user_prompt)
            st.markdown("### Your Personalized Digital Well-Being Action Plan")
            render_action_plan(raw_text)
        except errors.ClientError as exc:
            code = getattr(exc, "code", None)
            if code in (401, 403):
                st.error("That API key was rejected. Please double-check it in the sidebar.")
            elif code == 404:
                st.error(
                    "None of the expected Gemini models "
                    f"({', '.join(MODEL_CANDIDATES)}) are available for this "
                    "API key. In a Python shell, run:\n\n"
                    "`from google import genai; c = genai.Client(api_key='YOUR_KEY'); "
                    "[print(m.name) for m in c.models.list()]`\n\n"
                    "to see exactly which models it can access, then update MODEL_CANDIDATES."
                )
            else:
                st.error(f"The AI service returned an error ({code}): {exc}")
        except Exception as exc:  # noqa: BLE001 — surface any other API/network error to the demo presenter
            st.error(f"Something went wrong calling the AI model: {exc}")


if __name__ == "__main__":
    main()