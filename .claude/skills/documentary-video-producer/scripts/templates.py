"""Reusable branded HTML/SVG graphic-card templates, parameterized.

Each function returns a full standalone HTML document string, sized to a
1920x1080 stage, ready for Playwright to load and record as a short animated
clip. Every template animates in (CSS keyframes) over roughly 0.5-1.5s and
then holds a static frame — safe to keep on screen for anywhere from 2s to
10+ seconds without looking frozen or looping.

Default palette here is charcoal/off-white/red (a restrained "documentary"
look), but every color is a parameter — re-skin for a different brand by
passing different `color`/`big_color`/`left_color` etc. arguments per call,
or by editing BASE_CSS's background and the module-level defaults if the
whole project uses one different brand consistently.

Hard rule this library exists to enforce: never show plain text on a flat
background. Every card has an icon, a chart, a comparison, a stamp, or an
illustrated character — something with visual structure, not just typography.
"""

BASE_CSS = """
*{box-sizing:border-box;}
html,body{margin:0;padding:0;width:1920px;height:1080px;background:#121212;overflow:hidden;
  font-family:Arial,"Liberation Sans",sans-serif;color:#F2EFE6;}
.stage{position:relative;width:1920px;height:1080px;}
.tag{font-family:"Liberation Mono",monospace;letter-spacing:2px;opacity:.75;}
@keyframes fadeUp{from{opacity:0;transform:translateY(24px);}to{opacity:1;transform:translateY(0);}}
@keyframes fade{to{opacity:1;}}
@keyframes grow{to{height:var(--h);}}
@keyframes drawline{to{stroke-dashoffset:0;}}
@keyframes slam{from{opacity:0;transform:scale(1.5) rotate(var(--r,4deg));}to{opacity:1;transform:scale(1) rotate(var(--r,4deg));}}
@keyframes countup{from{--num:0;}to{--num:var(--target);}}
"""

