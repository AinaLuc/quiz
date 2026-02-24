"""
emails.py — 5-email drip sequence HTML templates.
All templates accept unsubscribe_url so every email has a compliant unsubscribe link.
"""


def _footer(unsubscribe_url: str = "") -> str:
    unsub = (
        f'<a href="{unsubscribe_url}" style="color:#9ca3af;text-decoration:underline;">Unsubscribe</a>'
        if unsubscribe_url else "Unsubscribe"
    )
    return f"""
      <tr><td style="background:#f9fafb;padding:24px 40px;text-align:center;border-top:1px solid #e5e7eb;">
        <p style="font-size:12px;color:#9ca3af;margin:0 0 6px;">
          You're receiving this because you completed the Coaching Business Quiz.
        </p>
        <p style="font-size:12px;color:#9ca3af;margin:0;">{unsub} · No spam. Ever.</p>
      </td></tr>"""


def email_1_html(name: str, free_url: str, payment_url: str, unsubscribe_url: str = "") -> str:
    """Day 0 — Immediate delivery of free report."""
    first = name.split()[0] if name else "Coach"
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;max-width:600px;">

      <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:40px 40px 32px;text-align:center;">
        <p style="color:rgba(255,255,255,0.85);font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">Your Free Report</p>
        <h1 style="color:#ffffff;font-size:28px;margin:0;line-height:1.3;">Your Coaching Business Snapshot is ready 🎯</h1>
      </td></tr>

      <tr><td style="padding:40px;">
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">Hi {first},</p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">
          You just answered questions about your coaching business — and based on what you shared,
          I've put together a personalised snapshot of what your offer could look like.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">Inside your free report:</p>
        <ul style="font-size:16px;color:#374151;line-height:1.9;margin:0 0 24px;padding-left:20px;">
          <li><strong>Your one-sentence offer</strong> — built from your exact answers</li>
          <li><strong>Your 6 offer layers</strong> — WHO, PAIN, OUTCOME, MECHANISM, PROOF, EXCLUSION</li>
          <li><strong>Your first 2 funnel tiers</strong> — lead magnet + low-ticket offer</li>
          <li><strong>Weeks 1–4 of your 90-day action plan</strong> — specific steps to launch</li>
        </ul>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:32px 0;">
          <tr><td align="center">
            <a href="{free_url}" style="display:inline-block;background:#667eea;color:#ffffff;
               font-size:17px;font-weight:bold;padding:16px 40px;border-radius:8px;
               text-decoration:none;">⬇ Download Your Free Snapshot</a>
          </td></tr>
        </table>

        <p style="font-size:15px;color:#6b7280;line-height:1.7;margin:0 0 8px;">Talk soon,<br>
          <strong style="color:#374151;">The Coaching Business Plan Team</strong></p>

        <div style="background:#f9fafb;border-left:4px solid #667eea;padding:20px 24px;border-radius:4px;margin-top:32px;">
          <p style="font-size:14px;color:#374151;margin:0 0 8px;"><strong>Want the full picture?</strong></p>
          <p style="font-size:14px;color:#6b7280;margin:0 0 12px;">
            Unlock Revenue Projections, Competitor Analysis, Fear Reframe, full Marketing Strategy,
            and the rest of your 90-Day Plan.
          </p>
          <a href="{payment_url}" style="font-size:14px;color:#667eea;font-weight:bold;text-decoration:none;">
            See what's inside the Full Plan →
          </a>
        </div>
      </td></tr>
      {_footer(unsubscribe_url)}
    </table>
  </td></tr>
