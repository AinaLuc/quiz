import os
import json
import uuid
import base64
from datetime import datetime, timedelta
from typing import Optional

import resend
import stripe
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, jsonify, send_file, render_template, redirect
from openai import OpenAI
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, numbers
from openpyxl.utils import get_column_letter
from dotenv import load_dotenv

from emails import email_1_html, email_2_html, email_3_html, email_4_html, email_5_html, email_abandoned_html

load_dotenv()
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
resend.api_key = os.environ.get('RESEND_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@example.com')

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# In-memory plan cache: file_id -> plan dict
# In production replace with Redis or a DB
_PLAN_CACHE: dict = {}
# Unsubscribe tokens: token -> {"email": ..., "file_id": ...}
_UNSUB_TOKENS: dict = {}

# ─────────────────────────────────────────────
# EMAIL SCHEDULER
# ─────────────────────────────────────────────
scheduler = BackgroundScheduler()
scheduler.start()


def send_email(to: str, subject: str, html: str, attachment_path: Optional[str] = None):
    """Send a single transactional email via Resend."""
    params: dict = {
        "from": FROM_EMAIL,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        filename = os.path.basename(attachment_path)
        params["attachments"] = [{"filename": filename, "content": content}]
    try:
        app.logger.info(f"Attempting to send email from {FROM_EMAIL} to {to}...")
        if attachment_path:
            app.logger.info(f"Attachment path: {attachment_path} (exists: {os.path.exists(attachment_path)})")
        
        r = resend.Emails.send(params)
        app.logger.info(f"Resend success: {r.get('id')} sent to {to}")
    except Exception as exc:
        # Log but don't crash — email failure should not break the webhook
        app.logger.error(f"CRITICAL: Resend failed for {to}. Error: {exc}")
        app.logger.error(f"Using FROM_EMAIL: {FROM_EMAIL}")


def schedule_email_sequence(to_email: str, name: str, file_id: str, host_url: str):
    """
    Queue all 5 emails using APScheduler DateTrigger.
    Delays: Day 0 (now), Day 1, Day 2, Day 4, Day 6.
    """
    free_url        = f"{host_url}download/free/{file_id}"
    payment_url     = f"{host_url}payment?file_id={file_id}"
    free_path       = f"/tmp/free_{file_id}.xlsx"
    now             = datetime.now()

    # Unsubscribe token unique per subscriber
    unsub_token = str(uuid.uuid4())
    _UNSUB_TOKENS[unsub_token] = {"email": to_email, "file_id": file_id}
    unsubscribe_url = f"{host_url}unsubscribe/{unsub_token}"

    sequence = [
        (1, "The #1 thing coaches who fill their calendar do differently",
         email_2_html(name, free_url, payment_url, unsubscribe_url), False),
        (2, "What most coaches skip — and why it quietly kills their revenue",
         email_3_html(name, free_url, payment_url, unsubscribe_url), False),
        (4, f"{name.split()[0] if name else 'Coach'}, here's what stood out in your quiz answers",
         email_4_html(name, free_url, payment_url, unsubscribe_url), False),
        (6, "This is the last time I'll mention it",
         email_5_html(name, free_url, payment_url, unsubscribe_url), False),
    ]

    for delay_days, subject, html, attach in sequence:
        run_at = now + timedelta(days=delay_days)
        attachment = free_path if attach else None
        scheduler.add_job(
            send_email,
            trigger="date",
            run_date=run_at,
            args=[to_email, subject, html, attachment],
            id=f"{file_id}_email_{delay_days}",
            replace_existing=True,
        )
    app.logger.info(f"Scheduled Day 1-6 drip sequence for {to_email}")


SYSTEM_PROMPT = """You are an expert coaching business strategist and offer design specialist.

Your job is to take quiz answers from someone wanting to start a coaching business 
and return a complete personalised coaching business plan as structured JSON.

RULES:
- Return ONLY valid JSON. No markdown. No explanation. No code blocks.
- Every field must be specific to THEIR answers — never generic
- Use the client's own words from Q5 in the trigger pain section
- Never use coaching platitudes like do the inner work or step into your power
- The offer sentence must follow this formula exactly:
  I help [WHO] who [PROBLEM IN THEIR EXACT WORDS] to [TANGIBLE LIFE EVENT OUTCOME] 
  in [TIMEFRAME] without [THEIR NUMBER 1 OBJECTION]
- Action Plan Focus Titles: MUST be high-urgency and evocative (e.g. "Scale Without You", 
  "The $10k Authority Reset", "Automated Client Acquisition", "The Flagship Launch").
- include_paid_funnel should be true only if Q15_interest is Yes AND Q15 answer is NOT No budget right now
- Revenue fields (year1_low_units, year1_low_revenue, year1_high_units, year1_high_revenue,
  year2_units, year2_revenue, price_numeric) MUST be plain integers — no $ signs, no text
- Funnel fields (monthly_clients, monthly_revenue_low, monthly_revenue_high) MUST be plain integers
- For competitors: identify 3 REAL named competitors in the same niche with actual pricing and
  business model details — never invent fictional coaches

MARKETING STRATEGY RULES:
- Every channel gets a full deep-dive: profile/setup audit, 3 content pillars
  with 3 hooks each, 3 complete ready-to-publish sample posts (150-250 words),
  a 10-entry 2-week content calendar, 3 quick wins, and 5 KPIs.
- NEVER write generic advice. Every field must be specific to their niche,
  their client avatar, and use the exact pain words from Q5.
- sample_post must be a complete publish-ready post — not a description of a post.
  Write it as if you are the coach posting it today.
- hooks must be scroll-stopping first lines. Start with the pain, a number, or
  a counterintuitive statement. NEVER start with 'I' or 'Are you'.
- two_week_calendar: exactly 10 entries, Mon-Fri week 1 then Mon-Fri week 2.
  Vary formats — never repeat the same format on consecutive days.
- quick_wins: the 3 most impactful actions in 48 hours, each fully written out
  so the coach can copy-paste and execute immediately.
- primary_metric in kpis: one number with a diagnostic rule attached
  (e.g. 'Profile views — if not growing, fix your headline before adding content').
- Use Q17 (current channels) to detect blind spots. If high-trust niches
  (e.g. grief coach, trauma, therapy, high-ticket transformation) do NOT list
  Partnerships or Referrals in Q17, include those channels and explicitly call
  out that they are commonly underestimated in why_this_channel.
- If Q17 shows heavy reliance on one channel, include at least one complementary
  channel that reduces single-channel risk.
- trust_channel_benchmarks must be based on similar coaches in the same niche,
  but do NOT fabricate specific names. Use a short benchmark_note like
  "Based on similar grief coaches with 1–3 partner referral sources."
- trust_channel_benchmarks used_now must be "Yes" or "No" based on Q17.
- trust_channel_benchmarks estimated_annual_clients and estimated_annual_revenue
  MUST be plain integers.

CHANNEL-SPECIFIC profile_audit keys — use EXACTLY these per channel:
  LinkedIn     → headline_before, headline_after, about_before, about_after,
                 banner_tip, featured_section
  Instagram    → bio_before, bio_after, bio_formula, highlight_covers, story_strategy
  Email        → subject_line_formula, welcome_sequence, list_growth_tactic, segmentation_tip
  YouTube      → channel_description_rewrite, about_page_cta, thumbnail_formula,
                 channel_trailer_script_outline
  Podcast      → show_description_rewrite, episode_title_formula, intro_hook_script,
                 guest_pitch_template
  Facebook Ads → audience_definition, ad_hook_formula, creative_brief, landing_page_checklist
  Blog/SEO     → target_keywords, title_formula, meta_description_template,
                 internal_link_strategy
  Twitter/X    → bio_rewrite, pinned_tweet_strategy, thread_formula, engagement_tactic
  Webinar      → title_formula, registration_page_headline, three_part_structure,
                 follow_up_sequence
  Partnerships → partner_target_list, partner_offer, outreach_script,
                 co_marketing_asset
  Referrals    → referral_offer, ask_points, referral_script, tracking_system"""


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def cl(ws, row, col, val,
      bold=False, italic=False,
      color="000000", bg=None,
      size=10, wrap=True, align="left"):
    cell = ws.cell(row=row, column=col, value=val)
    cell.font = Font(bold=bold, italic=italic,
                     color=color, size=size, name="Arial")
    cell.alignment = Alignment(wrap_text=wrap, vertical="top", horizontal=align)
    if bg:
        cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
    return cell


def rh(ws, row, h):
    ws.row_dimensions[row].height = h


def cw(ws, col, w):
    ws.column_dimensions[get_column_letter(col)].width = w


def section_header(ws, row, text, span, bg="1F3864"):
    cl(ws, row, 1, text, bold=True, color="FFFFFF", bg=bg, size=12)
    ws.merge_cells(f"A{row}:{get_column_letter(span)}{row}")
    rh(ws, row, 24)


def col_headers(ws, row, headers, bg="2E75B6"):
    for i, h in enumerate(headers, 1):
        cl(ws, row, i, h, bold=True, color="FFFFFF", bg=bg, size=10, align="center")
    rh(ws, row, 22)


def money_fmt(cell):
    cell.number_format = '"$"#,##0'


def pct_fmt(cell):
    cell.number_format = '0.0%'


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route("/webhook/tally", methods=["POST"])
def receive_tally():
    data = request.json
    fields = data["data"]["fields"]
    answers = {}

    # Extract respondent email and name from Tally fields
    respondent_email = ""
    respondent_name = ""

    for field in fields:
        label = field.get("label", "").strip()
        value = field.get("value", "")
        field_type = field.get("type", "")

        if isinstance(value, list):
            value = value[0] if len(value) == 1 else ", ".join(str(v) for v in value)

        str_value = str(value) if value else ""
        answers[label] = str_value

        # Tally sends email fields with type=INPUT_EMAIL or label containing "email"
        if field_type == "INPUT_EMAIL" or "email" in label.lower():
            respondent_email = str_value
        # Name typically has type=INPUT_TEXT and label containing name
        if not respondent_name and any(k in label.lower() for k in ["name", "first name", "full name"]):
            respondent_name = str_value

    file_id = str(uuid.uuid4())[:8]

    # Generate plan once; cache it so the premium route reuses it
    plan = call_openai(answers)
    _PLAN_CACHE[file_id] = plan

    # Build the FREE teaser report
    free_path = f"/tmp/free_{file_id}.xlsx"
    build_free_excel(plan, free_path)

    # Also pre-build the full premium report
    premium_path = f"/tmp/plan_{file_id}.xlsx"
    build_excel(plan, premium_path)

    # Schedule 5-email drip sequence if we have an email address
    if respondent_email:
        schedule_email_sequence(
            to_email=respondent_email,
            name=respondent_name or "Coach",
            file_id=file_id,
            host_url=request.host_url
        )

    payment_url = f"{request.host_url}payment?file_id={file_id}"
    return jsonify({
        "success": True,
        "free_download_url": f"{request.host_url}download/free/{file_id}",
        "premium_url": payment_url,
        "file_id": file_id
    })


@app.route("/test-email-sequence", methods=["POST"])
def test_email_sequence():
    """
    Test route — fires Email 1 immediately so you can verify Resend delivery.
    POST { "email": "you@example.com", "name": "Your Name" }
    Does NOT call OpenAI or build Excel — just sends the email with a fake file_id.
    """
    body = request.get_json(silent=True) or {}
    to_email = body.get("email", "")
    name     = body.get("name", "Test Coach")
    if not to_email:
        return jsonify({"error": "email is required"}), 400

    # Use a fixed fake file_id for testing
    file_id     = "testtest"
    host_url    = request.host_url
    free_url    = f"{host_url}download/free/{file_id}"
    payment_url = f"{host_url}payment?file_id={file_id}"
    unsubscribe_url = f"{host_url}unsubscribe/test-token"

    html = email_1_html(name, free_url, payment_url, unsubscribe_url)
    send_email(to_email, "[TEST] Your free Coaching Business Snapshot is here \U0001f3af", html)
    return jsonify({"success": True, "message": f"Test Email 1 sent to {to_email}"})


@app.route("/unsubscribe/<token>")
def unsubscribe(token):
    """
    Cancels all pending email jobs for the user associated with this token.
    """
    data = _UNSUB_TOKENS.get(token)
    if not data:
        return "<h1>Invalid or expired link.</h1>", 400

    file_id = data.get("file_id")
    email = data["email"]

    # Remove all 5 possible scheduled jobs for this file_id
    for delay in [0, 1, 2, 4, 6]:
        job_id = f"{file_id}_email_{delay}"
        try:
            scheduler.remove_job(job_id)
        except:
            pass # Job might have already run

    # Also check if there's an abandonment job to remove
    try:
        scheduler.remove_job(f"abandoned_{email}")
    except:
        pass

    # Also remove the token
    if token in _UNSUB_TOKENS:
        del _UNSUB_TOKENS[token]

    return f"<h1>You have been unsubscribed.</h1><p>We won't send any more emails to {email}.</p>"


@app.route("/track-start", methods=["POST"])
def track_start():
    """
    Called via AJAX when a user finishes the first 2 steps (Name/Email).
    Schedules a 'did you finish?' email for 30 minutes from now.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    name = data.get("name")
    
    if not email:
        return jsonify({"success": False, "reason": "No email"}), 400

    job_id = f"abandoned_{email}"
    run_at = datetime.now() + timedelta(minutes=30)
    
    # Generate a temporary unsubscribe token for this follow-up
    unsub_token = str(uuid.uuid4())
    _UNSUB_TOKENS[unsub_token] = {"email": email}
    unsubscribe_url = f"{request.host_url}unsubscribe/{unsub_token}"
    
    quiz_url = f"{request.host_url}quiz"
    html = email_abandoned_html(name, quiz_url, unsubscribe_url)
    
    scheduler.add_job(
        send_email,
        trigger="date",
        run_date=run_at,
        args=[email, "Did you get interrupted?", html],
        id=job_id,
        replace_existing=True,
    )
    
    app.logger.info(f"Scheduled abandonment follow-up for {email}")
    return jsonify({"success": True})


@app.route("/")
def index():
    """Renders the main landing page."""
    return render_template("landing.html")


@app.route("/quiz")
def quiz_page():
    """Renders the standalone quiz form."""
    return render_template("quiz.html")


@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():
    """
    Processes the standalone quiz form.
    Maps form fields to the keys expected by the plan generator.
    """
    form_data = request.form
    respondent_email = form_data.get("email", "")
    respondent_name = form_data.get("name", "")

    if not respondent_email:
        return "Email is required to receive your plan.", 400

    # Map form fields to the Q1-Q17 keys
    answers = {}
    for i in range(1, 18):
        key = f"Q{i}"
        if key == "Q17":
            vals = [v for v in form_data.getlist("Q17") if v.strip()]
            other = form_data.get("Q17_other", "").strip()
            if other:
                vals.append(other)
            answers[key] = ", ".join(vals)
        else:
            answers[key] = form_data.get(key, "")
    answers["Q15_interest"] = form_data.get("Q15_interest", "Yes")

    file_id = str(uuid.uuid4())[:8]

    # Generate plan and cache it
    plan = call_openai(answers)
    _PLAN_CACHE[file_id] = plan

    # Build reports
    payment_url = f"{request.host_url}payment?file_id={file_id}"
    free_path = f"/tmp/free_{file_id}.xlsx"
    build_free_excel(plan, free_path, payment_url)
    premium_path = f"/tmp/plan_{file_id}.xlsx"
    build_excel(plan, premium_path)

    # Send Email 1 Synchronously for maximum reliability
    # This avoids any scheduler 'now' race conditions
    unsub_token = str(uuid.uuid4())
    _UNSUB_TOKENS[unsub_token] = {"email": respondent_email, "file_id": file_id}
    unsubscribe_url = f"{request.host_url}unsubscribe/{unsub_token}"
    
    html_email_1 = email_1_html(
        respondent_name or "Coach",
        f"{request.host_url}download/free/{file_id}",
        f"{request.host_url}payment?file_id={file_id}",
        unsubscribe_url
    )
    send_email(
        respondent_email, 
        "Your free Coaching Business Snapshot is here 🎯", 
        html_email_1, 
        free_path
    )

    # Cancel any pending abandonment emails since they finished
    try:
        scheduler.remove_job(f"abandoned_{respondent_email}")
    except:
        pass

    # Schedule the 5-email drip sequence
    schedule_email_sequence(
        to_email=respondent_email,
        name=respondent_name or "Coach",
        file_id=file_id,
        host_url=request.host_url
    )

    return redirect(f"/payment?file_id={file_id}")


@app.route("/download/free/<file_id>")
def download_free_file(file_id):
    """Download the free teaser report."""
    if not file_id.isalnum():
        return "Invalid file ID", 400
    file_path = f"/tmp/free_{file_id}.xlsx"
    if not os.path.exists(file_path):
        return "File not found or expired", 404
    return send_file(file_path, as_attachment=True,
                     download_name="Your_Free_Coaching_Snapshot.xlsx")


@app.route("/download/<file_id>")
def download_file(file_id):
    """Download the full premium report (gated behind payment)."""
    if not file_id.isalnum():
        return "Invalid file ID", 400
    file_path = f"/tmp/plan_{file_id}.xlsx"
    if not os.path.exists(file_path):
        return "File not found or expired", 404
    return send_file(file_path, as_attachment=True,
                     download_name="Your_Full_Coaching_Business_Plan.xlsx")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ─────────────────────────────────────────────
# OPENAI CALL
# ─────────────────────────────────────────────
def call_openai(answers: dict) -> dict:
    user_message = f"""
Generate a personalised coaching business plan from these quiz answers.

Q1  - Experience type: {answers.get('Q1', '')}
Q2  - Natural advice area: "{answers.get('Q2', '')}"
Q3  - Coaching experience: {answers.get('Q3', '')}
Q4  - Ideal client: {answers.get('Q4', '')}
Q5  - Client problem in their exact words: "{answers.get('Q5', '')}"
Q6  - What they want: "{answers.get('Q6', '')}"
Q7  - Would not work with: "{answers.get('Q7', '')}"
Q8  - Delivery format: {answers.get('Q8', '')}
Q9  - Duration: {answers.get('Q9', '')}
Q10 - Pricing comfort: {answers.get('Q10', '')}
Q12 - Audience size: {answers.get('Q12', '')}
Q13 - Biggest fear: {answers.get('Q13', '')}
Q14 - Hours per week: {answers.get('Q14', '')}
Q15_interest - Open to paid marketing: {answers.get('Q15_interest', '')}
Q15 - Ad budget: {answers.get('Q15', '')}
Q16 - Success definition: "{answers.get('Q16', '')}"
Q17 - Current acquisition channels (selected): "{answers.get('Q17', '')}"

Return this exact JSON structure fully populated:
{{
  "offer_sentence": "",
  "offer_layers": [
    {{"layer": "WHO",       "raw": "", "refined": "", "why": ""}},
    {{"layer": "PAIN",      "raw": "", "refined": "", "why": ""}},
    {{"layer": "OUTCOME",   "raw": "", "refined": "", "why": ""}},
    {{"layer": "MECHANISM", "raw": "", "refined": "", "why": ""}},
    {{"layer": "PROOF",     "raw": "", "refined": "", "why": ""}},
    {{"layer": "EXCLUSION", "raw": "", "refined": "", "why": ""}}
  ],
  "funnel": [
    {{"tier": "LEAD MAGNET", "name": "", "format": "", "price": "Free",
      "purpose": "", "monthly_clients": 0, "monthly_revenue_low": 0, "monthly_revenue_high": 0}},
    {{"tier": "LOW-TICKET",  "name": "", "format": "", "price": "",
      "purpose": "", "monthly_clients": 0, "monthly_revenue_low": 0, "monthly_revenue_high": 0}},
    {{"tier": "MID-TICKET",  "name": "", "format": "", "price": "",
      "purpose": "", "monthly_clients": 0, "monthly_revenue_low": 0, "monthly_revenue_high": 0}},
    {{"tier": "FLAGSHIP",    "name": "", "format": "", "price": "",
      "purpose": "", "monthly_clients": 0, "monthly_revenue_low": 0, "monthly_revenue_high": 0}}
  ],
  "action_plan": [
    {{"week": "Weeks 1-2",   "focus": "", "actions": "", "milestone": ""}},
    {{"week": "Weeks 3-4",   "focus": "", "actions": "", "milestone": ""}},
    {{"week": "Weeks 5-6",   "focus": "", "actions": "", "milestone": ""}},
    {{"week": "Weeks 7-9",   "focus": "", "actions": "", "milestone": ""}},
    {{"week": "Weeks 10-12", "focus": "", "actions": "", "milestone": ""}}
  ],
  "fear_reframe": {{
    "fear": "", "truth": "", "action_1": "", "action_2": "", "action_3": ""
  }},
  "marketing": [
    {{
      "channel": "LinkedIn",
      "priority": "Primary",
      "why_this_channel": "",
      "profile_audit": {{}},
      "content_pillars": [
        {{
          "pillar": "",
          "purpose": "",
          "formats": "",
          "frequency": "",
          "hooks": ["", "", ""],
          "sample_post": ""
        }}
      ],
      "two_week_calendar": [
        {{"day": "Mon Wk1", "format": "", "pillar": "", "hook": "", "cta": ""}}
      ],
      "quick_wins": ["", "", ""],
      "kpis": {{
        "posting_frequency": "",
        "engagement_rate_target": "",
        "connection_growth_per_month": "",
        "leads_per_month": "",
        "primary_metric": ""
      }}
    }}
  ],
  "revenue": [
    {{"program": "", "price_numeric": 0,
      "year1_low_units": 0, "year1_low_revenue": 0,
      "year1_high_units": 0, "year1_high_revenue": 0,
      "year2_units": 0, "year2_revenue": 0}},
    {{"program": "", "price_numeric": 0,
      "year1_low_units": 0, "year1_low_revenue": 0,
      "year1_high_units": 0, "year1_high_revenue": 0,
      "year2_units": 0, "year2_revenue": 0}},
    {{"program": "", "price_numeric": 0,
      "year1_low_units": 0, "year1_low_revenue": 0,
      "year1_high_units": 0, "year1_high_revenue": 0,
      "year2_units": 0, "year2_revenue": 0}},
    {{"program": "", "price_numeric": 0,
      "year1_low_units": 0, "year1_low_revenue": 0,
      "year1_high_units": 0, "year1_high_revenue": 0,
      "year2_units": 0, "year2_revenue": 0}}
  ],
  "revenue_note": "",
  "personal_note": "",
  "trust_channel_benchmarks": {{
    "partnerships": {{
      "used_now": "",
      "why_underestimated": "",
      "estimated_annual_clients": 0,
      "estimated_annual_revenue": 0,
      "benchmark_note": "",
      "first_actions": ["", "", ""]
    }},
    "referrals": {{
      "used_now": "",
      "why_underestimated": "",
      "estimated_annual_clients": 0,
      "estimated_annual_revenue": 0,
      "benchmark_note": "",
      "first_actions": ["", "", ""]
    }}
  }},
  "include_paid_funnel": true,
  "competitors": [
    {{"name": "", "url": "", "niche": "", "strategy": "", "content_approach": "",
      "business_model": "", "flagship_offer": "", "flagship_price": "",
      "funnel_structure": "", "estimated_revenue": "", "audience_size": "",
      "strengths": "", "weaknesses": "", "your_edge": ""}},
    {{"name": "", "url": "", "niche": "", "strategy": "", "content_approach": "",
      "business_model": "", "flagship_offer": "", "flagship_price": "",
      "funnel_structure": "", "estimated_revenue": "", "audience_size": "",
      "strengths": "", "weaknesses": "", "your_edge": ""}},
    {{"name": "", "url": "", "niche": "", "strategy": "", "content_approach": "",
      "business_model": "", "flagship_offer": "", "flagship_price": "",
      "funnel_structure": "", "estimated_revenue": "", "audience_size": "",
      "strengths": "", "weaknesses": "", "your_edge": ""}}
  ]
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=10000,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ]
    )
    return json.loads(response.choices[0].message.content)


# ─────────────────────────────────────────────
# FREE TEASER HELPERS
# ─────────────────────────────────────────────

LOCK_BG      = "F2F2F2"   # light grey background for locked cells
LOCK_FG      = "9E9E9E"   # grey text for locked cells
LOCK_LABEL_BG = "D9E1F2"  # same blue-grey used for labels in paid version
LOCK_LABEL_FG = "1F3864"  # dark navy text


def _tease(val: str, keep: int = 45) -> str:
    """Return the first `keep` chars of val followed by a lock indicator."""
    if not val:
        return "🔒 [Upgrade to unlock]"
    if len(val) <= keep:
        return val[:keep] + "  🔒"
    return val[:keep].rstrip() + "…  🔒 [Upgrade to unlock]"


def _lock_cell(ws, row, col, val="", align="left"):
    """Write a greyed-out 'locked' cell."""
    return cl(ws, row, col, val or "🔒", italic=True,
              color=LOCK_FG, bg=LOCK_BG, align=align)


# ── FUNNEL — all 4 tiers, revenue columns locked on mid/flagship ──────────────
def build_free_funnel_sheet(ws, data):
    section_header(ws, 1, "YOUR RECOMMENDED FUNNEL  ·  Preview", span=8)
    col_headers(ws, 3, [
        "TIER", "NAME", "FORMAT", "PRICE", "PURPOSE",
        "EST. MONTHLY CLIENTS", "MONTHLY REV (LOW)", "MONTHLY REV (HIGH)"
    ])

    tier_colors = {
        "LEAD MAGNET": "70AD47",
        "LOW-TICKET":  "4472C4",
        "MID-TICKET":  "ED7D31",
        "FLAGSHIP":    "C00000",
    }
    funnel = data.get("funnel", [])

    for ri, item in enumerate(funnel, 4):
        tier  = item.get("tier", "")
        bg    = tier_colors.get(tier, "FFFFFF")
        locked = tier in ("MID-TICKET", "FLAGSHIP")

        # Col 1 — TIER label: always visible, add lock badge if restricted
        label = f"🔒 {tier}" if locked else tier
        cl(ws, ri, 1, label, bold=True,
           bg=(LOCK_LABEL_BG if locked else bg),
           color=(LOCK_LABEL_FG if locked else "FFFFFF"))

        # Col 2-3 — Name & Format: visible on lead/low, locked on mid/flagship
        if locked:
            _lock_cell(ws, ri, 2, "🔒 [Unlock Identity]")
            _lock_cell(ws, ri, 3, "🔒 [Unlock Structure]")
        else:
            cl(ws, ri, 2, item.get("name", ""))
            cl(ws, ri, 3, item.get("format", ""))

        # Col 4 — Price: show price even for locked tiers (creates desire)
        cl(ws, ri, 4, item.get("price", ""), bold=True,
           color="1F3864", bg=LOCK_BG if locked else "FFFFFF")

        # Col 5 — Purpose: teased on locked tiers
        if locked:
            cl(ws, ri, 5, _tease(item.get("purpose", ""), keep=50),
               italic=True, color=LOCK_FG, bg=LOCK_BG)
        else:
            cl(ws, ri, 5, item.get("purpose", ""))

        # Cols 6-8 — Metrics: fully visible for free tiers, locked for paid tiers
        if locked:
            _lock_cell(ws, ri, 6, align="center")
            _lock_cell(ws, ri, 7, "🔒 Upgrade", align="right")
            _lock_cell(ws, ri, 8, "🔒 Upgrade", align="right")
        else:
            c6 = cl(ws, ri, 6, item.get("monthly_clients", 0),      align="center")
            c7 = cl(ws, ri, 7, item.get("monthly_revenue_low", 0),  align="right")
            c8 = cl(ws, ri, 8, item.get("monthly_revenue_high", 0), align="right")
            money_fmt(c6); money_fmt(c7); money_fmt(c8)

        rh(ws, ri, 52)

    # Totals row hint
    tr = 4 + len(funnel)
    cl(ws, tr, 1, "MONTHLY TOTALS", bold=True, bg="1F3864", color="FFFFFF")
    for c in range(2, 6):
        cl(ws, tr, c, "", bg="D9E1F2")
    _lock_cell(ws, tr, 6, "🔒", align="center")
    _lock_cell(ws, tr, 7, "🔒 Full totals in paid plan", align="right")
    _lock_cell(ws, tr, 8, "🔒 Full totals in paid plan", align="right")
    rh(ws, tr, 22)

    cw(ws, 1, 16); cw(ws, 2, 26); cw(ws, 3, 22); cw(ws, 4, 14)
    cw(ws, 5, 40); cw(ws, 6, 20); cw(ws, 7, 18); cw(ws, 8, 18)


# ── 90-DAY PLAN — all 5 entries, actions+milestone teased on weeks 5-12 ───────
def build_free_action_sheet(ws, data):
    section_header(ws, 1, "YOUR 90-DAY ACTION PLAN  ·  Preview", span=5)
    col_headers(ws, 3, ["WEEK", "FOCUS", "ACTIONS", "MILESTONE", "STATUS"])

    phase_colors = ["4472C4", "4472C4", "ED7D31", "ED7D31", "C00000"]
    action_plan  = data.get("action_plan", [])

    for ri, item in enumerate(action_plan, 4):
        idx    = ri - 4
        locked = idx >= 2                          # Weeks 5+ are actions-locked
        blackout = idx >= 3                        # Weeks 10+ are focus-locked
        bg_ph  = phase_colors[idx] if idx < len(phase_colors) else "FFFFFF"

        # Col 1 — Week range: always visible
        label = f"🔒 {item.get('week', '')}" if locked else item.get("week", "")
        cl(ws, ri, 1, label, bold=True,
           bg=(LOCK_LABEL_BG if locked else bg_ph),
           color=(LOCK_LABEL_FG if locked else "FFFFFF"))

        # Col 2 — Focus title: Locked for late stages
        if blackout:
            _lock_cell(ws, ri, 2, "🔒 [Strategy Locked]", align="left")
        else:
            cl(ws, ri, 2, item.get("focus", ""), bold=True,
               bg="F2F2F2" if locked else "F7F9FC",
               color=LOCK_LABEL_FG if locked else "000000")

        # Cols 3-4 — Actions + Milestone: teased on locked weeks
        if locked:
            cl(ws, ri, 3, _tease(item.get("actions", ""),   keep=40 if blackout else 60),
               italic=True, color=LOCK_FG, bg=LOCK_BG)
            cl(ws, ri, 4, _tease(item.get("milestone", ""), keep=20 if blackout else 35),
               italic=True, color=LOCK_FG, bg=LOCK_BG)
            _lock_cell(ws, ri, 5, "🔒", align="center")
        else:
            cl(ws, ri, 3, item.get("actions", ""))
            cl(ws, ri, 4, item.get("milestone", ""), italic=True,
               color="375623", bg="E2EFDA")
            c = cl(ws, ri, 5, "⬜ Not Started", align="center", bg="FFF3EC")
            c.font = Font(name="Arial", size=10, color="ED7D31", bold=True)

        rh(ws, ri, 70)

    legend_row = 4 + len(action_plan) + 1
    ws.merge_cells(f"A{legend_row}:E{legend_row}")
    cl(ws, legend_row, 1,
       "Weeks 1–4 are fully unlocked.  🔒 Weeks 5–12 are available in the Full Plan.",
       italic=True, bg="EBF3FB", color="1F3864", size=9)
    rh(ws, legend_row, 18)

    cw(ws, 1, 16); cw(ws, 2, 28); cw(ws, 3, 44); cw(ws, 4, 34); cw(ws, 5, 18)


# ── FEAR REFRAME — labels visible, values teased ─────────────────────────────
def build_free_fear_sheet(ws, data):
    section_header(ws, 1, "YOUR FEAR REFRAME  ·  Preview", span=2)

    fear = data.get("fear_reframe", {})
    rows = [
        ("THE FEAR",           fear.get("fear", ""),     "C00000", "FFE0E0", False),
        ("THE REAL TRUTH",     fear.get("truth", ""),    "375623", "E2EFDA", True),
        ("ACTION THIS WEEK 1", fear.get("action_1", ""), "2E75B6", "EBF3FB", True),
        ("ACTION THIS WEEK 2", fear.get("action_2", ""), "2E75B6", "EBF3FB", True),
        ("ACTION THIS WEEK 3", fear.get("action_3", ""), "2E75B6", "EBF3FB", True),
    ]

    for ri, (label, val, label_color, val_bg, locked) in enumerate(rows, 3):
        cl(ws, ri, 1, label, bold=True, bg="D9E1F2", color=label_color, size=11)
        if locked:
            cl(ws, ri, 2, _tease(val, keep=55), italic=True,
               color=LOCK_FG, bg=LOCK_BG, size=11)
        else:
            # Show the fear itself in full — it's personalised and hooks them
            cl(ws, ri, 2, val, bg=val_bg, size=11)
        rh(ws, ri, 60)

    cw(ws, 1, 22); cw(ws, 2, 70)


# ── MARKETING HELPERS & BUILDERS ───────────────────────────────────────────────

CHANNEL_PALETTES = [
    {"header": "0A66C2", "sub": "1A85D6", "light": "D0E8FF", "accent": "EBF5FF"},  # LinkedIn blue
    {"header": "C13584", "sub": "D63C8A", "light": "FFD6EC", "accent": "FFF0F7"},  # Instagram pink
    {"header": "217346", "sub": "2A8F58", "light": "C6EFCE", "accent": "F0FFF4"},  # Email green
    {"header": "CC0000", "sub": "E00000", "light": "FFD0D0", "accent": "FFF5F5"},  # YouTube red
    {"header": "7C3AED", "sub": "8B5CF6", "light": "EDE9FE", "accent": "F9F7FF"},  # Purple
]

CHANNEL_EMOJIS = {
    "LinkedIn": "💼", "Instagram": "📸", "Email": "📧",
    "Email Newsletter": "📧", "YouTube": "🎬", "Podcast": "🎙",
    "Facebook Ads": "📣", "Blog": "✍️", "Blog/SEO": "✍️",
    "Twitter": "🐦", "Twitter/X": "🐦", "Webinar": "📡",
    "Partnerships": "🤝", "Referrals": "🔁",
}


def build_all_marketing_sheets(wb, data, is_free=False, payment_url=""):
    """Creates one dedicated worksheet per marketing channel."""
    channels = data.get("marketing", [])
    for idx, ch in enumerate(channels):
        palette = CHANNEL_PALETTES[idx % len(CHANNEL_PALETTES)]
        ch_name = ch.get("channel", f"Channel {idx+1}")
        emoji   = CHANNEL_EMOJIS.get(ch_name, "📌")
        tab     = f"{emoji} {ch_name}"[:31]
        ws      = wb.create_sheet(tab)
        _build_channel_sheet(ws, ch, palette, is_free, payment_url)


def _build_channel_sheet(ws, ch, palette, is_free, payment_url):
    H  = palette["header"]
    SB = palette["sub"]
    LT = palette["light"]
    AC = palette["accent"]

    name     = ch.get("channel",          "Channel")
    priority = ch.get("priority",         "Primary")
    why      = ch.get("why_this_channel", "")
    audit    = ch.get("profile_audit",    {})
    pillars  = ch.get("content_pillars",  [])
    calendar = ch.get("two_week_calendar", [])
    qwins    = ch.get("quick_wins",       [])
    kpis     = ch.get("kpis",             {})

    row = 1

    # ── TITLE BANNER ─────────────────────────────────────────────────────────
    ws.merge_cells(f"A{row}:F{row}")
    cl(ws, row, 1, f"{name.upper()} STRATEGY  ·  {priority} Channel",
       bold=True, color="FFFFFF", bg=H, size=14, align="center")
    rh(ws, row, 32); row += 1

    ws.merge_cells(f"A{row}:F{row}")
    cl(ws, row, 1, why, italic=True, color="1F3864", bg=AC, size=10)
    rh(ws, row, 28); row += 2

    # ── SECTION 1: PROFILE AUDIT ─────────────────────────────────────────────
    ws.merge_cells(f"A{row}:F{row}")
    cl(ws, row, 1, "① PROFILE AUDIT — Fix These First",
       bold=True, color="FFFFFF", bg=H, size=11)
    rh(ws, row, 22); row += 1

    # Column headers
    cl(ws, row, 1, "FIELD",           bold=True, color="FFFFFF", bg=SB, size=9, align="center")
    cl(ws, row, 2, "❌  BEFORE",      bold=True, color="FFFFFF", bg="C00000", size=9)
    cl(ws, row, 3, "YOUR CURRENT ✏️", bold=True, color="555555", bg="F2F2F2", size=9, italic=True)
    ws.merge_cells(f"D{row}:F{row}")
    cl(ws, row, 4, "✅  AFTER — YOUR REWRITE", bold=True, color="FFFFFF", bg="375623", size=9)
    rh(ws, row, 18); row += 1

    # Map: audit key → (display label, matching "after" key or None)
    AUDIT_MAP = {
        "headline_before":                ("Headline",              "headline_after"),
        "about_before":                   ("About / Summary",       "about_after"),
        "banner_tip":                     ("Banner Image",          None),
        "featured_section":               ("Featured Section",      None),
        "bio_before":                     ("Bio",                   "bio_after"),
        "bio_formula":                    ("Bio Formula",           None),
        "highlight_covers":               ("Story Highlights",      None),
        "story_strategy":                 ("Stories Strategy",      None),
        "subject_line_formula":           ("Subject Line Formula",  None),
        "welcome_sequence":               ("Welcome Sequence",      None),
        "list_growth_tactic":             ("List Growth Tactic",    None),
        "segmentation_tip":               ("Segmentation",          None),
        "channel_description_rewrite":    ("Channel Description",   None),
        "about_page_cta":                 ("About Page CTA",        None),
        "thumbnail_formula":              ("Thumbnail Formula",     None),
        "channel_trailer_script_outline": ("Trailer Script",        None),
        "show_description_rewrite":       ("Show Description",      None),
        "episode_title_formula":          ("Episode Title Formula", None),
        "intro_hook_script":              ("Intro Hook Script",     None),
        "guest_pitch_template":           ("Guest Pitch Template",  None),
        "audience_definition":            ("Target Audience",       None),
        "ad_hook_formula":                ("Ad Hook Formula",       None),
        "creative_brief":                 ("Creative Brief",        None),
        "landing_page_checklist":         ("Landing Page",          None),
        "target_keywords":                ("Target Keywords (5)",   None),
        "title_formula":                  ("Title Formula",         None),
        "meta_description_template":      ("Meta Description",      None),
        "internal_link_strategy":         ("Internal Link Strategy",None),
        "bio_rewrite":                    ("Bio Rewrite",           None),
        "pinned_tweet_strategy":          ("Pinned Tweet",          None),
        "thread_formula":                 ("Thread Formula",        None),
        "engagement_tactic":              ("Engagement Tactic",     None),
        "registration_page_headline":     ("Registration Headline", None),
        "three_part_structure":           ("3-Part Structure",      None),
        "follow_up_sequence":             ("Follow-up Sequence",    None),
        "partner_target_list":            ("Partner Target List",   None),
        "partner_offer":                  ("Partner Offer",         None),
        "outreach_script":                ("Outreach Script",        None),
        "co_marketing_asset":             ("Co-Marketing Asset",    None),
        "referral_offer":                 ("Referral Offer",        None),
        "ask_points":                     ("Ask Points",            None),
        "referral_script":                ("Referral Script",        None),
        "tracking_system":                ("Tracking System",       None),
    }

    rendered = set()
    for key, (label, after_key) in AUDIT_MAP.items():
        val = audit.get(key)
        if not val or key in rendered:
            continue
        rendered.add(key)
        if after_key:
            rendered.add(after_key)

        after_val = audit.get(after_key, "") if after_key else ""
        bg_row    = AC if row % 2 == 0 else "FFFFFF"

        cl(ws, row, 1, label, bold=True, bg=LT, color="1F3864", size=9)

        if after_key:
            cl(ws, row, 2, val,       italic=True, color="9E2A2B", bg="FFE8E8",  size=9)
            cl(ws, row, 3, "",                                    bg="F2F2F2",   size=9)
            ws.merge_cells(f"D{row}:F{row}")
            cl(ws, row, 4, after_val, bold=True,  color="1F4E24", bg="E2EFDA",  size=9)
        else:
            ws.merge_cells(f"B{row}:F{row}")
            cl(ws, row, 2, val, bg=bg_row, size=9)

        char_count = len(str(val or "") + str(after_val or ""))
        rh(ws, row, max(40, min(130, char_count // 3)))
        row += 1

    row += 1  # spacer

    # ── SECTION 2: CONTENT PILLARS ────────────────────────────────────────────
    ws.merge_cells(f"A{row}:F{row}")
    cl(ws, row, 1, "② CONTENT PILLARS — Your 3-Pillar Framework",
       bold=True, color="FFFFFF", bg=H, size=11)
    rh(ws, row, 22); row += 1

    cl(ws, row, 1, "PILLAR",         bold=True, color="FFFFFF", bg=SB, size=9, align="center")
    cl(ws, row, 2, "PURPOSE",        bold=True, color="FFFFFF", bg=SB, size=9)
    cl(ws, row, 3, "FORMAT & FREQ",  bold=True, color="FFFFFF", bg=SB, size=9)
    ws.merge_cells(f"D{row}:F{row}")
    cl(ws, row, 4, "3 SCROLL-STOPPING HOOKS", bold=True, color="FFFFFF", bg=SB, size=9)
    rh(ws, row, 18); row += 1

    for pi, pillar in enumerate(pillars):
        bg_p    = AC if pi % 2 == 0 else "FFFFFF"
        pname   = pillar.get("pillar",    "")
        purp    = pillar.get("purpose",   "")
        fmt     = f"{pillar.get('formats','')}  ·  {pillar.get('frequency','')}"
        hooks   = pillar.get("hooks", [])
        hook_text = "\n".join(f"▸  {h}" for h in hooks)

        cl(ws, row, 1, pname,     bold=True, bg=LT, color="1F3864", size=10)
        cl(ws, row, 2, purp,      bg=bg_p,          size=9)
        cl(ws, row, 3, fmt,       bg=bg_p,           size=9, italic=True)
        ws.merge_cells(f"D{row}:F{row}")
        cl(ws, row, 4, hook_text, bg=bg_p,           size=9, color="1F3864")
        rh(ws, row, 75)
        row += 1

    row += 1  # spacer

    # ── SECTION 3: SAMPLE POSTS ───────────────────────────────────────────────
    ws.merge_cells(f"A{row}:F{row}")
    if is_free:
        cl(ws, row, 1, "③ SAMPLE POSTS  🔒  Full publish-ready posts in the Full Plan",
           bold=True, color="FFFFFF", bg=H, size=11)
    else:
        cl(ws, row, 1, "③ SAMPLE POSTS — Copy, Edit to Your Voice, Post",
           bold=True, color="FFFFFF", bg=H, size=11)
    rh(ws, row, 22); row += 1

    for pi, pillar in enumerate(pillars):
        pname = pillar.get("pillar", f"Pillar {pi+1}")
        post  = pillar.get("sample_post", "")
        bg_p  = AC if pi % 2 == 0 else "FFFFFF"

        cl(ws, row, 1, pname, bold=True, bg=LT, color="1F3864", size=9)

        ws.merge_cells(f"B{row}:F{row}")
        if is_free:
            teased = (post[:90].rstrip() + "…  🔒 Upgrade to unlock full post") if len(post) > 90 else post + "  🔒"
            cl(ws, row, 2, teased, italic=True, color="9E9E9E", bg="F2F2F2", size=9)
            rh(ws, row, 40)
        else:
            cl(ws, row, 2, post, bg=bg_p, size=9)
            rh(ws, row, max(80, min(200, len(post) // 2)))
        row += 1

    row += 1  # spacer

    # ── SECTION 4: 2-WEEK CONTENT CALENDAR ───────────────────────────────────
    ws.merge_cells(f"A{row}:F{row}")
    if is_free:
        cl(ws, row, 1, "④ 2-WEEK CONTENT CALENDAR  🔒  Week 2 unlocks in Full Plan",
           bold=True, color="FFFFFF", bg=H, size=11)
    else:
        cl(ws, row, 1, "④ 2-WEEK STARTER CALENDAR — Copy, Paste, Post",
           bold=True, color="FFFFFF", bg=H, size=11)
    rh(ws, row, 22); row += 1

    cl(ws, row, 1, "DAY",    bold=True, color="FFFFFF", bg=SB, size=9, align="center")
    cl(ws, row, 2, "FORMAT", bold=True, color="FFFFFF", bg=SB, size=9, align="center")
    cl(ws, row, 3, "PILLAR", bold=True, color="FFFFFF", bg=SB, size=9)
    ws.merge_cells(f"D{row}:E{row}")
    cl(ws, row, 4, "HOOK / OPENING LINE",   bold=True, color="FFFFFF", bg=SB, size=9)
    cl(ws, row, 6, "CTA",    bold=True, color="FFFFFF", bg=SB, size=9, align="center")
    rh(ws, row, 18); row += 1

    for ci, entry in enumerate(calendar):
        bg_c   = AC if ci % 2 == 0 else "FFFFFF"
        day    = entry.get("day",    "")
        fmt    = entry.get("format", "")
        pillar = entry.get("pillar", "")
        hook   = entry.get("hook",   "")
        cta    = entry.get("cta",    "")
        locked = is_free and ci >= 5  # lock week 2 in free version

        if locked:
            cl(ws, row, 1, day, bold=True, bg="D9D9D9", color="9E9E9E", size=9, align="center")
            ws.merge_cells(f"B{row}:F{row}")
            cl(ws, row, 2, "🔒 Week 2 available in Full Plan",
               italic=True, color="9E9E9E", bg="F2F2F2", size=9)
        else:
            cl(ws, row, 1, day,    bold=True, bg=LT, color="1F3864", size=9, align="center")
            cl(ws, row, 2, fmt,    bg=bg_c,           size=9, align="center")
            cl(ws, row, 3, pillar, bg=bg_c,           size=9)
            ws.merge_cells(f"D{row}:E{row}")
            cl(ws, row, 4, hook,   bg=bg_c,           size=9)
            cl(ws, row, 6, cta,    bg="E2EFDA", color="375623", size=9, bold=True)

        rh(ws, row, 45)
        row += 1

    row += 1  # spacer

    # ── SECTION 5: QUICK WINS ─────────────────────────────────────────────────
    ws.merge_cells(f"A{row}:F{row}")
    if is_free:
        cl(ws, row, 1, "⑤ QUICK WINS  🔒  3 copy-paste actions — unlock in Full Plan",
           bold=True, color="FFFFFF", bg=H, size=11)
    else:
        cl(ws, row, 1, "⑤ QUICK WINS — Do These in the Next 48 Hours",
           bold=True, color="FFFFFF", bg=H, size=11)
    rh(ws, row, 22); row += 1

    for qi, win in enumerate(qwins, 1):
        bg_q = AC if qi % 2 == 0 else "FFFFFF"
        cl(ws, row, 1, f"ACTION {qi}", bold=True, bg=LT, color="1F3864", size=10, align="center")
        ws.merge_cells(f"B{row}:E{row}")
        if is_free:
            teased = (win[:80].rstrip() + "…  🔒 Upgrade to unlock") if len(win) > 80 else win + "  🔒"
            cl(ws, row, 2, teased, italic=True, color="9E9E9E", bg="F2F2F2", size=9)
        else:
            cl(ws, row, 2, win, bg=bg_q, size=9)
        cl(ws, row, 6, "⬜ Done", bg="FFF3EC", color="ED7D31", bold=True, size=10, align="center")
        rh(ws, row, max(45, min(100, len(win) // 2)))
        row += 1

    row += 1  # spacer

    # ── SECTION 6: KPIs ───────────────────────────────────────────────────────
    ws.merge_cells(f"A{row}:F{row}")
    cl(ws, row, 1, "⑥ SUCCESS METRICS — Track These Weekly",
       bold=True, color="FFFFFF", bg=H, size=11)
    rh(ws, row, 22); row += 1

    kpi_fields = [
        ("Posting Frequency",            "posting_frequency"),
        ("Engagement Rate Target",       "engagement_rate_target"),
        ("Follower / Connection Growth", "connection_growth_per_month"),
        ("Leads per Month",              "leads_per_month"),
        ("🎯 Primary Metric to Watch",   "primary_metric"),
    ]
    for ki, (label, key) in enumerate(kpi_fields):
        bg_k  = AC if ki % 2 == 0 else "FFFFFF"
        val   = kpis.get(key, "—")
        is_primary = key == "primary_metric"

        cl(ws, row, 1, label, bold=True, bg=LT, color="1F3864", size=9)
        ws.merge_cells(f"B{row}:C{row}")
        cl(ws, row, 2, val,
           bold=is_primary, bg="E2EFDA" if is_primary else bg_k,
           color="375623" if is_primary else "000000", size=10)
        ws.merge_cells(f"D{row}:E{row}")
        cl(ws, row, 4, "YOUR CURRENT →", italic=True, color="9E9E9E", bg="F2F2F2", size=8, align="center")
        cl(ws, row, 6, "⬜ Track",       italic=True, color="9E9E9E", bg="F2F2F2", size=8, align="center")
        rh(ws, row, max(28, min(80, len(str(val)) // 2)))
        row += 1

    # ── COLUMN WIDTHS ─────────────────────────────────────────────────────────
    cw(ws, 1, 22)   # Label column
    cw(ws, 2, 30)   # Before / Format / Value
    cw(ws, 3, 22)   # Current state / Freq / Pillar
    cw(ws, 4, 32)   # After / Hook col A
    cw(ws, 5, 18)   # Hook col B
    cw(ws, 6, 20)   # CTA / Done checkbox


# ── REVENUE — program names + Y1 low visible, everything else locked ──────────
def build_free_revenue_sheet(ws, data):
    section_header(ws, 1, "REVENUE PROJECTION  ·  Preview", span=9)
    col_headers(ws, 3, [
        "PROGRAM", "PRICE",
        "Y1 UNITS (LOW)", "Y1 REVENUE (LOW)",
        "Y1 UNITS (HIGH)", "Y1 REVENUE (HIGH)",
        "Y2 UNITS", "Y2 REVENUE",
        "YoY GROWTH"
    ])

    items      = data.get("revenue", [])
    data_start = 4

    for ri, item in enumerate(items, data_start):
        bg = "F7F9FC" if ri % 2 == 0 else "FFFFFF"

        # Program name + price — always visible
        cl(ws, ri, 1, item.get("program", ""), bold=True, bg=bg, color="1F3864")
        c2 = cl(ws, ri, 2, item.get("price_numeric", 0), bg=bg, align="right")
        money_fmt(c2)

        # Revenue metrics - Lock everything except Lead Magnet
        if ri > data_start:
            for col in range(3, 10):
                _lock_cell(ws, ri, col, "🔒 [Unlock Numbers]")
        else:
            # Y1 low — visible ONLY for lead magnet
            c3 = cl(ws, ri, 3, item.get("year1_low_units",    0), bg=bg, align="center")
            c4 = cl(ws, ri, 4, item.get("year1_low_revenue",  0), bg=bg, align="right")
            money_fmt(c4)
            for col in range(5, 10):
                _lock_cell(ws, ri, col, "🔒")

        rh(ws, ri, 30)

    # Totals row — fully locked
    tr = data_start + len(items)
    cl(ws, tr, 1, "TOTAL", bold=True, bg="1F3864", color="FFFFFF")
    cl(ws, tr, 2, "",      bg="1F3864")
    for col in range(3, 10):
        _lock_cell(ws, tr, col, "🔒 Full plan only")
    rh(ws, tr, 26)

    # Note row
    note_row = tr + 1
    ws.merge_cells(f"A{note_row}:I{note_row}")
    cl(ws, note_row, 1,
       "🔒 Full Year 1 (high), Year 2 projections, and your personalised revenue note are in the Full Plan.",
       italic=True, bg="EBF3FB", color="1F3864")
    rh(ws, note_row, 40)

    cw(ws, 1, 34); cw(ws, 2, 12); cw(ws, 3, 14); cw(ws, 4, 17)
    cw(ws, 5, 14); cw(ws, 6, 17); cw(ws, 7, 12); cw(ws, 8, 17); cw(ws, 9, 14)


# ── COMPETITOR ANALYSIS — names + niches visible, details teased ──────────────
def build_free_competitor_sheet(ws, data):
    section_header(ws, 1, "COMPETITOR ANALYSIS  ·  Preview", span=3)

    COMP_COLORS = [
        ("4472C4", "EBF3FB"),
        ("ED7D31", "FFF3EC"),
        ("70AD47", "EFF7E8"),
    ]
    # Which fields to show vs lock
    VISIBLE_FIELDS = {"url", "niche", "strengths", "your_edge"}

    FIELD_LABELS = [
        ("WEBSITE",             "url"),
        ("NICHE",               "niche"),
        ("STRATEGY",            "strategy"),
        ("CONTENT APPROACH",    "content_approach"),
        ("BUSINESS MODEL",      "business_model"),
        ("FLAGSHIP OFFER",      "flagship_offer"),
        ("FLAGSHIP PRICE",      "flagship_price"),
        ("FUNNEL STRUCTURE",    "funnel_structure"),
        ("EST. ANNUAL REVENUE", "estimated_revenue"),
        ("AUDIENCE SIZE",       "audience_size"),
        ("STRENGTHS",           "strengths"),
        ("WEAKNESSES",          "weaknesses"),
        ("YOUR EDGE OVER THEM", "your_edge"),
    ]

    current_row = 3
    for idx, comp in enumerate(data.get("competitors", [])[:3]):
        header_bg, body_bg = COMP_COLORS[idx]
        comp_name = comp.get("name", f"Competitor {idx + 1}")
        # Only show names for Competitor 1
        is_secret_comp = idx > 0

        label_text = f"🔒 COMPETITOR {idx + 1} — [Unlock Identity]" if is_secret_comp else f"COMPETITOR {idx + 1} — {comp_name}"
        cl(ws, current_row, 1, label_text,
           bold=True, color="FFFFFF", bg=header_bg if not is_secret_comp else LOCK_FG, size=11)
        ws.merge_cells(f"A{current_row}:C{current_row}")
        rh(ws, current_row, 22)
        current_row += 1

        col_headers(ws, current_row,
                    ["FIELD", "DETAIL", "YOUR NOTES / IMPLICATIONS"],
                    bg=header_bg if not is_secret_comp else LOCK_FG)
        current_row += 1

        for label, key in FIELD_LABELS:
            value  = comp.get(key, "")
            locked = (key not in VISIBLE_FIELDS) or is_secret_comp
            alt_bg = body_bg if current_row % 2 == 0 else "FFFFFF"

            if key == "your_edge" and not is_secret_comp:
                # Always show "your edge" for Comp 1
                cl(ws, current_row, 1, label, bold=True,
                   bg="1F3864", color="FFD700", size=10)
                cl(ws, current_row, 2, value, bold=True,
                   bg="1F3864", color="FFFFFF", size=10)
                cl(ws, current_row, 3, "", bg="1F3864")
            elif locked:
                cl(ws, current_row, 1, label, bold=True,
                   bg="D9E1F2", color="1F3864")
                cl(ws, current_row, 2, _tease(value, keep=30 if is_secret_comp else 50),
                   italic=True, color=LOCK_FG, bg=LOCK_BG)
                _lock_cell(ws, current_row, 3, "🔒 [Unlock Details]")
            else:
                cl(ws, current_row, 1, label, bold=True,
                   bg="D9E1F2", color="1F3864")
                cl(ws, current_row, 2, value, bg=alt_bg)
                cl(ws, current_row, 3, "", bg=alt_bg)

            rh(ws, current_row, 50)
            current_row += 1

        current_row += 1  # spacer between competitors

    ws.merge_cells(f"A{current_row}:C{current_row}")
    cl(ws, current_row, 1,
       "🔒 Full competitor details — pricing, funnel structure, weaknesses, and your complete edge — are in the Full Plan.",
       italic=True, bg="E2EFDA", color="375623", size=10)
    rh(ws, current_row, 30)

    cw(ws, 1, 26); cw(ws, 2, 52); cw(ws, 3, 45)


# ── PAID ACQUISITION — structure visible, content teased ──────────────────────
def build_free_paid_sheet(ws, data):
    section_header(ws, 1, "PAID ACQUISITION  ·  Preview", span=2)

    rows_config = [
        ("AD GOAL",                True),
        ("AD HOOK FORMULA",        False),
        ("WEBINAR — Self Recognition", False),
        ("WEBINAR — Epiphany",     False),
        ("WEBINAR — Invitation",   False),
        ("DISCOVERY CALL GOAL",    True),
        ("CALL — Listen For",      False),
        ("CALL — Red Flags",       False),
        ("CALL — Close",           False),
    ]
    # The actual content (same as build_paid_sheet)
    rows_content = [
        "Drive registrations to your free webinar. You are selling a free training, not coaching.",
        "Line 1: Call out the exact person and their exact pain. Line 2: Name the real problem they have not admitted. Line 3: Introduce the webinar as the answer. Line 4: One clear CTA with genuine urgency.",
        "Describe their daily reality so precisely they feel you are reading their diary. Use their exact words. Pause for responses. This is the most important phase.",
        "Show them the problem is not what they think. Introduce your framework as the real explanation. Maximum 3 insights. Depth over breadth.",
        "Invite the RIGHT people to a call. Name exactly who it is NOT for. Frame it as a fit conversation, not a sales call.",
        "Determine fit. Never convince. If you are selling, you have already lost. The right client should be selling themselves.",
        "Specific answers not vague ones. They take responsibility for their situation. Their goal matches your program outcome. You feel genuine excitement about helping them.",
        "First question is about price. Blames only external factors. Expects results in two weeks. You feel a knot in your stomach.",
        "If YES: Here is how we get started. If NOT YET: What specifically needs to change for this to be a yes. If NO: This does not sound like the right fit. Never discount to close.",
    ]

    for ri, ((label, visible), val) in enumerate(zip(rows_config, rows_content), 3):
        cl(ws, ri, 1, label, bold=True, bg="D9E1F2", color="1F3864", size=10)
        if visible:
            cl(ws, ri, 2, val, bg="F7F9FC" if ri % 2 == 0 else "FFFFFF")
        else:
            cl(ws, ri, 2, _tease(val, keep=60),
               italic=True, color=LOCK_FG, bg=LOCK_BG)
        rh(ws, ri, 55)

    cw(ws, 1, 28); cw(ws, 2, 75)


# ── UPGRADE CTA — updated with direct link ────────────────────────────────────
def build_upgrade_cta_sheet(ws, payment_url: str = ""):
    """Summary sheet listing every premium section with clear upgrade CTA."""
    section_header(ws, 1, "🔒 YOUR FULL PLAN — PREMIUM SECTIONS", span=2)

    locked_sections = [
        ("😨 Fear Reframe (Full)",
         "The real truth behind your fear + 3 specific, personalised actions to take this week."),
        ("📣 Marketing Strategy (Full Detail)",
         "5 tailored channels with full content pillars, example posts, and KPIs."),
        ("💰 Revenue Projection (Complete)",
         "Year 1 high, Year 2, and YoY growth for every tier — plus your personalised revenue note."),
        ("🤝 Trust Channel Benchmarks",
         "Partnerships + Referrals benchmarks with estimated annual clients, revenue, and next actions."),
        ("🕵 Competitor Analysis (Full)",
         "Full pricing, funnel, strengths, weaknesses, and your edge for all 3 named competitors."),
        ("📈 Paid Acquisition Blueprint (Full)",
         "Complete ad hook formula, webinar script, and discovery call framework."),
        ("📅 90-Day Plan — Weeks 5–12",
         "Social proof build, first client close, system setup, and scale — with milestones."),
        ("💼 Full Funnel Revenue (Mid-Ticket + Flagship)",
         "Monthly client estimates and full revenue projections for your top two tiers."),
    ]

    for ri, (label, description) in enumerate(locked_sections, 3):
        cl(ws, ri, 1, f"🔒  {label}", bold=True, bg="D9E1F2", color="1F3864", size=11)
        cl(ws, ri, 2,
           f"{description}\n\n➡  Unlock in the Full Coaching Business Plan.",
           bg="FFF8E7", color="856404")
        rh(ws, ri, 70)

    cta_row = 3 + len(locked_sections) + 1
    ws.merge_cells(f"A{cta_row}:B{cta_row}")
    upgrade_text = (
        "✨  UPGRADE TO THE FULL PLAN  ✨\n\n"
        "You've seen your Offer Blueprint, partial Funnel, and previews of every section above.\n"
        "Join 80+ coaches who upgraded this month to unlock the complete strategy.\n\n"
        "The remaining sections — Revenue Projections, Competitor Deep-Dives, Full Marketing,\n"
        "Fear Reframe, Paid Acquisition, and the complete 90-Day Plan — are waiting for you."
    )
    cl(ws, cta_row, 1, upgrade_text, bold=True, bg="1F3864", color="FFFFFF", size=12)
    rh(ws, cta_row, 120)

    link_row = cta_row + 1
    ws.merge_cells(f"A{link_row}:B{link_row}")
    tag_cell = cl(ws, link_row, 1,
                  "👉  CLICK HERE TO UNLOCK YOUR FULL PLAN  →",
                  bold=True, bg="FFD700", color="1F3864", size=14, align="center")
    if payment_url:
        tag_cell.hyperlink = payment_url
    rh(ws, link_row, 40)

    cw(ws, 1, 32); cw(ws, 2, 72)


# ─────────────────────────────────────────────
# MAIN: BUILD FREE EXCEL
# ─────────────────────────────────────────────
def build_free_excel(data: dict, file_path: str, payment_url: str = ""):
    """
    Teaser report with ALL sheets and ALL columns present.
    Free tiers/weeks show full content; locked sections show teased excerpts.
    Gives people the complete picture of what they're buying — drives upgrades.
    """
    wb = Workbook()

    # Sheet 1 — Offer Blueprint: fully unlocked (best hook to start)
    ws1 = wb.active
    ws1.title = "Your Offer"
    build_offer_sheet(ws1, data, is_premium=False)

    # Sheet 2 — Full funnel (all 4 tiers, revenue locked on mid/flagship)
    ws2 = wb.create_sheet("Your Funnel")
    build_free_funnel_sheet(ws2, data)

    # Sheet 3 — Full 90-day plan (all 5 entries, weeks 5-12 teased)
    ws3 = wb.create_sheet("90-Day Plan")
    build_free_action_sheet(ws3, data)

    # Sheet 4 — Fear Reframe (fear visible, actions teased)
    ws4 = wb.create_sheet("Fear Reframe")
    build_free_fear_sheet(ws4, data)

    # Sheet 5 — Marketing Strategy (Per-channel sheets)
    build_all_marketing_sheets(wb, data, is_free=True, payment_url=payment_url)

    # Sheet 6 — Revenue (Y1 low visible, everything else locked)
    ws6 = wb.create_sheet("Revenue")
    build_free_revenue_sheet(ws6, data)

    # Sheet 7 — Trust Channel Benchmarks (Partnerships/Referrals)
    ws7 = wb.create_sheet("Trust Channels")
    build_free_trust_channel_sheet(ws7, data)

    # Sheet 8 — Competitor Analysis (names/niches/your-edge visible, details teased)
    ws8 = wb.create_sheet("Competitor Analysis")
    build_free_competitor_sheet(ws8, data)

    # Sheet 9 — Paid Acquisition (structure visible, content teased; conditional)
    if data.get("include_paid_funnel"):
        ws9 = wb.create_sheet("Paid Acquisition")
        build_free_paid_sheet(ws9, data)

    # Final sheet — Upgrade CTA
    ws_cta = wb.create_sheet("🔒 Unlock Full Plan")
    build_upgrade_cta_sheet(ws_cta, payment_url)

    wb.save(file_path)


# ─────────────────────────────────────────────
# BUILD EXCEL
# ─────────────────────────────────────────────
def build_excel(data: dict, file_path: str):
    wb = Workbook()
    ws1 = wb.active;          ws1.title = "Your Offer";       build_offer_sheet(ws1, data, is_premium=True)
    ws2 = wb.create_sheet("Your Funnel");                     build_funnel_sheet(ws2, data)
    ws3 = wb.create_sheet("90-Day Plan");                     build_action_sheet(ws3, data)
    ws4 = wb.create_sheet("Fear Reframe");                    build_fear_sheet(ws4, data)
    # Marketing Strategy Sheets (One per channel)
    build_all_marketing_sheets(wb, data, is_free=False)
    ws6 = wb.create_sheet("Revenue");                         build_revenue_sheet(ws6, data)
    ws7 = wb.create_sheet("Trust Channels");                  build_trust_channel_sheet(ws7, data)
    ws8 = wb.create_sheet("Competitor Analysis");             build_competitor_sheet(ws8, data)
    if data.get("include_paid_funnel"):
        ws9 = wb.create_sheet("Paid Acquisition");            build_paid_sheet(ws9, data)
    wb.save(file_path)


# ── OFFER SHEET (unchanged) ──────────────────
def build_offer_sheet(ws, data, is_premium=False):
    if is_premium:
        ws.merge_cells("A1:D1")
        cl(ws, 1, 1, "🏆 WELCOME TO YOUR FULL COACHING PLAN — LET'S SCALE!", bold=True, bg="1F3864", color="FFD700", size=14, align="center")
        rh(ws, 1, 35)
        offset = 1
    else:
        offset = 0

    section_header(ws, 1 + offset, "YOUR PERSONALISED COACHING OFFER", span=4)
    ws.merge_cells(f"A{3 + offset}:D{3 + offset}")
    cl(ws, 3 + offset, 1, "YOUR ONE-SENTENCE OFFER", bold=True, bg="2E75B6", color="FFFFFF", size=11)
    ws.merge_cells(f"A{4 + offset}:D{4 + offset}")
    cl(ws, 4 + offset, 1, data.get("offer_sentence", ""), bold=True, color="1F3864", size=12, bg="EBF3FB")
    rh(ws, 4 + offset, 55)
    if data.get("personal_note"):
        ws.merge_cells(f"A{6 + offset}:D{6 + offset}")
        cl(ws, 6 + offset, 1, f"Note: {data['personal_note']}", italic=True, bg="E2EFDA", color="375623")
        rh(ws, 6 + offset, 40)
    section_header(ws, 8 + offset, "OFFER LAYERS", span=4, bg="2E75B6")
    col_headers(ws, 9 + offset, ["LAYER", "RAW INPUT", "REFINED", "WHY THIS SELLS"])
    for ri, layer in enumerate(data.get("offer_layers", []), 10 + offset):
        bg = "F7F9FC" if ri % 2 == 0 else "FFFFFF"
        cl(ws, ri, 1, layer.get("layer", ""), bold=True, bg="D9E1F2", color="1F3864")
        cl(ws, ri, 2, layer.get("raw", ""), bg=bg)
        cl(ws, ri, 3, layer.get("refined", ""), bg=bg)
        cl(ws, ri, 4, layer.get("why", ""), bg=bg)
        rh(ws, ri, 65)
    cw(ws, 1, 18); cw(ws, 2, 35); cw(ws, 3, 42); cw(ws, 4, 40)


# ── FUNNEL SHEET — added Est. Monthly Clients + Revenue Low/High ──
def build_funnel_sheet(ws, data):
    section_header(ws, 1, "YOUR RECOMMENDED FUNNEL", span=8)
    col_headers(ws, 3, [
        "TIER", "NAME", "FORMAT", "PRICE", "PURPOSE",
        "EST. MONTHLY CLIENTS", "MONTHLY REV (LOW)", "MONTHLY REV (HIGH)"
    ])
    colors = {
        "LEAD MAGNET": "70AD47",
        "LOW-TICKET":  "4472C4",
        "MID-TICKET":  "ED7D31",
        "FLAGSHIP":    "C00000",
    }
    for ri, item in enumerate(data.get("funnel", []), 4):
        tier = item.get("tier", "")
        bg   = colors.get(tier, "FFFFFF")
        cl(ws, ri, 1, tier, bold=True, bg=bg, color="FFFFFF")
        cl(ws, ri, 2, item.get("name", ""))
        cl(ws, ri, 3, item.get("format", ""))
        cl(ws, ri, 4, item.get("price", ""), bold=True, color="1F3864")
        cl(ws, ri, 5, item.get("purpose", ""))
        c6 = cl(ws, ri, 6, item.get("monthly_clients", 0), align="center")
        c7 = cl(ws, ri, 7, item.get("monthly_revenue_low", 0),  align="right")
        c8 = cl(ws, ri, 8, item.get("monthly_revenue_high", 0), align="right")
        money_fmt(c7); money_fmt(c8)
        rh(ws, ri, 50)

    # Totals row
    tr = 4 + len(data.get("funnel", []))
    cl(ws, tr, 1, "MONTHLY TOTALS", bold=True, bg="1F3864", color="FFFFFF")
    cl(ws, tr, 5, "", bg="1F3864")
    for col in [2, 3, 4]:
        cl(ws, tr, col, "", bg="D9E1F2")
    c7t = ws.cell(row=tr, column=7, value=f"=SUM(G4:G{tr-1})")
    c8t = ws.cell(row=tr, column=8, value=f"=SUM(H4:H{tr-1})")
    for c in [c7t, c8t]:
        c.font = Font(bold=True, color="FFFFFF", name="Arial", size=10)
        c.fill = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
        c.alignment = Alignment(horizontal="right", vertical="top")
        money_fmt(c)
    c6t = ws.cell(row=tr, column=6, value=f"=SUM(F4:F{tr-1})")
    c6t.font = Font(bold=True, color="FFFFFF", name="Arial", size=10)
    c6t.fill = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
    c6t.alignment = Alignment(horizontal="center", vertical="top")
    rh(ws, tr, 22)

    cw(ws, 1, 16); cw(ws, 2, 26); cw(ws, 3, 22); cw(ws, 4, 14)
    cw(ws, 5, 38); cw(ws, 6, 20); cw(ws, 7, 18); cw(ws, 8, 18)


# ── 90-DAY PLAN — added STATUS column ────────
def build_action_sheet(ws, data):
    section_header(ws, 1, "YOUR 90-DAY ACTION PLAN", span=5)
    col_headers(ws, 3, ["WEEK", "FOCUS", "ACTIONS", "MILESTONE", "STATUS"])
    phase_colors = ["4472C4", "4472C4", "ED7D31", "ED7D31", "C00000"]
    STATUS_OPTIONS = ["⬜ Not Started", "🔄 In Progress", "✅ Done"]

    for ri, item in enumerate(data.get("action_plan", []), 4):
        bg = phase_colors[ri - 4] if (ri - 4) < len(phase_colors) else "FFFFFF"
        cl(ws, ri, 1, item.get("week", ""),      bold=True, bg=bg, color="FFFFFF")
        cl(ws, ri, 2, item.get("focus", ""),     bold=True, bg="F7F9FC")
        cl(ws, ri, 3, item.get("actions", ""))
        cl(ws, ri, 4, item.get("milestone", ""), italic=True, color="375623", bg="E2EFDA")
        # Pre-fill with "Not Started"; coach updates as they go
        c = cl(ws, ri, 5, STATUS_OPTIONS[0], align="center", bg="FFF3EC")
        c.font = Font(name="Arial", size=10, color="ED7D31", bold=True)
        rh(ws, ri, 70)

    # Legend
    legend_row = 4 + len(data.get("action_plan", [])) + 1
    ws.merge_cells(f"A{legend_row}:E{legend_row}")
    cl(ws, legend_row, 1,
       "STATUS key — update as you go:  ⬜ Not Started  |  🔄 In Progress  |  ✅ Done",
       italic=True, bg="EBF3FB", color="1F3864", size=9)
    rh(ws, legend_row, 18)

    cw(ws, 1, 16); cw(ws, 2, 26); cw(ws, 3, 44); cw(ws, 4, 34); cw(ws, 5, 18)


# ── FEAR SHEET (unchanged) ───────────────────
def build_fear_sheet(ws, data):
    section_header(ws, 1, "YOUR FEAR REFRAME", span=2)
    fear = data.get("fear_reframe", {})
    rows = [
        ("THE FEAR",           fear.get("fear", ""),     "C00000", "FFE0E0"),
        ("THE REAL TRUTH",     fear.get("truth", ""),    "375623", "E2EFDA"),
        ("ACTION THIS WEEK 1", fear.get("action_1", ""), "2E75B6", "EBF3FB"),
        ("ACTION THIS WEEK 2", fear.get("action_2", ""), "2E75B6", "EBF3FB"),
        ("ACTION THIS WEEK 3", fear.get("action_3", ""), "2E75B6", "EBF3FB"),
    ]
    for ri, (label, val, label_color, val_bg) in enumerate(rows, 3):
        cl(ws, ri, 1, label, bold=True, bg="D9E1F2", color=label_color, size=11)
        cl(ws, ri, 2, val, bg=val_bg, size=11)
        rh(ws, ri, 60)
    cw(ws, 1, 22); cw(ws, 2, 70)


# ── TRUST CHANNEL BENCHMARKS (Partnerships / Referrals) ──────────────────────
def build_trust_channel_sheet(ws, data):
    section_header(ws, 1, "TRUST CHANNEL BENCHMARKS", span=3)
    col_headers(ws, 3, ["METRIC", "PARTNERSHIPS", "REFERRALS"])

    bench = data.get("trust_channel_benchmarks", {})
    partnerships = bench.get("partnerships", {})
    referrals = bench.get("referrals", {})

    def _yes_no(val: str) -> str:
        return "Yes" if str(val).strip().lower() == "yes" else "No"

    rows = [
        ("USED NOW?", _yes_no(partnerships.get("used_now", "No")), _yes_no(referrals.get("used_now", "No"))),
        ("WHY IT'S UNDERESTIMATED",
         partnerships.get("why_underestimated", ""),
         referrals.get("why_underestimated", "")),
        ("EST. ANNUAL CLIENTS (BENCHMARK)",
         partnerships.get("estimated_annual_clients", 0),
         referrals.get("estimated_annual_clients", 0)),
        ("EST. ANNUAL REVENUE (BENCHMARK)",
         partnerships.get("estimated_annual_revenue", 0),
         referrals.get("estimated_annual_revenue", 0)),
        ("BENCHMARK NOTE",
         partnerships.get("benchmark_note", ""),
         referrals.get("benchmark_note", "")),
        ("FIRST 3 ACTIONS",
         "\n".join(f"• {a}" for a in partnerships.get("first_actions", []) if a),
         "\n".join(f"• {a}" for a in referrals.get("first_actions", []) if a)),
    ]

    for ri, (label, p_val, r_val) in enumerate(rows, 4):
        bg = "F7F9FC" if ri % 2 == 0 else "FFFFFF"
        cl(ws, ri, 1, label, bold=True, bg="D9E1F2", color="1F3864")
        p_cell = cl(ws, ri, 2, p_val, bg=bg)
        r_cell = cl(ws, ri, 3, r_val, bg=bg)
        if label.startswith("EST. ANNUAL REVENUE"):
            money_fmt(p_cell); money_fmt(r_cell)
        rh(ws, ri, 70 if label == "FIRST 3 ACTIONS" else 55)

    cw(ws, 1, 32); cw(ws, 2, 46); cw(ws, 3, 46)


def build_free_trust_channel_sheet(ws, data):
    section_header(ws, 1, "TRUST CHANNEL BENCHMARKS  ·  Preview", span=3)
    col_headers(ws, 3, ["METRIC", "PARTNERSHIPS", "REFERRALS"])

    bench = data.get("trust_channel_benchmarks", {})
    partnerships = bench.get("partnerships", {})
    referrals = bench.get("referrals", {})

    def _yes_no(val: str) -> str:
        return "Yes" if str(val).strip().lower() == "yes" else "No"

    p_used = _yes_no(partnerships.get("used_now", "No"))
    r_used = _yes_no(referrals.get("used_now", "No"))

    rows = [
        ("USED NOW?", p_used, r_used, False),
        ("WHY IT'S UNDERESTIMATED",
         partnerships.get("why_underestimated", ""),
         referrals.get("why_underestimated", ""),
         False),
        ("EST. ANNUAL CLIENTS (BENCHMARK)",
         partnerships.get("estimated_annual_clients", 0),
         referrals.get("estimated_annual_clients", 0),
         True),
        ("EST. ANNUAL REVENUE (BENCHMARK)",
         partnerships.get("estimated_annual_revenue", 0),
         referrals.get("estimated_annual_revenue", 0),
         True),
        ("BENCHMARK NOTE",
         partnerships.get("benchmark_note", ""),
         referrals.get("benchmark_note", ""),
         True),
        ("FIRST 3 ACTIONS",
         "\n".join(f"• {a}" for a in partnerships.get("first_actions", []) if a),
         "\n".join(f"• {a}" for a in referrals.get("first_actions", []) if a),
         True),
    ]

    for ri, (label, p_val, r_val, lockable) in enumerate(rows, 4):
        bg = "F7F9FC" if ri % 2 == 0 else "FFFFFF"
        cl(ws, ri, 1, label, bold=True, bg="D9E1F2", color="1F3864")

        def _write_channel(col, val, used_now):
            should_lock = lockable and used_now == "No"
            if should_lock:
                _lock_cell(ws, ri, col, "🔒 [Unlock in Full Plan]")
                return None
            return cl(ws, ri, col, val, bg=bg)

        p_cell = _write_channel(2, p_val, p_used)
        r_cell = _write_channel(3, r_val, r_used)

        if label.startswith("EST. ANNUAL REVENUE"):
            if p_cell:
                money_fmt(p_cell)
            if r_cell:
                money_fmt(r_cell)
        rh(ws, ri, 70 if label == "FIRST 3 ACTIONS" else 55)

    cw(ws, 1, 32); cw(ws, 2, 46); cw(ws, 3, 46)

# ── MARKETING (REPLACED) ──────────────────────
def build_marketing_sheet(ws, data):
    """Obsolete - replaced by build_all_marketing_sheets"""
    pass


# ── REVENUE — full numeric rebuild with totals + YoY growth ──
def build_revenue_sheet(ws, data):
    section_header(ws, 1, "REVENUE PROJECTION", span=9)
    col_headers(ws, 3, [
        "PROGRAM", "PRICE",
        "Y1 UNITS (LOW)", "Y1 REVENUE (LOW)",
        "Y1 UNITS (HIGH)", "Y1 REVENUE (HIGH)",
        "Y2 UNITS", "Y2 REVENUE",
        "YoY GROWTH"
    ])

    items = data.get("revenue", [])
    data_start = 4

    for ri, item in enumerate(items, data_start):
        bg = "F7F9FC" if ri % 2 == 0 else "FFFFFF"
        cl(ws, ri, 1, item.get("program", ""),          bold=True, bg=bg, color="1F3864")
        c2 = cl(ws, ri, 2, item.get("price_numeric", 0), bg=bg, align="right")
        money_fmt(c2)

        c3 = cl(ws, ri, 3, item.get("year1_low_units", 0),    bg=bg, align="center")
        c4 = cl(ws, ri, 4, item.get("year1_low_revenue", 0),  bg=bg, align="right")
        c5 = cl(ws, ri, 5, item.get("year1_high_units", 0),   bg=bg, align="center")
        c6 = cl(ws, ri, 6, item.get("year1_high_revenue", 0), bg=bg, align="right")
        c7 = cl(ws, ri, 7, item.get("year2_units", 0),        bg=bg, align="center")
        c8 = cl(ws, ri, 8, item.get("year2_revenue", 0),      bg=bg, align="right")
        money_fmt(c4); money_fmt(c6); money_fmt(c8)

        # YoY growth = (Y2 revenue - Y1 high revenue) / Y1 high revenue
        row_letter = ri
        c9 = ws.cell(row=ri, column=9,
                     value=f"=IF(F{row_letter}=0,\"\",((H{row_letter}-F{row_letter})/F{row_letter}))")
        c9.font = Font(name="Arial", size=10, bold=True, color="375623")
        c9.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        c9.alignment = Alignment(horizontal="center", vertical="top")
        pct_fmt(c9)
        rh(ws, ri, 30)

    # Totals row
    tr = data_start + len(items)
    cl(ws, tr, 1, "TOTAL", bold=True, bg="1F3864", color="FFFFFF")
    cl(ws, tr, 2, "",      bg="1F3864")
    cl(ws, tr, 3, "",      bg="D9E1F2")
    cl(ws, tr, 5, "",      bg="D9E1F2")
    cl(ws, tr, 7, "",      bg="D9E1F2")

    for col_idx, col_letter in [(4, "D"), (6, "F"), (8, "H")]:
        c = ws.cell(row=tr, column=col_idx,
                    value=f"=SUM({col_letter}{data_start}:{col_letter}{tr-1})")
        c.font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        c.fill = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
        c.alignment = Alignment(horizontal="right", vertical="top")
        money_fmt(c)

    # YoY growth on totals
    ct = ws.cell(row=tr, column=9,
                 value=f"=IF(F{tr}=0,\"\",(H{tr}-F{tr})/F{tr})")
    ct.font = Font(name="Arial", size=11, bold=True, color="FFD700")
    ct.fill = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
    ct.alignment = Alignment(horizontal="center", vertical="top")
    pct_fmt(ct)
    rh(ws, tr, 26)

    # Note row
    note_row = tr + 1
    ws.merge_cells(f"A{note_row}:I{note_row}")
    cl(ws, note_row, 1, data.get("revenue_note", ""), italic=True, bg="EBF3FB", color="1F3864")
    rh(ws, note_row, 45)

    cw(ws, 1, 34); cw(ws, 2, 12); cw(ws, 3, 14); cw(ws, 4, 17)
    cw(ws, 5, 14); cw(ws, 6, 17); cw(ws, 7, 12); cw(ws, 8, 17); cw(ws, 9, 14)


# ── COMPETITOR SHEET ─────────────────────────
def build_competitor_sheet(ws, data):
    section_header(ws, 1, "COMPETITOR ANALYSIS — Know Who You're Up Against", span=3)
    LABEL_BG  = "D9E1F2"
    LABEL_COL = "1F3864"
    COMP_COLORS = [
        ("4472C4", "EBF3FB"),
        ("ED7D31", "FFF3EC"),
        ("70AD47", "EFF7E8"),
    ]
    FIELD_LABELS = [
        ("WEBSITE",             "url"),
        ("NICHE",               "niche"),
        ("STRATEGY",            "strategy"),
        ("CONTENT APPROACH",    "content_approach"),
        ("BUSINESS MODEL",      "business_model"),
        ("FLAGSHIP OFFER",      "flagship_offer"),
        ("FLAGSHIP PRICE",      "flagship_price"),
        ("FUNNEL STRUCTURE",    "funnel_structure"),
        ("EST. ANNUAL REVENUE", "estimated_revenue"),
        ("AUDIENCE SIZE",       "audience_size"),
        ("STRENGTHS",           "strengths"),
        ("WEAKNESSES",          "weaknesses"),
        ("YOUR EDGE OVER THEM", "your_edge"),
    ]
    current_row = 3
    for idx, comp in enumerate(data.get("competitors", [])[:3]):
        header_bg, body_bg = COMP_COLORS[idx]
        comp_name = comp.get("name", f"Competitor {idx + 1}")
        cl(ws, current_row, 1, f"COMPETITOR {idx + 1} — {comp_name}",
           bold=True, color="FFFFFF", bg=header_bg, size=11)
        ws.merge_cells(f"A{current_row}:C{current_row}")
        rh(ws, current_row, 22)
        current_row += 1
        col_headers(ws, current_row,
                    ["FIELD", "DETAIL", "YOUR NOTES / IMPLICATIONS"],
                    bg=header_bg)
        current_row += 1
        for label, key in FIELD_LABELS:
            value = comp.get(key, "")
            if key == "your_edge":
                cl(ws, current_row, 1, label, bold=True, bg="1F3864", color="FFD700", size=10)
                cl(ws, current_row, 2, value, bold=True, bg="1F3864", color="FFFFFF", size=10)
                cl(ws, current_row, 3, "", bg="1F3864")
            else:
                alt_bg = body_bg if current_row % 2 == 0 else "FFFFFF"
                cl(ws, current_row, 1, label, bold=True, bg=LABEL_BG, color=LABEL_COL)
                cl(ws, current_row, 2, value, bg=alt_bg)
                cl(ws, current_row, 3, "", bg=alt_bg)
            rh(ws, current_row, 50)
            current_row += 1
        current_row += 1

    ws.merge_cells(f"A{current_row}:C{current_row}")
    cl(ws, current_row, 1,
       "💡 Fill in YOUR NOTES column with what you will do differently based on each competitor's weaknesses.",
       italic=True, bg="E2EFDA", color="375623", size=10)
    rh(ws, current_row, 30)
    cw(ws, 1, 26); cw(ws, 2, 52); cw(ws, 3, 45)


# ── PAID ACQUISITION (unchanged) ─────────────
def build_paid_sheet(ws, data):
    section_header(ws, 1, "PAID ACQUISITION — Ads to Webinar to Discovery Call", span=2)
    rows = [
        ("AD GOAL",
         "Drive registrations to your free webinar. You are selling a free training, not coaching."),
        ("AD HOOK FORMULA",
         "Line 1: Call out the exact person and their exact pain. "
         "Line 2: Name the real problem they have not admitted. "
         "Line 3: Introduce the webinar as the answer. "
         "Line 4: One clear CTA with genuine urgency."),
        ("WEBINAR — Self Recognition",
         "Describe their daily reality so precisely they feel you are reading their diary. "
         "Use their exact words. Pause for responses. This is the most important phase."),
        ("WEBINAR — Epiphany",
         "Show them the problem is not what they think. "
         "Introduce your framework as the real explanation. Maximum 3 insights. Depth over breadth."),
        ("WEBINAR — Invitation",
         "Invite the RIGHT people to a call. Name exactly who it is NOT for. "
         "Frame it as a fit conversation, not a sales call."),
        ("DISCOVERY CALL GOAL",
         "Determine fit. Never convince. If you are selling, you have already lost. "
         "The right client should be selling themselves."),
        ("CALL — Listen For",
         "Specific answers not vague ones. They take responsibility for their situation. "
         "Their goal matches your program outcome. You feel genuine excitement about helping them."),
        ("CALL — Red Flags",
         "First question is about price. Blames only external factors. "
         "Expects results in two weeks. You feel a knot in your stomach."),
        ("CALL — Close",
         "If YES: Here is how we get started. "
         "If NOT YET: What specifically needs to change for this to be a yes. "
         "If NO: This does not sound like the right fit. Here is what I would suggest instead. "
         "Never discount to close."),
    ]
    for ri, (label, val) in enumerate(rows, 3):
        cl(ws, ri, 1, label, bold=True, bg="D9E1F2", color="1F3864", size=10)
        cl(ws, ri, 2, val, bg="F7F9FC" if ri % 2 == 0 else "FFFFFF")
        rh(ws, ri, 55)
    cw(ws, 1, 28); cw(ws, 2, 75)


# ─────────────────────────────────────────────
# STRIPE ROUTES
# ─────────────────────────────────────────────
@app.route('/payment', methods=['GET'])
def payment():
    key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    file_id = request.args.get('file_id', '')
    return render_template('payment.html', key=key, file_id=file_id)


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    # 1. Check for API key
    if not stripe.api_key:
        err_msg = "STRIPE_SECRET_KEY is not set in environment variables."
        app.logger.error(f"CRITICAL: {err_msg}")
        return jsonify(error=err_msg), 500 # Use 500 for configuration errors

    try:
        body = request.get_json(silent=True) or {}
        file_id = body.get('file_id', '')
        tier = body.get('tier', 'standard')
        
        if tier == 'premium':
            price_amount = 60000
            product_name = 'Full Plan + 1-on-1 Video Review'
        else:
            price_amount = 15000
            product_name = 'Full Coaching Business Plan'

        # 2. Create the session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': product_name,
                        },
                        'unit_amount': price_amount,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.host_url + f'success?file_id={file_id}&tier={tier}',
            cancel_url=request.host_url + 'cancel',
            metadata={'file_id': file_id, 'tier': tier},
        )
        return jsonify({'id': checkout_session.id})
    except stripe.error.StripeError as e:
        app.logger.error(f"Stripe Specific Error: {e.user_message or str(e)}")
        return jsonify(error=f"Stripe error: {e.user_message or str(e)}"), 400
    except Exception as e:
        app.logger.error(f"Unexpected error in create-checkout-session: {e}")
        return jsonify(error="An unexpected internal error occurred."), 500


@app.route('/success')
def success():
    file_id = request.args.get('file_id', '')
    tier = request.args.get('tier', 'standard')
    
    tier_msg = "Your full Coaching Business Plan is ready."
    if tier == 'premium':
        tier_msg = "Your full Plan is ready, and we'll be in touch shortly for your 1-on-1 Video Review!"

    if file_id and file_id.isalnum():
        download_url = f"{request.host_url}download/{file_id}"
        return f"""
        <html><body style="font-family:Arial;text-align:center;padding:60px;">
          <h1 style="color:#4338ca;">🎉 Payment confirmed!</h1>
          <p style="font-size:18px;">{tier_msg}</p>
          <a href="{download_url}" style="display:inline-block;margin-top:20px;
             background:#4338ca;color:white;padding:14px 32px;
             border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">
            ⬇ Download Your Full Plan
          </a>
          { '<p style="margin-top:20px;color:#666;">Check your email for next steps regarding your video review.</p>' if tier == 'premium' else '' }
        </body></html>
        """
    return "<h1>Thanks for your order!</h1><p>Check your email for your report.</p>"


@app.route('/cancel')
def cancel():
    return "<h1>Order cancelled.</h1><p><a href='/'>Return home</a></p>"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