ICONS = {
  "person": '<circle cx="50" cy="30" r="16" fill="none" stroke="{c}" stroke-width="5"/><path d="M20 88 Q50 55 80 88" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
  "building": '<rect x="30" y="30" width="40" height="55" fill="none" stroke="{c}" stroke-width="5"/><rect x="40" y="42" width="8" height="8" fill="{c}"/><rect x="54" y="42" width="8" height="8" fill="{c}"/><rect x="40" y="58" width="8" height="8" fill="{c}"/><rect x="54" y="58" width="8" height="8" fill="{c}"/><rect x="43" y="72" width="14" height="13" fill="{c}"/>',
  "dollar": '<circle cx="50" cy="50" r="34" fill="none" stroke="{c}" stroke-width="5"/><text x="50" y="65" font-size="42" text-anchor="middle" fill="{c}" font-family="Arial" font-weight="700">$</text>',
  "briefcase": '<rect x="20" y="42" width="60" height="38" rx="6" fill="none" stroke="{c}" stroke-width="5"/><path d="M38 42 V32 Q38 24 50 24 Q62 24 62 32 V42" fill="none" stroke="{c}" stroke-width="5"/>',
  "magnifier": '<circle cx="42" cy="42" r="24" fill="none" stroke="{c}" stroke-width="5"/><line x1="60" y1="60" x2="82" y2="82" stroke="{c}" stroke-width="6" stroke-linecap="round"/>',
  "clock": '<circle cx="50" cy="50" r="34" fill="none" stroke="{c}" stroke-width="5"/><line x1="50" y1="50" x2="50" y2="28" stroke="{c}" stroke-width="4" stroke-linecap="round"/><line x1="50" y1="50" x2="66" y2="58" stroke="{c}" stroke-width="4" stroke-linecap="round"/>',
  "truck": '<rect x="14" y="45" width="45" height="28" fill="none" stroke="{c}" stroke-width="5"/><path d="M59 55 h18 l10 12 v6 h-28 z" fill="none" stroke="{c}" stroke-width="5"/><circle cx="30" cy="78" r="7" fill="none" stroke="{c}" stroke-width="4"/><circle cx="72" cy="78" r="7" fill="none" stroke="{c}" stroke-width="4"/><path d="M32 52 h10 M37 47 v10" stroke="{c}" stroke-width="4"/>',
  "scale": '<line x1="50" y1="20" x2="50" y2="75" stroke="{c}" stroke-width="5"/><line x1="22" y1="35" x2="78" y2="35" stroke="{c}" stroke-width="5"/><path d="M22 35 L12 60 A16 10 0 0 0 32 60 Z" fill="none" stroke="{c}" stroke-width="4"/><path d="M78 35 L68 60 A16 10 0 0 0 88 60 Z" fill="none" stroke="{c}" stroke-width="4"/><line x1="38" y1="82" x2="62" y2="82" stroke="{c}" stroke-width="5"/>',
  "warning": '<path d="M50 18 L88 82 H12 Z" fill="none" stroke="{c}" stroke-width="5" stroke-linejoin="round"/><line x1="50" y1="42" x2="50" y2="60" stroke="{c}" stroke-width="5" stroke-linecap="round"/><circle cx="50" cy="70" r="2.5" fill="{c}"/>',
  "document": '<rect x="28" y="16" width="44" height="68" rx="3" fill="none" stroke="{c}" stroke-width="5"/><line x1="38" y1="34" x2="62" y2="34" stroke="{c}" stroke-width="4"/><line x1="38" y1="46" x2="62" y2="46" stroke="{c}" stroke-width="4"/><line x1="38" y1="58" x2="54" y2="58" stroke="{c}" stroke-width="4"/>',
  "chart_down": '<polyline points="15,25 40,45 60,35 85,75" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="M75 75 H85 V65" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
  "chart_up": '<polyline points="15,75 40,55 60,65 85,25" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="M75 25 H85 V35" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>',
  "handshake": '<path d="M15 50 L38 50 L50 40 L62 50 L85 50" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><path d="M38 50 L30 62 M62 50 L70 62" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
  "gavel": '<rect x="18" y="60" width="46" height="14" rx="3" transform="rotate(-35 18 60)" fill="none" stroke="{c}" stroke-width="5"/><line x1="46" y1="46" x2="70" y2="70" stroke="{c}" stroke-width="6" stroke-linecap="round"/><line x1="20" y1="86" x2="80" y2="86" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
  "check": '<circle cx="50" cy="50" r="44" fill="none" stroke="{c}" stroke-width="4" opacity="0.35"/><path d="M28 52 L44 68 L74 34" fill="none" stroke="{c}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>',
  "cross": '<circle cx="50" cy="50" r="44" fill="none" stroke="{c}" stroke-width="4" opacity="0.35"/><line x1="32" y1="32" x2="68" y2="68" stroke="{c}" stroke-width="7" stroke-linecap="round"/><line x1="68" y1="32" x2="32" y2="68" stroke="{c}" stroke-width="7" stroke-linecap="round"/>',
  "calendar": '<rect x="18" y="24" width="64" height="58" rx="4" fill="none" stroke="{c}" stroke-width="5"/><line x1="18" y1="42" x2="82" y2="42" stroke="{c}" stroke-width="5"/><line x1="32" y1="16" x2="32" y2="30" stroke="{c}" stroke-width="5" stroke-linecap="round"/><line x1="68" y1="16" x2="68" y2="30" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
}

def icon_svg(name, color="#F2EFE6", size=150):
    path = ICONS[name].format(c=color)
    return f'<svg width="{size}" height="{size}" viewBox="0 0 100 100">{path}</svg>'


def wrap(body, extra_css=""):
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{BASE_CSS}{extra_css}</style></head><body><div class='stage'>{body}</div></body></html>"


def title_bar(text, delay=0.05):
    return (f'<div style="position:absolute;top:120px;left:0;width:100%;text-align:center;'
            f'font-size:42px;font-weight:700;opacity:0;animation:fade .4s ease-out {delay}s forwards;">{text}</div>')