</table>
</body>
</html>"""


def email_2_html(name: str, free_url: str, payment_url: str, unsubscribe_url: str = "") -> str:
    """Day 1 — Value drop."""
    first = name.split()[0] if name else "Coach"
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;max-width:600px;">

      <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:40px 40px 32px;text-align:center;">
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.3;">
          The #1 thing coaches who fill their calendar do differently
        </h1>
      </td></tr>

      <tr><td style="padding:40px;">
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">Hi {first},</p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">
          The coaches who struggle say things like <em>"I help people reach their potential."</em>
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">
          The coaches who fill their calendar say something so specific that the right person thinks:
          <em>"That's exactly me. How do I work with this person?"</em>
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">
          The difference is almost never skill. It's <strong>specificity.</strong>
          That's what the Offer section of your free snapshot is designed to build.
        </p>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
          <tr><td align="center">
            <a href="{free_url}" style="display:inline-block;background:#667eea;color:#ffffff;
               font-size:16px;font-weight:bold;padding:14px 36px;border-radius:8px;
               text-decoration:none;">Open My Free Snapshot →</a>
          </td></tr>
        </table>

        <p style="font-size:15px;color:#6b7280;line-height:1.7;margin:0;">
          — The Coaching Business Plan Team
        </p>
      </td></tr>
      {_footer(unsubscribe_url)}
    </table>
  </td></tr>
</table>
</body>
</html>"""


def email_3_html(name: str, free_url: str, payment_url: str, unsubscribe_url: str = "") -> str:
    """Day 2 — Tease locked sections."""
    first = name.split()[0] if name else "Coach"
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;max-width:600px;">

      <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:40px 40px 32px;text-align:center;">
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.3;">
          What most coaches skip — and why it quietly kills their revenue
        </h1>
      </td></tr>

      <tr><td style="padding:40px;">
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">Hi {first},</p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">
          Most coaches launch with one offer. They attract someone who's curious but not ready
          to pay $2,000–$5,000 for their flagship. That person leaves. Nothing changes.
        </p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">
          The fix is a <strong>complete funnel</strong> — a path from "I just discovered you"
          to "I want your full program."
        </p>
        <ul style="font-size:16px;color:#374151;line-height:1.9;margin:0 0 24px;padding-left:20px;">
          <li>Mid-Ticket + Flagship offers with revenue projections</li>
          <li>Year 1 &amp; Year 2 revenue across every tier</li>
          <li>3 real named competitors in your niche — pricing, funnel, and your edge</li>
        </ul>

        <div style="background:#f3f4f6;border:2px dashed #d1d5db;border-radius:8px;padding:24px;margin:24px 0;text-align:center;">
          <p style="font-size:24px;margin:0 0 8px;">🔒</p>
          <p style="font-size:15px;font-weight:bold;color:#374151;margin:0 0 4px;">All of this is in the Full Plan</p>
        </div>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
          <tr><td align="center">
            <a href="{payment_url}" style="display:inline-block;background:#667eea;color:#ffffff;
               font-size:17px;font-weight:bold;padding:16px 40px;border-radius:8px;
               text-decoration:none;">Get My Full Coaching Business Plan →</a>
          </td></tr>
        </table>
        <p style="font-size:14px;color:#9ca3af;text-align:center;margin:0 0 24px;">One-time payment. Instant download.</p>
        <p style="font-size:15px;color:#6b7280;margin:0;">— The Coaching Business Plan Team</p>
      </td></tr>
      {_footer(unsubscribe_url)}
    </table>
  </td></tr>
