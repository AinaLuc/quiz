"""
emails.py — 5-email drip sequence HTML templates.
Redesigned with luxury branding while preserving the original technical content.
"""

def _footer(unsubscribe_url: str = "") -> str:
    unsub = (
        f'<a href="{unsubscribe_url}" style="color:#a1a1aa;text-decoration:underline;">Unsubscribe</a>'
        if unsubscribe_url else "Unsubscribe"
    )
    return f"""
      <tr><td style="background:#fafafa;padding:32px 40px;text-align:center;border-top:1px solid #f4f4f5;">
        <p style="font-size:12px;color:#a1a1aa;margin:0 0 8px;font-family:'Helvetica Neue',Arial,sans-serif;">
            You're receiving this because you completed the Coaching Business Quiz.
        </p>
        <p style="font-size:12px;color:#a1a1aa;margin:0;font-family:'Helvetica Neue',Arial,sans-serif;">{unsub} · No spam. Ever.</p>
      </td></tr>"""


def email_1_html(name: str, free_url: str, payment_url: str, unsubscribe_url: str = "") -> str:
    """Day 0 — Immediate delivery of free report."""
    first = name.split()[0] if name else "Coach"
    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#fdfcfb;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fdfcfb;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:24px;overflow:hidden;max-width:600px;box-shadow:0 10px 30px rgba(0,0,0,0.03);">

      <tr><td style="background:#4f46e5;padding:48px 40px;text-align:center;">
        <p style="color:rgba(255,255,255,0.7);font-size:12px;margin:0 0 12px;text-transform:uppercase;letter-spacing:2px;font-weight:bold;">Your Free Report</p>
        <h1 style="color:#ffffff;font-size:28px;margin:0;line-height:1.2;font-weight:800;">Your Coaching Business Snapshot is ready 🎯</h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#18181b;line-height:1.8;margin:0 0 24px;">Hi {first},</p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          You just answered questions about your coaching business — and based on what you shared, I've put together a personalised snapshot of what your offer could look like.
        </p>
        
        <p style="font-size:14px;color:#71717a;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 16px;">Inside your free report:</p>
        <div style="background:#f9fafb;border-radius:16px;padding:24px;margin:0 0 32px;">
            <table width="100%" cellpadding="0" cellspacing="4">
              <tr><td style="color:#4f46e5;font-size:18px;width:24px;">✓</td><td style="font-size:15px;color:#3f3f46;"><strong>Your one-sentence offer</strong> — built from your exact answers</td></tr>
              <tr><td style="color:#4f46e5;font-size:18px;">✓</td><td style="font-size:15px;color:#3f3f46;"><strong>Your 6 offer layers</strong> — WHO, PAIN, OUTCOME, MECHANISM, PROOF, EXCLUSION</td></tr>
              <tr><td style="color:#4f46e5;font-size:18px;">✓</td><td style="font-size:15px;color:#3f3f46;"><strong>Your first 2 funnel tiers</strong> — lead magnet + low-ticket offer</td></tr>
              <tr><td style="color:#4f46e5;font-size:18px;">✓</td><td style="font-size:15px;color:#3f3f46;"><strong>Weeks 1–4 of your 90-day action plan</strong> — specific steps to launch</td></tr>
            </table>
        </div>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0 32px;">
          <tr><td align="center">
            <a href="{free_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:16px;font-weight:bold;padding:18px 44px;border-radius:16px;
               text-decoration:none;box-shadow:0 10px 20px rgba(79,70,229,0.2);">⬇ Download Your Free Snapshot</a>
          </td></tr>
        </table>

        <div style="background:#fff7ed;border:1px solid #fed7aa;padding:24px;border-radius:16px;margin:32px 0 0;">
          <p style="font-size:15px;color:#7c2d12;margin:0 0 12px;font-weight:bold;">Want the full picture?</p>
          <p style="font-size:14px;color:#9a3412;margin:0 0 16px;line-height:1.6;">
            Unlock Revenue Projections, Competitor Analysis, Fear Reframe, full Marketing Strategy, and the rest of your 90-Day Plan.
          </p>
          <a href="{payment_url}" style="font-size:14px;color:#4f46e5;font-weight:bold;text-decoration:none;">
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
<body style="margin:0;padding:0;background:#fdfcfb;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fdfcfb;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:24px;overflow:hidden;max-width:600px;box-shadow:0 10px 30px rgba(0,0,0,0.03);">

      <tr><td style="background:#4f46e5;padding:48px 40px;text-align:center;">
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.2;font-weight:800;">
          The #1 thing coaches who fill their calendar do differently
        </h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#18181b;line-height:1.8;margin:0 0 24px;">Hi {first},</p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          The coaches who struggle say things like <em>"I help people reach their potential."</em>
        </p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          The coaches who fill their calendar say something so specific that the right person thinks: 
          <em>"That's exactly me. How do I work with this person?"</em>
        </p>
        <p style="font-size:16px;color:#18181b;line-height:1.8;margin:0 0 32px;">
          The difference is almost never skill. It's <strong>specificity.</strong> That's what the Offer section of your free snapshot is designed to build.
        </p>

        <div style="text-align:center;">
            <a href="{free_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:15px;font-weight:bold;padding:16px 40px;border-radius:14px;
               text-decoration:none;">Open My Free Snapshot →</a>
        </div>
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
<body style="margin:0;padding:0;background:#fdfcfb;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fdfcfb;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:24px;overflow:hidden;max-width:600px;box-shadow:0 10px 30px rgba(0,0,0,0.03);">

      <tr><td style="background:#4f46e5;padding:48px 40px;text-align:center;">
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.2;font-weight:800;">
          What most coaches skip — and why it quietly kills their revenue
        </h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#18181b;line-height:1.8;margin:0 0 24px;">Hi {first},</p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          Most coaches launch with one offer. They attract someone who's curious but not ready to pay $2,000–$5,000 for their flagship. That person leaves. Nothing changes.
        </p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          The fix is a <strong>complete funnel</strong> — a path from "I just discovered you" to "I want your full program."
        </p>
        
        <div style="background:#f4f4f5;border:2px dashed #d4d4d8;border-radius:16px;padding:24px;margin:32px 0;text-align:center;">
          <p style="font-size:32px;margin:0 0 8px;">🔒</p>
          <p style="font-size:15px;font-weight:bold;color:#18181b;margin:0 0 4px;">All of this is in the Full Plan:</p>
          <ul style="font-size:14px;color:#71717a;margin:0;padding:0;list-style:none;">
            <li>Mid-Ticket + Flagship offers with revenue projections</li>
            <li>Year 1 & Year 2 revenue across every tier</li>
            <li>3 real named competitors in your niche</li>
          </ul>
        </div>

        <div style="text-align:center;">
            <a href="{payment_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:16px;font-weight:bold;padding:18px 44px;border-radius:16px;
               text-decoration:none;box-shadow:0 10px 20px rgba(79,70,229,0.2);">Get My Full Coaching Business Plan →</a>
            <p style="font-size:13px;color:#a1a1aa;margin:16px 0 0;">One-time payment. Instant download.</p>
        </div>
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
<body style="margin:0;padding:0;background:#fdfcfb;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fdfcfb;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:24px;overflow:hidden;max-width:600px;box-shadow:0 10px 30px rgba(0,0,0,0.03);">

      <tr><td style="background:#4f46e5;padding:48px 40px;text-align:center;">
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.2;font-weight:800;">
          {first}, here's what stood out in your quiz answers
        </h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">Hi {first},</p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
            Two things come up almost every time for coaches in your niche:
        </p>

        <div style="background:#fff7ed;border-left:6px solid #f97316;padding:24px;border-radius:8px;margin:0 0 20px;">
          <p style="font-size:15px;color:#7c2d12;margin:0;line-height:1.7;">
            <strong>1. "Nobody will pay that much for coaching."</strong><br>
            Almost never true. It's a positioning problem, not a pricing problem. Your full plan includes a personalised Fear Reframe with 3 concrete actions.
          </p>
        </div>

        <div style="background:#f5f3ff;border-left:6px solid #8b5cf6;padding:24px;border-radius:8px;margin:0 0 32px;">
          <p style="font-size:15px;color:#4c1d95;margin:0;line-height:1.7;">
            <strong>2. Marketing on the wrong channels.</strong><br>
            Your full marketing strategy maps 5 specific channels to your delivery style, audience size, and content medium.
          </p>
        </div>

        <div style="text-align:center;">
            <a href="{payment_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:16px;font-weight:bold;padding:18px 44px;border-radius:16px;
               text-decoration:none;">Unlock My Full Plan — $49</a>
        </div>
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
<body style="margin:0;padding:0;background:#fdfcfb;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#fdfcfb;padding:40px 0;">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:24px;overflow:hidden;max-width:600px;box-shadow:0 10px 30px rgba(0,0,0,0.03);">

      <tr><td style="background:#18181b;padding:48px 40px;text-align:center;">
        <p style="color:rgba(255,255,255,0.5);font-size:12px;margin:0 0 12px;text-transform:uppercase;letter-spacing:2px;font-weight:bold;">Final Email</p>
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.2;font-weight:800;">
          This is the last time I'll mention it, {first}
        </h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">Hi {first},</p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">This is the last email in this sequence. I hope your snapshot has already given you some massive clarity.</p>

        <div style="background:#f9fafb;border-radius:20px;padding:32px;margin:0 0 32px;border:1px solid #f1f1f4;">
          <p style="font-size:15px;font-weight:bold;color:#18181b;margin:0 0 20px;">What's waiting for you:</p>
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr><td style="padding:8px 0;font-size:14px;color:#3f3f46;">✅ Complete Funnel (all 4 tiers)</td></tr>
            <tr><td style="padding:8px 0;font-size:14px;color:#3f3f46;">✅ Revenue projections Year 1 + Year 2</td></tr>
            <tr><td style="padding:8px 0;font-size:14px;color:#3f3f46;">✅ 3 real competitors — with your edge over each</td></tr>
            <tr><td style="padding:8px 0;font-size:14px;color:#3f3f46;">✅ Personalised Fear Reframe + 3 actions</td></tr>
            <tr><td style="padding:8px 0;font-size:14px;color:#3f3f46;">✅ Full Marketing Strategy (5 channels + KPIs)</td></tr>
            <tr><td style="padding:8px 0;font-size:14px;color:#3f3f46;">✅ Full 90-Day Action Plan</td></tr>
            <tr><td style="padding:8px 0;font-size:14px;color:#3f3f46;">✅ Paid Acquisition Blueprint</td></tr>
          </table>
        </div>

        <div style="text-align:center;">
            <a href="{payment_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:18px;font-weight:bold;padding:18px 48px;border-radius:18px;
               text-decoration:none;box-shadow:0 10px 20px rgba(79,70,229,0.2);">Get My Full Plan for $49 →</a>
            <p style="font-size:13px;color:#a1a1aa;margin:20px 0 0;">Instant download. 14-day clarity guarantee.</p>
        </div>
      </td></tr>
      {_footer(unsubscribe_url)}
    </table>
  </td></tr>
</table>
</body>
</html>"""