def stat_reveal(title, big_text, big_color="#E63A2E", subtitle=None, tag=None, icon=None, icon_color=None):
    """Single big stat/phrase, centered, with a required icon, optional tag above and subtitle below.
    icon: name from ICONS. Always pass one — a bare text card is not an acceptable output."""
    parts = []
    if icon:
        ic = icon_color or big_color
        parts.append(f'<div style="position:absolute;top:150px;left:0;width:100%;text-align:center;opacity:0;'
                     f'animation:fadeUp .5s ease-out 0s forwards;">{icon_svg(icon, ic, 130)}</div>')
    if tag:
        parts.append(f'<div class="tag" style="position:absolute;top:340px;left:0;width:100%;text-align:center;font-size:30px;opacity:0;animation:fade .4s ease-out .1s forwards;">{tag}</div>')
    if title:
        parts.append(f'<div style="position:absolute;top:400px;left:0;width:100%;text-align:center;font-size:46px;font-weight:700;opacity:0;animation:fade .4s ease-out .25s forwards;">{title}</div>')
    parts.append(f'<div style="position:absolute;top:480px;left:0;width:100%;text-align:center;font-size:120px;font-weight:800;color:{big_color};opacity:0;'
                 f'animation:fadeUp .6s ease-out .55s forwards;">{big_text}</div>')
    if subtitle:
        parts.append(f'<div style="position:absolute;top:660px;left:0;width:100%;text-align:center;font-size:34px;opacity:0;animation:fade .5s ease-out 1.1s forwards;">{subtitle}</div>')
    return wrap("".join(parts))


def bar_chart(title, bars, gap_caption=None):
    """bars: list of (label, height_px 0-460, color)"""
    n = len(bars)
    gap = 160
    total_w = n*220 + (n-1)*gap
    left0 = (1920-total_w)//2
    items = []
    for i,(label,h,color) in enumerate(bars):
        left = left0 + i*(220+gap)
        delay = 0.3 + i*0.15
        items.append(f'''<div style="position:absolute;left:{left}px;bottom:230px;width:220px;height:0;background:{color};
            border-radius:6px 6px 0 0;animation:rise{i} 1.1s cubic-bezier(.2,.8,.2,1) {delay}s forwards;">
            <div style="position:absolute;bottom:-60px;left:0;width:100%;text-align:center;font-size:26px;font-weight:700;">{label}</div>
            </div>
            <style>@keyframes rise{i}{{to{{height:{h}px;}}}}</style>''')
    gap_html = ""
    if gap_caption:
        gap_html = f'<div style="position:absolute;left:0;top:440px;width:100%;text-align:center;color:#E63A2E;font-size:32px;font-weight:800;opacity:0;animation:fade .5s ease-out 1.5s forwards;">{gap_caption}</div>'
    return wrap(title_bar(title) + "".join(items) + gap_html)


def stamp_reveal(setup_text, stamp_text, icon_name="check", icon_color="#F2EFE6", rotate="-4deg"):
    icon = icon_svg(icon_name, icon_color, 180) if icon_name else ""
    setup = f'<div style="position:absolute;top:260px;left:0;width:100%;text-align:center;font-size:44px;font-weight:700;opacity:0;animation:fade .4s ease-out .05s forwards;">{setup_text}</div>' if setup_text else ""
    return wrap(f'''
    <div style="position:absolute;left:860px;top:420px;">{icon}</div>
    {setup}
    <div style="position:absolute;left:0;top:660px;width:100%;text-align:center;opacity:0;
      animation:slam .28s cubic-bezier(.2,1.6,.4,1) .55s forwards;--r:{rotate};">
      <div style="display:inline-block;border:6px solid #E63A2E;border-radius:10px;padding:14px 40px;
        color:#E63A2E;font-size:70px;font-weight:800;letter-spacing:2px;">{stamp_text}</div>
    </div>''')


