"""
emails.py — 5-email drip sequence HTML templates.
Redesigned with luxury branding consistent with the quiz and landing page.
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
        <p style="color:rgba(255,255,255,0.7);font-size:12px;margin:0 0 12px;text-transform:uppercase;letter-spacing:2px;font-weight:bold;">Your Free Blueprint</p>
        <h1 style="color:#ffffff;font-size:28px;margin:0;line-height:1.2;font-weight:800;">Your Coaching Business Snapshot 🎯</h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#18181b;line-height:1.8;margin:0 0 24px;">Hi {first},</p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
            I've analyzed your responses and built a custom strategy designed for your specific coaching niche. This isn't just a generic document—it's a reflection of your unique expertise.
        </p>
        
        <p style="font-size:14px;color:#71717a;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:0 0 16px;">What's inside your free report:</p>
        <div style="background:#f9fafb;border-radius:16px;padding:24px;margin:0 0 32px;">
            <table width="100%" cellpadding="0" cellspacing="4">
              <tr><td style="color:#4f46e5;font-size:18px;width:24px;">✓</td><td style="font-size:15px;color:#3f3f46;"><strong>Your one-sentence offer</strong> refined for 2026</td></tr>
              <tr><td style="color:#4f46e5;font-size:18px;">✓</td><td style="font-size:15px;color:#3f3f46;"><strong>Complete offer layers</strong> (Pain, Outcome, Mechanism)</td></tr>
              <tr><td style="color:#4f46e5;font-size:18px;">✓</td><td style="font-size:15px;color:#3f3f46;"><strong>Funnel Top-Tier</strong> (Lead magnet + low-ticket)</td></tr>
              <tr><td style="color:#4f46e5;font-size:18px;">✓</td><td style="font-size:15px;color:#3f3f46;"><strong>First 30 days</strong> of your action plan</td></tr>
            </table>
        </div>

        <table width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0 32px;">
          <tr><td align="center">
            <a href="{free_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:16px;font-weight:bold;padding:18px 44px;border-radius:16px;
               text-decoration:none;box-shadow:0 10px 20px rgba(79,70,229,0.2);">⬇ Download Your Snapshot</a>
          </td></tr>
        </table>

        <div style="background:#fff7ed;border:1px solid #fed7aa;padding:24px;border-radius:16px;margin:32px 0 0;">
          <p style="font-size:15px;color:#7c2d12;margin:0 0 12px;font-weight:bold;">Ready for the full strategy?</p>
          <p style="font-size:14px;color:#9a3412;margin:0 0 16px;line-height:1.6;">
            Unlock Revenue Projections, Competitor Mapping, Fear Reframe, and the complete 90-Day Scaling Plan.
          </p>
          <a href="{payment_url}" style="font-size:14px;color:#4f46e5;font-weight:bold;text-decoration:none;">
            Unlock the Full $49 Plan →
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
          The #1 Secret of High-Ticket Coaches
        </h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#18181b;line-height:1.8;margin:0 0 24px;">Hi {first},</p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          The coaches who struggle say things like "I help people reach their potential."
        </p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          The coaches who fill their calendar say something so specific that the right person thinks: 
          <em>"That's exactly me. How do I work with this person?"</em>
        </p>
        <p style="font-size:16px;color:#18181b;line-height:1.8;margin:0 0 32px;font-weight:bold;">
          The difference isn't skill. It's positioning.
        </p>

        <div style="text-align:center;">
            <a href="{free_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:15px;font-weight:bold;padding:16px 40px;border-radius:14px;
               text-decoration:none;">Refine My Positioning →</a>
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
          The "Silent Killer" of Coaching Revenue
        </h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#18181b;line-height:1.8;margin:0 0 24px;">Hi {first},</p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          Most coaches launch with one offer. They attract someone who's curious but not ready to pay $5,000. That person leaves. Nothing changes.
        </p>
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          The fix is a <strong>complete funnel</strong>—a path from "I just discovered you" to flagship client.
        </p>
        
        <div style="background:#f4f4f5;border:2px dashed #d4d4d8;border-radius:20px;padding:32px;margin:32px 0;text-align:center;">
          <p style="font-size:32px;margin:0 0 12px;">🔒</p>
          <p style="font-size:15px;font-weight:bold;color:#18181b;margin:0 0 8px;">Waiting in your Full Plan:</p>
          <p style="font-size:14px;color:#71717a;margin:0;">Mid-Ticket Revenue + Competitor Mapping + 90-Day Scaling</p>
        </div>

        <div style="text-align:center;">
            <a href="{payment_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:16px;font-weight:bold;padding:18px 44px;border-radius:16px;
               text-decoration:none;box-shadow:0 10px 20px rgba(79,70,229,0.2);">Unlock My Complete Funnel →</a>
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
          Looking at your results, {first}...
        </h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
          Two things usually hold back coaches in your niche:
        </p>

        <div style="background:#fff7ed;border-left:6px solid #f97316;padding:24px;border-radius:8px;margin:0 0 20px;">
          <p style="font-size:15px;color:#7c2d12;margin:0;line-height:1.7;">
            <strong>1. The "Imposter" Price Trap</strong><br>
            Thinking people won't pay high-ticket. It's a positioning problem, not a pricing one. Your plan includes a Fear Reframe to fix this.
          </p>
        </div>

        <div style="background:#f5f3ff;border-left:6px solid #8b5cf6;padding:24px;border-radius:8px;margin:0 0 32px;">
          <p style="font-size:15px;color:#4c1d95;margin:0;line-height:1.7;">
            <strong>2. Channel Overload</strong><br>
            Your plan maps 5 specific channels to YOUR delivery style so you stop wasting time.
          </p>
        </div>

        <div style="text-align:center;">
            <a href="{payment_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:16px;font-weight:bold;padding:18px 44px;border-radius:16px;
               text-decoration:none;">See Your Growth Strategy →</a>
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
        <p style="color:rgba(255,255,255,0.5);font-size:12px;margin:0 0 12px;text-transform:uppercase;letter-spacing:2px;font-weight:bold;">Final Invitation</p>
        <h1 style="color:#ffffff;font-size:26px;margin:0;line-height:1.2;font-weight:800;">
          This is the last time I'll mention it, {first}
        </h1>
      </td></tr>

      <tr><td style="padding:48px 40px;">
        <p style="font-size:16px;color:#3f3f46;line-height:1.8;margin:0 0 24px;">
            This is the final email in this sequence. I hope your snapshot has already given you some massive clarity.
        </p>

        <div style="background:#f9fafb;border-radius:20px;padding:32px;margin:0 0 32px;border:1px solid #f1f1f4;">
          <p style="font-size:15px;font-weight:bold;color:#18181b;margin:0 0 20px;">Ready to finalize your 2026 plan?</p>
          <table cellpadding="0" cellspacing="0" width="100%">
            <tr><td style="padding:10px 0;font-size:14px;color:#3f3f46;">🚀 <strong>Full Funnel</strong> (Mid-Ticket + Flagship)</td></tr>
            <tr><td style="padding:10px 0;font-size:14px;color:#3f3f46;">📊 <strong>Year 1 & 2</strong> Revenue Projections</td></tr>
            <tr><td style="padding:10px 0;font-size:14px;color:#3f3f46;">🔍 <strong>Competitor Intelligence</strong> + Your Edge</td></tr>
            <tr><td style="padding:10px 0;font-size:14px;color:#3f3f46;">🧠 <strong>Fear Reframe</strong> + Concrete Actions</td></tr>
            <tr><td style="padding:10px 0;font-size:14px;color:#3f3f46;">📆 <strong>Full 90-Day Action Plan</strong></td></tr>
          </table>
        </div>

        <div style="text-align:center;">
            <a href="{payment_url}" style="display:inline-block;background:#4f46e5;color:#ffffff;
               font-size:18px;font-weight:bold;padding:20px 48px;border-radius:18px;
               text-decoration:none;box-shadow:0 10px 20px rgba(79,70,229,0.2);">Unlock Everything for $49 →</a>
            <p style="font-size:13px;color:#a1a1aa;margin:20px 0 0;">One-time payment. Instant delivery.</p>
        </div>
      </td></tr>
      {_footer(unsubscribe_url)}
    </table>
  </td></tr>
</table>
</body>
</html>"""