</table>
</body>
</html>"""


def email_4_html(name: str, free_url: str, payment_url: str, unsubscribe_url: str = "") -> str:
    """Day 4 — Personalised feel."""
    first = name.split()[0] if name else "Coach"
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;max-width:600px;">

      <tr><td style="background:linear-gradient(135deg,#667eea,#764ba2);padding:40px 40px 32px;text-align:center;">
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.3;">
          {first}, here's what stood out in your quiz answers
        </h1>
      </td></tr>

      <tr><td style="padding:40px;">
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">Hi {first},</p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">
          Two things come up almost every time for coaches in your niche:
        </p>

        <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:20px 24px;border-radius:4px;margin:0 0 20px;">
          <p style="font-size:15px;color:#92400e;margin:0;line-height:1.7;">
            <strong>1. "Nobody will pay that much for coaching."</strong><br>
            Almost never true. It's a positioning problem, not a pricing problem.
            Your full plan includes a personalised Fear Reframe with 3 concrete actions.
          </p>
        </div>

        <div style="background:#ede9fe;border-left:4px solid #7c3aed;padding:20px 24px;border-radius:4px;margin:0 0 24px;">
          <p style="font-size:15px;color:#4c1d95;margin:0;line-height:1.7;">
            <strong>2. Marketing on the wrong channels.</strong><br>
            Your full marketing strategy maps 5 specific channels to your delivery style,
            audience size, and content medium.
          </p>
        </div>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:28px 0;">
          <tr><td align="center">
            <a href="{payment_url}" style="display:inline-block;background:#667eea;color:#ffffff;
               font-size:17px;font-weight:bold;padding:16px 40px;border-radius:8px;
               text-decoration:none;">Unlock My Full Plan — $49</a>
          </td></tr>
        </table>
        <p style="font-size:15px;color:#6b7280;margin:0;">— The Coaching Business Plan Team</p>
      </td></tr>
      {_footer(unsubscribe_url)}
    </table>
  </td></tr>
</table>
</body>
</html>"""


def email_5_html(name: str, free_url: str, payment_url: str, unsubscribe_url: str = "") -> str:
    """Day 6 — Final urgency close."""
    first = name.split()[0] if name else "Coach"
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f7;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;max-width:600px;">

      <tr><td style="background:linear-gradient(135deg,#374151,#1f2937);padding:40px 40px 32px;text-align:center;">
        <p style="color:rgba(255,255,255,0.7);font-size:13px;margin:0 0 8px;text-transform:uppercase;letter-spacing:1px;">Final Email</p>
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.3;">
          This is the last time I'll mention it, {first}
        </h1>
      </td></tr>

      <tr><td style="padding:40px;">
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">Hi {first},</p>
        <p style="font-size:16px;color:#374151;line-height:1.7;margin:0 0 20px;">This is the last email in this sequence.</p>

        <div style="background:#f9fafb;border-radius:8px;padding:24px;margin:0 0 24px;">
          <p style="font-size:15px;font-weight:bold;color:#374151;margin:0 0 16px;">What's waiting for you:</p>
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr><td style="padding:8px 0;font-size:15px;color:#374151;">✅ Complete Funnel (all 4 tiers)</td></tr>
            <tr><td style="padding:8px 0;font-size:15px;color:#374151;">✅ Revenue projections Year 1 + Year 2</td></tr>
            <tr><td style="padding:8px 0;font-size:15px;color:#374151;">✅ 3 real competitors — with your edge over each</td></tr>
            <tr><td style="padding:8px 0;font-size:15px;color:#374151;">✅ Personalised Fear Reframe + 3 actions</td></tr>
            <tr><td style="padding:8px 0;font-size:15px;color:#374151;">✅ Full Marketing Strategy (5 channels + KPIs)</td></tr>
            <tr><td style="padding:8px 0;font-size:15px;color:#374151;">✅ Full 90-Day Action Plan</td></tr>
            <tr><td style="padding:8px 0;font-size:15px;color:#374151;">✅ Paid Acquisition Blueprint</td></tr>
          </table>
        </div>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 16px;">
          <tr><td align="center">
            <a href="{payment_url}" style="display:inline-block;background:#667eea;color:#ffffff;
               font-size:18px;font-weight:bold;padding:18px 44px;border-radius:8px;
               text-decoration:none;">Get My Full Plan for $49 →</a>
          </td></tr>
        </table>
        <p style="font-size:14px;color:#9ca3af;text-align:center;margin:0 0 24px;">Instant download. 14-day clarity guarantee.</p>
        <p style="font-size:15px;color:#6b7280;margin:0;">Either way — your free snapshot is yours to keep. Use it well.<br>— The Coaching Business Plan Team</p>
      </td></tr>
      {_footer(unsubscribe_url)}
    </table>
  </td></tr>
</table>
</body>
</html>"""