def icon_flow(title, nodes):
    """nodes: list of (icon_name, label, color)"""
    n = len(nodes)
    gap = 110
    row = []
    for i,(icon,label,color) in enumerate(nodes):
        delay = 0.15 + i*0.4
        row.append(f'''<div style="display:flex;flex-direction:column;align-items:center;opacity:0;
          animation:fadeUp .6s ease-out {delay}s forwards;">
          {icon_svg(icon,color,150)}
          <div style="margin-top:22px;font-size:28px;font-weight:700;text-align:center;color:{color};">{label}</div>
          </div>''')
        if i < n-1:
            adelay = 0.15+i*0.4+0.35
            row.append(f'''<svg width="70" height="24" viewBox="0 0 100 30" style="opacity:0;animation:fade .4s ease-out {adelay}s forwards;">
              <line x1="5" y1="15" x2="85" y2="15" stroke="#F2EFE6" stroke-width="4"/>
              <path d="M70 4 L88 15 L70 26" fill="none" stroke="#F2EFE6" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg>''')
    body = (f'<div style="position:absolute;top:420px;left:0;width:100%;display:flex;align-items:center;'
            f'justify-content:center;gap:{gap}px;">{"".join(row)}</div>')
    return wrap(title_bar(title) + body if title else body)


def split_compare(left_tag, left_headline, left_icon, right_tag, right_headline, right_icon, left_color="#F2EFE6", right_color="#E63A2E"):
    css = """
    .side{position:absolute;top:0;width:50%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;}
    .left{left:0;animation:fade .5s ease-out .1s forwards;}
    .right{left:50%;animation:fade .5s ease-out .9s forwards;}
    .divider{position:absolute;top:0;left:50%;width:4px;height:0;background:#E63A2E;transform:translateX(-2px);animation:grow2 .5s ease-out .55s forwards;}
    @keyframes grow2{to{height:100%;}}
    """
    body = f'''
    <div class="side left">{icon_svg(left_icon,left_color,150)}
      <div class="tag" style="font-size:30px;margin-top:20px;color:{left_color};">{left_tag}</div>
      <div style="font-size:50px;font-weight:800;text-align:center;padding:0 60px;margin-top:8px;color:{left_color};">{left_headline}</div></div>
    <div class="side right">{icon_svg(right_icon,right_color,150)}
      <div class="tag" style="font-size:30px;margin-top:20px;color:{right_color};">{right_tag}</div>
      <div style="font-size:50px;font-weight:800;text-align:center;padding:0 60px;margin-top:8px;color:{right_color};">{right_headline}</div></div>
    <div class="divider"></div>'''
    return wrap(body, css)


def timeline_year(year, headline, subtext=None, icon_name=None):
    icon = icon_svg(icon_name, "#E63A2E", 120) if icon_name else ""
    sub = f'<div style="position:absolute;top:700px;left:0;width:100%;text-align:center;font-size:32px;opacity:0;animation:fade .5s ease-out .9s forwards;">{subtext}</div>' if subtext else ""
    return wrap(f'''
    <div style="position:absolute;top:260px;left:0;width:100%;text-align:center;">{icon}</div>
    <div style="position:absolute;top:420px;left:0;width:100%;text-align:center;font-family:'Liberation Mono',monospace;
      font-size:150px;font-weight:700;color:#E63A2E;opacity:0;animation:fadeUp .6s ease-out .15s forwards;">{year}</div>
    <div style="position:absolute;top:600px;left:0;width:100%;text-align:center;font-size:44px;font-weight:700;opacity:0;
      animation:fade .5s ease-out .5s forwards;">{headline}</div>
    {sub}''')


def line_chart(title, points, stamp_text=None, color="#E63A2E"):
    pts = " ".join(f"{x},{y}" for x,y in points)
    stamp = ""
    if stamp_text:
        stamp = f'''<div style="position:absolute;left:0;top:760px;width:100%;text-align:center;opacity:0;
          animation:slam .3s cubic-bezier(.2,1.6,.4,1) 2.1s forwards;--r:3deg;">
          <div style="display:inline-block;border:6px solid #E63A2E;border-radius:10px;padding:12px 36px;
            color:#E63A2E;font-size:60px;font-weight:800;letter-spacing:2px;">{stamp_text}</div></div>'''
    return wrap(f'''
    {title_bar(title)}
    <svg width="1920" height="600" style="position:absolute;top:220px;left:0;">
      <polyline points="{pts}" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"
        style="stroke-dasharray:1400;stroke-dashoffset:1400;animation:drawline 2s ease-in-out .2s forwards;"/>
    </svg>
    {stamp}''')


