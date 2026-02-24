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

from emails import email_1_html, email_2_html, email_3_html, email_4_html, email_5_html

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
        resend.Emails.send(params)
    except Exception as exc:
        # Log but don't crash — email failure should not break the webhook
        app.logger.error(f"Resend error sending to {to}: {exc}")


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
        (0, "Your free Coaching Business Snapshot is here 🎯",
         email_1_html(name, free_url, payment_url, unsubscribe_url), True),
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
    app.logger.info(f"Scheduled 5-email sequence for {to_email} (file_id={file_id})")


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
- include_paid_funnel should be true only if Q15 answer is NOT No budget right now
- Revenue fields (year1_low_units, year1_low_revenue, year1_high_units, year1_high_revenue,
  year2_units, year2_revenue, price_numeric) MUST be plain integers — no $ signs, no text
- Funnel fields (monthly_clients, monthly_revenue_low, monthly_revenue_high) MUST be plain integers
- For competitors: identify 3 REAL named competitors in the same niche with actual pricing and
  business model details — never invent fictional coaches"""


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

    file_id = data["file_id"]
    email = data["email"]

    # Remove all 5 possible scheduled jobs for this file_id
    for delay in [0, 1, 2, 4, 6]:
        job_id = f"{file_id}_email_{delay}"
        try:
            scheduler.remove_job(job_id)
        except:
            pass # Job might have already run

    # Also remove the token
    if token in _UNSUB_TOKENS:
        del _UNSUB_TOKENS[token]

    return f"<h1>You have been unsubscribed.</h1><p>We won't send any more emails to {email}.</p>"


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
    form_data = request.form.to_dict()
    respondent_email = form_data.get("email", "")
    respondent_name = form_data.get("name", "")

    if not respondent_email:
        return "Email is required to receive your plan.", 400

    # Map form fields to the Q1-Q16 keys
    answers = {}
    for i in range(1, 17):
        key = f"Q{i}"
        answers[key] = form_data.get(key, "")

    file_id = str(uuid.uuid4())[:8]

    # Generate plan and cache it
    plan = call_openai(answers)
    _PLAN_CACHE[file_id] = plan

    # Build reports
    free_path = f"/tmp/free_{file_id}.xlsx"
    build_free_excel(plan, free_path)
    premium_path = f"/tmp/plan_{file_id}.xlsx"
    build_excel(plan, premium_path)

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
Q11 - Content medium: {answers.get('Q11', '')}
Q12 - Audience size: {answers.get('Q12', '')}
Q13 - Biggest fear: {answers.get('Q13', '')}
Q14 - Hours per week: {answers.get('Q14', '')}
Q15 - Ad budget: {answers.get('Q15', '')}
Q16 - Success definition: "{answers.get('Q16', '')}"

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
    {{"channel": "", "frequency": "", "pillar": "", "example": "", "kpi": ""}},
    {{"channel": "", "frequency": "", "pillar": "", "example": "", "kpi": ""}},
    {{"channel": "", "frequency": "", "pillar": "", "example": "", "kpi": ""}},
    {{"channel": "", "frequency": "", "pillar": "", "example": "", "kpi": ""}},
    {{"channel": "", "frequency": "", "pillar": "", "example": "", "kpi": ""}}
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
# BUILD FREE TEASER EXCEL
# ─────────────────────────────────────────────
def build_upgrade_cta_sheet(ws, payment_url: str = ""):
    """A locked sheet that teases the premium content and drives upgrades."""
    section_header(ws, 1, "🔒 YOUR FULL PLAN — PREMIUM SECTIONS", span=2)

    locked_sections = [
        ("😨 Fear Reframe",
         "Your personalised fear reframe — the real truth behind what's holding you "
         "back and 3 specific actions to take this week."),
        ("📣 Marketing Strategy",
         "5 tailored marketing channels with frequency, content pillars, example posts, "
         "and KPIs matched to your delivery style and audience size."),
        ("💰 Revenue Projection",
         "Year 1 (low & high) and Year 2 projections for every program tier — "
         "plus YoY growth and a personalised revenue note."),
        ("🕵 Competitor Analysis",
         "3 REAL named competitors in your exact niche — pricing, funnel structure, "
         "strengths, weaknesses, and your specific edge over each one."),
        ("📈 Paid Acquisition Blueprint",
         "Ad hook formula, webinar script outline, discovery call framework — "
         "the complete paid funnel playbook written for coaches, not marketers."),
        ("📅 Full 90-Day Plan (Weeks 5–12)",
         "The second half of your action plan: social proof build, first client close, "
         "system setup, and scale — with milestones and status tracker."),
        ("💼 Full Funnel (Mid-Ticket + Flagship)",
         "Your mid-ticket and flagship offer with estimated monthly client counts "
         "and realistic revenue projections for each tier."),
    ]

    for ri, (label, description) in enumerate(locked_sections, 3):
        cl(ws, ri, 1, f"🔒  {label}", bold=True, bg="D9E1F2", color="1F3864", size=11)
        cl(ws, ri, 2,
           f"{description}\n\n➡  Unlock this section in the Full Coaching Business Plan.",
           bg="FFF8E7", color="856404")
        rh(ws, ri, 70)

    cta_row = 3 + len(locked_sections) + 1
    ws.merge_cells(f"A{cta_row}:B{cta_row}")
    upgrade_text = (
        "✨  UPGRADE TO THE FULL PLAN  ✨\n\n"
        "You've seen your Offer Blueprint, partial Funnel, and first 4 weeks of your action plan above.\n"
        "The remaining 7 premium sections — including Revenue Projections, Competitor Deep-Dives,\n"
        "Fear Reframe, Full Marketing Strategy, and the complete 90-Day Plan — are waiting for you.\n\n"
        + (f"👉  Pay once at: {payment_url}" if payment_url else "👉  Contact us to upgrade.")
    )
    cl(ws, cta_row, 1, upgrade_text,
       bold=True, bg="1F3864", color="FFD700", size=12)
    rh(ws, cta_row, 140)

    cw(ws, 1, 32); cw(ws, 2, 72)


def build_free_excel(data: dict, file_path: str, payment_url: str = ""):
    """
    Teaser report: Offer (full) + partial Funnel (top 2 tiers) +
    partial 90-Day Plan (Weeks 1-4) + Upgrade CTA sheet.
    Valuable on its own, but clearly incomplete — drives premium purchase.
    """
    wb = Workbook()

    # Sheet 1 — Full Offer Blueprint (high value, zero gatekeeping)
    ws1 = wb.active
    ws1.title = "Your Offer"
    build_offer_sheet(ws1, data)

    # Sheet 2 — Partial Funnel (Lead Magnet + Low-Ticket only)
    ws2 = wb.create_sheet("Your Funnel (Preview)")
    section_header(ws2, 1, "YOUR RECOMMENDED FUNNEL — First 2 Tiers (Preview)", span=8)
    col_headers(ws2, 3, [
        "TIER", "NAME", "FORMAT", "PRICE", "PURPOSE",
        "EST. MONTHLY CLIENTS", "MONTHLY REV (LOW)", "MONTHLY REV (HIGH)"
    ])
    colors = {"LEAD MAGNET": "70AD47", "LOW-TICKET": "4472C4"}
    funnel = data.get("funnel", [])[:2]  # Only first 2 tiers
    for ri, item in enumerate(funnel, 4):
        tier = item.get("tier", "")
        bg = colors.get(tier, "FFFFFF")
        cl(ws2, ri, 1, tier, bold=True, bg=bg, color="FFFFFF")
        cl(ws2, ri, 2, item.get("name", ""))
        cl(ws2, ri, 3, item.get("format", ""))
        cl(ws2, ri, 4, item.get("price", ""), bold=True, color="1F3864")
        cl(ws2, ri, 5, item.get("purpose", ""))
        c6 = cl(ws2, ri, 6, item.get("monthly_clients", 0), align="center")
        c7 = cl(ws2, ri, 7, item.get("monthly_revenue_low", 0), align="right")
        c8 = cl(ws2, ri, 8, item.get("monthly_revenue_high", 0), align="right")
        money_fmt(c7); money_fmt(c8)
        rh(ws2, ri, 50)
    # Locked rows for Mid-Ticket + Flagship
    for ri, label in enumerate(["🔒 MID-TICKET — Upgrade to unlock", "🔒 FLAGSHIP — Upgrade to unlock"],
                                4 + len(funnel)):
        cl(ws2, ri, 1, label, bold=True, bg="C7C7C7", color="5C5C5C")
        for col in range(2, 9):
            cl(ws2, ri, col, "Available in Premium Plan", bg="F2F2F2", color="999999", italic=True)
        rh(ws2, ri, 36)
    cw(ws2, 1, 16); cw(ws2, 2, 26); cw(ws2, 3, 22); cw(ws2, 4, 14)
    cw(ws2, 5, 38); cw(ws2, 6, 20); cw(ws2, 7, 18); cw(ws2, 8, 18)

    # Sheet 3 — Partial 90-Day Plan (Weeks 1-4 only)
    ws3 = wb.create_sheet("90-Day Plan (Preview)")
    section_header(ws3, 1, "YOUR 90-DAY ACTION PLAN — Weeks 1–4 (Preview)", span=5)
    col_headers(ws3, 3, ["WEEK", "FOCUS", "ACTIONS", "MILESTONE", "STATUS"])
    phase_colors = ["4472C4", "4472C4", "ED7D31", "ED7D31"]
    STATUS_OPTIONS = ["⬜ Not Started", "🔄 In Progress", "✅ Done"]
    action_plan = data.get("action_plan", [])[:2]  # Weeks 1-2 and 3-4 only
    for ri, item in enumerate(action_plan, 4):
        bg = phase_colors[ri - 4] if (ri - 4) < len(phase_colors) else "FFFFFF"
        cl(ws3, ri, 1, item.get("week", ""),      bold=True, bg=bg, color="FFFFFF")
        cl(ws3, ri, 2, item.get("focus", ""),     bold=True, bg="F7F9FC")
        cl(ws3, ri, 3, item.get("actions", ""))
        cl(ws3, ri, 4, item.get("milestone", ""), italic=True, color="375623", bg="E2EFDA")
        c = cl(ws3, ri, 5, STATUS_OPTIONS[0], align="center", bg="FFF3EC")
        c.font = Font(name="Arial", size=10, color="ED7D31", bold=True)
        rh(ws3, ri, 70)
    # Locked rows for remaining weeks
    for ri, label in enumerate(
        ["🔒 Weeks 5-6 — Upgrade to unlock",
         "🔒 Weeks 7-9 — Upgrade to unlock",
         "🔒 Weeks 10-12 — Upgrade to unlock"],
        4 + len(action_plan)
    ):
        cl(ws3, ri, 1, label, bold=True, bg="C7C7C7", color="5C5C5C")
        for col in range(2, 6):
            cl(ws3, ri, col, "Available in Premium Plan", bg="F2F2F2", color="999999", italic=True)
        rh(ws3, ri, 36)
    cw(ws3, 1, 16); cw(ws3, 2, 26); cw(ws3, 3, 44); cw(ws3, 4, 34); cw(ws3, 5, 18)

    # Sheet 4 — Upgrade CTA
    ws4 = wb.create_sheet("🔒 Unlock Premium Sections")
    build_upgrade_cta_sheet(ws4, payment_url)

    wb.save(file_path)


# ─────────────────────────────────────────────
# BUILD EXCEL
# ─────────────────────────────────────────────
def build_excel(data: dict, file_path: str):
    wb = Workbook()
    ws1 = wb.active;          ws1.title = "Your Offer";       build_offer_sheet(ws1, data)
    ws2 = wb.create_sheet("Your Funnel");                     build_funnel_sheet(ws2, data)
    ws3 = wb.create_sheet("90-Day Plan");                     build_action_sheet(ws3, data)
    ws4 = wb.create_sheet("Fear Reframe");                    build_fear_sheet(ws4, data)
    ws5 = wb.create_sheet("Marketing");                       build_marketing_sheet(ws5, data)
    ws6 = wb.create_sheet("Revenue");                         build_revenue_sheet(ws6, data)
    ws7 = wb.create_sheet("Competitor Analysis");             build_competitor_sheet(ws7, data)
    if data.get("include_paid_funnel"):
        ws8 = wb.create_sheet("Paid Acquisition");            build_paid_sheet(ws8, data)
    wb.save(file_path)


# ── OFFER SHEET (unchanged) ──────────────────
def build_offer_sheet(ws, data):
    section_header(ws, 1, "YOUR PERSONALISED COACHING OFFER", span=4)
    ws.merge_cells("A3:D3")
    cl(ws, 3, 1, "YOUR ONE-SENTENCE OFFER", bold=True, bg="2E75B6", color="FFFFFF", size=11)
    ws.merge_cells("A4:D4")
    cl(ws, 4, 1, data.get("offer_sentence", ""), bold=True, color="1F3864", size=12, bg="EBF3FB")
    rh(ws, 4, 55)
    if data.get("personal_note"):
        ws.merge_cells("A6:D6")
        cl(ws, 6, 1, f"Note: {data['personal_note']}", italic=True, bg="E2EFDA", color="375623")
        rh(ws, 6, 40)
    section_header(ws, 8, "OFFER LAYERS", span=4, bg="2E75B6")
    col_headers(ws, 9, ["LAYER", "RAW INPUT", "REFINED", "WHY THIS SELLS"])
    for ri, layer in enumerate(data.get("offer_layers", []), 10):
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


# ── MARKETING — added KPI column ─────────────
def build_marketing_sheet(ws, data):
    section_header(ws, 1, "YOUR MARKETING STRATEGY", span=5)
    col_headers(ws, 3, ["CHANNEL", "FREQUENCY", "CONTENT PILLAR", "EXAMPLE POST / TACTIC", "SUCCESS KPI"])
    for ri, item in enumerate(data.get("marketing", []), 4):
        bg = "F7F9FC" if ri % 2 == 0 else "FFFFFF"
        cl(ws, ri, 1, item.get("channel", ""),   bold=True, bg="D9E1F2", color="1F3864")
        cl(ws, ri, 2, item.get("frequency", ""), bg=bg)
        cl(ws, ri, 3, item.get("pillar", ""),    bg=bg)
        cl(ws, ri, 4, item.get("example", ""),   bg=bg, italic=True)
        c = cl(ws, ri, 5, item.get("kpi", ""),   bg="E2EFDA")
        c.font = Font(name="Arial", size=10, color="375623", bold=True)
        rh(ws, ri, 50)
    cw(ws, 1, 20); cw(ws, 2, 18); cw(ws, 3, 34); cw(ws, 4, 42); cw(ws, 5, 30)


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
    try:
        body = request.get_json(silent=True) or {}
        file_id = body.get('file_id', '')
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Full Coaching Business Plan',
                        },
                        'unit_amount': 4900,
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            # Pass file_id so /success can serve the right file
            success_url=request.host_url + f'success?file_id={file_id}',
            cancel_url=request.host_url + 'cancel',
            metadata={'file_id': file_id},
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403


@app.route('/success')
def success():
    file_id = request.args.get('file_id', '')
    if file_id and file_id.isalnum():
        download_url = f"{request.host_url}download/{file_id}"
        return f"""
        <html><body style="font-family:Arial;text-align:center;padding:60px;">
          <h1 style="color:#4338ca;">🎉 Payment confirmed!</h1>
          <p style="font-size:18px;">Your full Coaching Business Plan is ready.</p>
          <a href="{download_url}" style="display:inline-block;margin-top:20px;
             background:#4338ca;color:white;padding:14px 32px;
             border-radius:8px;text-decoration:none;font-weight:bold;font-size:16px;">
            ⬇ Download Your Full Plan
          </a>
        </body></html>
        """
    return "<h1>Thanks for your order!</h1><p>Check your email for your report.</p>"


@app.route('/cancel')
def cancel():
    return "<h1>Order cancelled.</h1><p><a href='/'>Return home</a></p>"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