def route_pair(center_label, routes):
    """routes: list of (destination, distance_label) — shows center point with two routes branching out.
    Built for factual, restrained illustration of real events (e.g. distance to
    the nearest available help) without dramatizing them — see SKILL.md's note
    on sensitive-topic handling."""
    items = []
    n = len(routes)
    gap = 500
    left0 = (1920 - (n-1)*gap)//2
    for i,(dest,dist) in enumerate(routes):
        x = left0 + i*gap
        delay = 0.3 + i*0.5
        items.append(f'''
        <div style="position:absolute;left:{x-140}px;top:560px;width:280px;text-align:center;opacity:0;
          animation:fadeUp .6s ease-out {delay}s forwards;">
          {icon_svg("truck", "#E63A2E" if i==0 else "#F2EFE6", 90)}
          <div style="margin-top:14px;font-size:34px;font-weight:700;">{dest}</div>
          <div class="tag" style="font-size:26px;margin-top:6px;opacity:.8;">{dist}</div>
        </div>''')
    center = f'''<div style="position:absolute;left:0;top:380px;width:100%;text-align:center;font-size:36px;
      font-weight:700;opacity:0;animation:fade .4s ease-out .05s forwards;">{center_label}</div>'''
    return wrap(center + "".join(items))


def quiet_quote(text, tag=None):
    """A muted, minimal card for sensitive/human moments — no stat, no icon, just restrained typography.
    Text wraps naturally within a fixed side padding (thanks to box-sizing:border-box
    in BASE_CSS) — do not remove that rule, a long quote will overflow the frame
    without it."""
    tagline = (f'<div class="tag" style="position:absolute;top:420px;left:0;width:100%;text-align:center;'
               f'font-size:26px;opacity:0;animation:fade .5s ease-out .1s forwards;">{tag}</div>') if tag else ""
    return wrap(f'''
    {tagline}
    <div style="position:absolute;top:480px;left:0;width:100%;text-align:center;padding:0 220px;
      font-size:44px;font-weight:500;line-height:1.4;opacity:0;font-style:italic;color:#F2EFE6;
      animation:fadeUp .8s ease-out .35s forwards;">{text}</div>
    ''')


def kinetic_words(words, accent_indices=None, align="center"):
    """words: list of strings, each flies/scales in sequentially, fast-paced.
    accent_indices: set of indices to render in red and larger."""
    accent_indices = accent_indices or set()
    spans = []
    delay = 0.05
    for i, w in enumerate(words):
        is_accent = i in accent_indices
        color = "#E63A2E" if is_accent else "#F2EFE6"
        size = "96px" if is_accent else "64px"
        spans.append(f'''<span style="display:inline-block;color:{color};font-size:{size};font-weight:800;
          margin:0 14px;opacity:0;transform:translateY(30px) scale(.8);
          animation:kw .35s cubic-bezier(.2,1.4,.4,1) {delay:.2f}s forwards;">{w}</span>''')
        delay += 0.16
    css = "@keyframes kw{to{opacity:1;transform:translateY(0) scale(1);}}"
    return wrap(f'''<div style="position:absolute;top:0;left:0;width:100%;height:100%;display:flex;
      align-items:center;justify-content:{("center" if align=="center" else "flex-start")};
      flex-wrap:wrap;padding:0 160px;line-height:1.3;">{"".join(spans)}</div>''', css)


def line_draw_stat(label, value, points, color="#E63A2E"):
    """Small animated line chart with a big value readout beside it.
    points: list of (x, y) in SVG pixel space (700x300 viewport) — lower y is
    higher on screen, so a rising trend needs decreasing y as x increases."""
    pts = " ".join(f"{x},{y}" for x,y in points)
    return wrap(f'''
    <div style="position:absolute;left:180px;top:390px;">
      <div class="tag" style="font-size:28px;opacity:.8;margin-bottom:10px;">{label}</div>
      <div style="font-size:120px;font-weight:800;color:{color};">{value}</div>
    </div>
    <svg width="700" height="300" style="position:absolute;right:160px;top:390px;">
      <polyline points="{pts}" fill="none" stroke="{color}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"
        style="stroke-dasharray:900;stroke-dashoffset:900;animation:drawline 1.1s ease-out .1s forwards;"/>
    </svg>''')


def receipt_card(header, items, total_label, total_value):
    """items: list of (label, value) — looks like a printed itemized receipt.
    Good for any "here's what actually makes up this number" beat."""
    rows = []
    for i,(label,val) in enumerate(items):
        delay = 0.15 + i*0.13
        rows.append(f'''<div style="display:flex;justify-content:space-between;width:520px;
          font-family:'Liberation Mono',monospace;font-size:26px;padding:6px 0;opacity:0;
          border-bottom:1px dashed rgba(242,239,230,.25);
          animation:fadeUp .35s ease-out {delay:.2f}s forwards;"><span>{label}</span><span>{val}</span></div>''')
    total_delay = 0.15 + len(items)*0.13 + 0.15
    return wrap(f'''
    <div style="position:absolute;left:50%;top:150px;transform:translateX(-50%);width:560px;
      background:#1a1a1a;border:2px solid #2c2c2c;padding:36px 20px;">
      <div style="text-align:center;font-family:'Liberation Mono',monospace;font-size:30px;
        font-weight:700;margin-bottom:20px;letter-spacing:2px;">{header}</div>
      {"".join(rows)}
      <div style="display:flex;justify-content:space-between;width:520px;margin-top:16px;
        font-family:'Liberation Mono',monospace;font-size:34px;font-weight:800;color:#E63A2E;
        opacity:0;animation:fadeUp .4s ease-out {total_delay:.2f}s forwards;">
        <span>{total_label}</span><span>{total_value}</span></div>
    </div>''')


def glow_number(value, label, color="#E63A2E"):
    """A big number with pulsing expanding radial rings — use for the single
    biggest/most dramatic figure in a section, sparingly (it's a strong visual
    beat, not a default card)."""
    css = """
    @keyframes ring{0%{transform:scale(.6);opacity:.8;}100%{transform:scale(1.8);opacity:0;}}
    .ringel{position:absolute;left:50%;top:50%;width:260px;height:260px;margin:-130px 0 0 -130px;
      border-radius:50%;border:3px solid var(--rc);animation:ring 1.4s ease-out infinite;}
    """
    return wrap(f'''
    <div style="position:absolute;left:0;top:0;width:100%;height:100%;">
      <div class="ringel" style="--rc:{color};animation-delay:0s;"></div>
      <div class="ringel" style="--rc:{color};animation-delay:.45s;"></div>
      <div style="position:absolute;left:0;top:440px;width:100%;text-align:center;
        font-size:130px;font-weight:800;color:{color};opacity:0;
        animation:fadeUp .5s cubic-bezier(.2,1.4,.4,1) .2s forwards;">{value}</div>
      <div class="tag" style="position:absolute;left:0;top:640px;width:100%;text-align:center;
        font-size:28px;opacity:0;animation:fade .4s ease-out .5s forwards;">{label}</div>
    </div>''', css)


CHARACTER_POSES = {
  # Consistent line-art figure (head + torso + limbs), same stroke style as ICONS.
  "shrug": {
    "head": '<circle cx="0" cy="-70" r="26" fill="none" stroke="{c}" stroke-width="5"/><path d="M-10 -74 q10 8 20 0" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>',
    "body": '<path d="M0 -44 L0 30" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 -30 Q-46 -20 -50 20" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 -30 Q46 -20 50 20" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 30 L-26 92" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 30 L26 92" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
  },
  "overwhelmed": {
    "head": '<circle cx="0" cy="-70" r="26" fill="none" stroke="{c}" stroke-width="5"/><path d="M-10 -66 q10 -8 20 0" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>',
    "body": '<path d="M0 -44 L0 30" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 -34 Q-30 -60 -20 -96" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 -34 Q30 -60 20 -96" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 30 L-26 92" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 30 L26 92" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
  },
  "thinking": {
    "head": '<circle cx="0" cy="-70" r="26" fill="none" stroke="{c}" stroke-width="5"/><path d="M-8 -66 h6 M2 -66 h6" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>',
    "body": '<path d="M0 -44 L0 30" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 -30 Q-40 -10 -46 30" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 -20 Q26 -40 22 -64" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 30 L-26 92" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 30 L26 92" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
  },
  "confident": {
    "head": '<circle cx="0" cy="-70" r="26" fill="none" stroke="{c}" stroke-width="5"/><path d="M-9 -67 q9 6 18 0" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>',
    "body": '<path d="M0 -44 L0 30" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 -20 Q-30 -12 -34 10" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 -20 Q30 -12 34 10" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 30 L-26 92" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 30 L26 92" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
  },
  "collapsed": {
    "head": '<circle cx="18" cy="-30" r="24" fill="none" stroke="{c}" stroke-width="5"/><path d="M9 -27 q9 -6 18 0" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>',
    "body": '<path d="M18 -6 Q-10 10 -40 8" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M0 2 Q-20 -14 -14 -34" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M-40 8 L-70 8" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M-30 8 L-40 50" stroke="{c}" stroke-width="5" stroke-linecap="round"/>'
            '<path d="M-15 8 L-15 52" stroke="{c}" stroke-width="5" stroke-linecap="round"/>',
  },
}

def character_svg(pose, color="#F2EFE6", size=260):
    p = CHARACTER_POSES[pose]
    head = p["head"].format(c=color)
    body = p["body"].format(c=color)
    return f'<svg width="{size}" height="{size}" viewBox="-100 -110 200 220">{body}{head}</svg>'


def character_scene(pose, headline, tag=None, prop_icon=None, prop_color=None, color="#F2EFE6", bob=True):
    """A small illustrated scene: character + optional floating prop icon + caption.
    This is the 'almost a real picture' alternative to a bare stat card — use it
    for emotional/human beats (being overwhelmed, confident, thinking) rather
    than data points."""
    css = """
    @keyframes bob{0%,100%{transform:translateY(0);}50%{transform:translateY(-14px);}}
    @keyframes floatprop{0%{transform:translateY(0) rotate(-4deg);}50%{transform:translateY(-18px) rotate(4deg);}100%{transform:translateY(0) rotate(-4deg);}}
    .charwrap{animation:bob 2.4s ease-in-out infinite;}
    .propwrap{animation:floatprop 2.2s ease-in-out infinite;}
    """
    prop = ""
    if prop_icon:
        pc = prop_color or "#E63A2E"
        prop = f'<div class="propwrap" style="position:absolute;left:1160px;top:280px;opacity:0;animation:fade .4s ease-out .3s forwards, floatprop 2.2s ease-in-out .5s infinite;">{icon_svg(prop_icon, pc, 110)}</div>'
    tagline = (f'<div class="tag" style="position:absolute;top:640px;left:0;width:100%;text-align:center;'
               f'font-size:28px;opacity:0;animation:fade .4s ease-out .15s forwards;">{tag}</div>') if tag else ""
    return wrap(f'''
    <div class="charwrap" style="position:absolute;left:660px;top:340px;opacity:0;
      animation:fadeUp .4s ease-out 0s forwards, bob 2.4s ease-in-out .4s infinite;">{character_svg(pose, color)}</div>
    {prop}
    {tagline}
    <div style="position:absolute;top:calc(640px + {"48px" if tag else "0px"});left:0;width:100%;text-align:center;
      font-size:44px;font-weight:700;padding:0 260px;opacity:0;
      animation:fade .5s ease-out .35s forwards;">{headline}</div>
    ''', css)
