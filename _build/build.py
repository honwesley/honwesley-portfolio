"""Builds every page of the site from projects.py.

    python3 _build/build.py

Writes index.html, about.html, projects.html, experience.html and projects/<slug>.html
into the site root.

Needs only Python 3. If Pillow is installed (pip install pillow) it also writes WebP copies
of the images (full size and an 800 px version) and adds width/height to every <img> so the
page doesn't jump while images load. Without Pillow the pages still build, just with plain JPEGs.
"""
from html import escape as e
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from projects import PROJECTS, CATEGORIES  # noqa: E402

try:
    from PIL import Image
except ImportError:  # the site still builds without Pillow
    Image = None

CAT = dict(CATEGORIES)
SITE = "https://honwesley.github.io/honwesley-portfolio/"
EMAIL = "wesleyhon@gmail.com"
LINKEDIN = "https://linkedin.com/in/wesleyhon"
GITHUB = "https://github.com/honwesley"
RESUME = "assets/docs/Wesley_Hon_Resume.pdf"
DEVPOST = "https://devpost.com/software/cpr-trainer-a9olkm"
FEATURED = ["pendubot", "dc-microgrid-nmpc", "actuator-testbench", "baja-daq"]
DEFAULT_DESC = "Engineering portfolio of Wesley Hon: power electronics, controls, embedded hardware and PCB design."


# Version tags for the stylesheet and script, taken from their contents. Each build points the pages
# at e.g. main.js?v=3f9a1c2b, so a browser can never pair a new page with an old cached script.
def _ver(name):
    return hashlib.sha1((ROOT / name).read_bytes()).hexdigest()[:8]


CSS_V, JS_V = _ver("styles.css"), _ver("main.js")

# Images that are drawings, schematics or plots: shown whole on a paper sheet instead of cropped.
CONTAIN = ("schematic", "block", "buckboost", "signet-cad", "pendubot", "brewbird",
           "smv", "peec-simulink", "baja-power", "baja-controls", "ee141-circuit")
DARK = ("ee141", "ece131")  # dark MATLAB plots: shown whole on a dark well


def fit(img):
    if not img:
        return "cover"
    if any(k in img for k in CONTAIN):
        return "contain"
    if any(k in img for k in ("ozcan", "signet-hand")):
        return "board"
    if any(k in img for k in DARK):
        return "dark"
    return "cover"


def cats_text(p):
    return ", ".join(CAT[c] for c in p["cats"] if c != "course") or CAT["course"]


# ---------- images: WebP copies, sizes and dimensions ----------

_dims = {}


def _variants(rel):
    """For assets/img/x.jpg, make x.webp and x-800.webp (if wider than 800). Returns (w, h, srcset)."""
    if rel in _dims:
        return _dims[rel]
    src = ROOT / rel
    if Image is None or not src.exists():
        _dims[rel] = (None, None, None)
        return _dims[rel]
    with Image.open(src) as im:
        w, h = im.size
        full = src.with_suffix(".webp")
        small = src.with_name(src.stem + "-800.webp")
        if not full.exists() or full.stat().st_mtime < src.stat().st_mtime:
            im.convert("RGB").save(full, "WEBP", quality=80, method=6)
        parts = []
        if w > 800:
            if not small.exists() or small.stat().st_mtime < src.stat().st_mtime:
                im.convert("RGB").resize((800, round(h * 800 / w)), Image.LANCZOS).save(small, "WEBP", quality=80, method=6)
            parts.append(f"{small.name} 800w")
        parts.append(f"{full.name} {w}w")
    base = rel.rsplit("/", 1)[0] + "/"
    _dims[rel] = (w, h, ", ".join(base + p for p in parts))
    return _dims[rel]


def pic(rel, alt, root="", cls="", sizes="100vw", lazy=True, priority=False):
    """<picture> with a WebP srcset and the original JPEG as fallback. rel is relative to the site root."""
    w, h, srcset = _variants(rel)
    dim = f' width="{w}" height="{h}"' if w else ""
    load = ' loading="lazy" decoding="async"' if lazy else (' fetchpriority="high"' if priority else "")
    c = f' class="{cls}"' if cls else ""
    img = f'<img src="{root}{rel}" alt="{e(alt)}"{dim}{load}{c}>'
    if not srcset:
        return img
    srcset = ", ".join(root + s for s in srcset.split(", "))
    return f'<picture><source type="image/webp" srcset="{srcset}" sizes="{sizes}">{img}</picture>'


ARROW = '<svg class="arrow" viewBox="0 0 20 20" aria-hidden="true"><path d="M4 10h11M11 5l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'


# ---------- page shell ----------

def page(title, body, root="", desc=DEFAULT_DESC, current="", path="", image="assets/img/og-card.png", jsonld=None):
    nav = [("index.html", "Home", "home"), ("about.html", "About", "about"),
           ("projects.html", "Projects", "projects"), ("experience.html", "Experience", "experience")]
    links = "".join(
        f'<li><a href="{root}{h}"{" aria-current=\"page\"" if k == current else ""}>{t}</a></li>' for h, t, k in nav)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld)}</script>\n' if jsonld else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Wesley Hon">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}{image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{root}assets/apple-touch-icon.png">
<meta name="theme-color" content="#F4EFE4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#211D15" media="(prefers-color-scheme: dark)">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,300..500&family=Inter+Tight:wght@400..700&display=swap" rel="stylesheet">
<script>document.documentElement.classList.add("js");try{{var t=localStorage.getItem("theme");if(t!=="light"&&t!=="dark")t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
<link rel="stylesheet" href="{root}styles.css?v={CSS_V}">
{ld}</head>
<body class="pg-{current or 'project'}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="top-in">
    <a class="mark" href="{root}index.html" aria-label="Wesley Hon, home">Wesley Hon</a>
    <button type="button" class="theme-toggle" role="switch" aria-checked="false" aria-label="Dark mode">
      <svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>
      <svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/></svg>
      <span class="knob"></span>
    </button>
    <button type="button" class="menu-btn" aria-expanded="false" aria-controls="site-nav">
      <span class="menu-lines" aria-hidden="true"><i></i><i></i></span><span class="menu-word">Menu</span>
    </button>
    <nav id="site-nav" class="nav" aria-label="Site">
      <ul>
        {links}
        <li><a href="{GITHUB}" rel="noopener">GitHub</a></li>
        <li class="nav-resume"><a class="btn btn-sm" href="{root}{RESUME}">Resume</a></li>
      </ul>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="foot" aria-labelledby="foot-h">
  <div class="foot-in">
    <p class="label label-dark">Contact</p>
    <h2 id="foot-h">Let's talk hardware.</h2>
    <p class="foot-lede">Looking for internships and research in power electronics, controls and embedded systems.</p>
    <div class="actions">
      <a class="btn btn-primary" href="mailto:{EMAIL}">{EMAIL}</a>
      <a class="btn btn-on-dark" href="{LINKEDIN}" rel="noopener">LinkedIn</a>
      <a class="btn btn-on-dark" href="{GITHUB}" rel="noopener">GitHub</a>
      <a class="btn btn-on-dark" href="{root}{RESUME}">Resume (PDF)</a>
    </div>
  </div>
  <p class="fine">© 2026 Wesley Hon</p>
</footer>
<dialog id="lightbox" aria-label="Image viewer">
  <button class="lb-close" type="button">Close</button>
  <img alt="">
  <p class="lb-cap"></p>
</dialog>
<script src="{root}main.js?v={JS_V}"></script>
</body>
</html>
"""


# ---------- shared pieces ----------

def label(text, idx=None, dark=False):
    n = f'<span class="idx">{idx}</span>' if idx else ""
    return f'<p class="label{" label-dark" if dark else ""}">{n}{e(text)}</p>'


def card(p, root="", i=0, heading="h3", eager=False):
    when = p.get("when") or p.get("org", "")
    if p["cover"]:
        media = pic(f"assets/img/{p['cover']}", "", root, sizes="(min-width: 1100px) 400px, (min-width: 640px) 50vw, 100vw",
                    lazy=not eager)
    else:
        media = f'<span class="card-type">{e(p["title"])}</span>'
    return f"""<a class="card" href="{root}projects/{p['slug']}.html" data-cats="{' '.join(p['cats'])}" style="--i:{i}">
  <span class="card-media fit-{fit(p['cover'])}" style="view-transition-name: p-{p['slug']}">{media}</span>
  <span class="card-body">
    <span class="card-cat">{e(cats_text(p))}</span>
    <{heading} class="card-title">{e(p['title'])}</{heading}>
    <span class="card-short">{e(p['short'])}</span>
    <span class="card-meta"><span>{e(when)}</span>{ARROW}</span>
  </span>
</a>"""


SIM = """<figure class="rig" aria-labelledby="rig-cap">
  <div class="rig-stage">
    <canvas id="pendubot" role="img" aria-label="Simulated Pendubot. Drag link 1 to disturb it; the controller swings it back up and balances it."></canvas>
    <span class="grab-hint">Grab link 1 and shove it</span>
  </div>
  <div class="rig-bar">
    <div class="seg" role="group" aria-label="Balance controller">
      <button type="button" data-ctl="pid" aria-pressed="false">PID</button>
      <button type="button" data-ctl="lqr" aria-pressed="true">LQR</button>
      <button type="button" data-ctl="nmpc" aria-pressed="false">NMPC</button>
      <button type="button" data-ctl="fuzzy" aria-pressed="false">Fuzzy</button>
    </div>
    <p class="ctl-note" id="ctl-note">Full-state feedback from the Riccati solution on the linearized model.</p>
  </div>
  <div class="rig-bar rig-actions">
    <div class="seg" role="group" aria-label="Reset position">
      <button type="button" data-reset="up" aria-pressed="false">Reset upright</button>
      <button type="button" data-reset="down" aria-pressed="false">Reset hanging</button>
    </div>
    <button type="button" class="start-btn" data-start disabled>Start motor</button>
    <p class="rig-status" id="rig-status" aria-live="polite"></p>
  </div>
  <div class="scopes">
    <div class="scope">
      <p class="scope-h"><b>Joint angles</b><span><i class="sw ch1"></i>θ₁ link 1</span><span><i class="sw ch2"></i>θ₂ link 2</span><span class="scale">±180°, last 10 s</span></p>
      <canvas id="scope-a" aria-hidden="true"></canvas>
    </div>
    <div class="scope">
      <p class="scope-h"><b>Effort and energy</b><span><i class="sw ch1"></i>τ motor torque</span><span><i class="sw ch2"></i>E − E<sub>top</sub></span><span class="scale">±3 N·m, ±1.5 J</span></p>
      <canvas id="scope-b" aria-hidden="true"></canvas>
    </div>
  </div>
  <dl class="telemetry">
    <div class="t-mode"><dt>Mode</dt><dd id="t-mode" data-mode="swing">Swinging up</dd></div>
    <div><dt>θ₁</dt><dd id="t-q1">0.0°</dd></div>
    <div><dt>θ₂</dt><dd id="t-q2">0.0°</dd></div>
    <div><dt>τ, N·m</dt><dd id="t-u">0.00</dd></div>
    <div><dt>Compute, µs</dt><dd id="t-solve">0</dd></div>
    <div><dt>ω₁, rad/s</dt><dd id="t-w1">0.00</dd></div>
    <div><dt>ω₂, rad/s</dt><dd id="t-w2">0.00</dd></div>
    <div><dt>E − E<sub>top</sub>, J</dt><dd id="t-e">0.000</dd></div>
  </dl>
  <figcaption id="rig-cap">My Pendubot, simulated live at 1 kHz with two equal 11 in aluminum links and a 3 N·m motor limit. The motor drives the shoulder only; the elbow is a free, frictionless pin moved by nothing but gravity and link 1. When the arm falls, an energy-based swing-up brings it back and hands off to the controller you pick.</figcaption>
</figure>"""


def section(s):
    out = f'<section class="p-sec"><h2>{e(s["h"])}</h2>'
    if "p" in s:
        out += f'<p>{e(s["p"])}</p>'
    if "list" in s:
        out += "<ul class=\"did\">" + "".join(f"<li>{e(x)}</li>" for x in s["list"]) + "</ul>"
    if "ol" in s:
        out += "<ol class=\"steps\">" + "".join(f"<li><b>{e(a)}</b> {e(b)}</li>" for a, b in s["ol"]) + "</ol>"
    if "dl" in s:
        out += "<dl class=\"pairs\">" + "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in s["dl"]) + "</dl>"
    return out + "</section>"


WORK = [
    ("Power Electronics and Energy Conversion Lab", "Undergraduate researcher", "June 2026 to present"),
    ("Emergence of Communication Lab", "Undergraduate researcher", "October 2026 to present"),
    ("Ozcan Lab", "Undergraduate researcher", "November 2026 to present"),
    ("UCLA Bruin Racing SAE", "Electronics project lead", "April 2025 to present"),
]


# ---------- pages ----------

def build_home():
    feats = [next(p for p in PROJECTS if p["slug"] == s) for s in FEATURED]
    cards = "\n".join(card(p, "", i) for i, p in enumerate(feats))
    plate = [
        ("assets/img/testbench-model-2.jpg", "Drive motor and encoder on the eCVT actuator testbench", "eCVT actuator testbench", "projects/actuator-testbench.html"),
        ("assets/img/daq-board.jpg", "Assembled Baja controls and DAQ board", "Baja controls and DAQ board", "projects/baja-daq.html"),
        ("assets/img/ozcan-pcb.jpg", "Heater and thermistor control PCB, drawn from its KiCad layout", "Heater control PCB, from the KiCad layout", "projects/heater-control-pcb.html"),
    ]
    figs = "".join(
        f'<a class="plate-fig plate-{i + 1} fit-{fit(src)}" href="{href}">{pic(src, alt, "", sizes="(min-width: 960px) 30vw, 50vw", lazy=False, priority=(i == 0))}'
        f'<span class="plate-cap"><span class="idx">Fig. {i + 1}</span>{e(cap)}</span></a>'
        for i, (src, alt, cap, href) in enumerate(plate))
    work = "".join(f'<li><span class="w-org">{e(o)}</span><span class="w-role">{e(r)}</span><span class="w-when">{e(d)}</span></li>' for o, r, d in WORK)
    body = f"""
<section class="hero wrap" aria-labelledby="hero-h">
  <div class="hero-text">
    {label("Electrical engineering, UCLA")}
    <h1 id="hero-h">Wesley<br>Hon</h1>
    <p class="hero-tag">Power electronics, controls and embedded hardware</p>
    <p class="lede">Electrical engineering at UCLA. I design power converters, the controllers that keep them stable, and the boards they run on, then take them to the bench to see what breaks.</p>
    <div class="actions">
      <a class="btn btn-primary" href="projects.html">View projects</a>
      <a class="btn" href="{RESUME}">Resume</a>
      <a class="btn btn-ghost" href="mailto:{EMAIL}">Contact</a>
    </div>
    <dl class="facts">
      <div><dt>Focus</dt><dd>Power electronics, feedback control, autonomous systems, mechatronics</dd></div>
      <div><dt>Degree</dt><dd>BS expected 2028, MS expected 2029</dd></div>
      <div><dt>Now</dt><dd>Undergraduate researcher
        <ul class="labs">
          <li>Power Electronics and Energy Conversion Lab</li>
          <li>Emergence of Communication Lab</li>
          <li>Ozcan Lab</li>
        </ul></dd></div>
    </dl>
  </div>
  <div class="plate" aria-label="Hardware from my projects">
    {figs}
  </div>
</section>

<section class="band wrap" aria-labelledby="sel-h">
  <div class="band-head">
    <div>{label("Selected work", "01")}<h2 id="sel-h" class="section-h">Selected work</h2></div>
    <a class="more-link" href="projects.html">All {len(PROJECTS)} projects {ARROW}</a>
  </div>
  <div class="cards cards-feature">
{cards}
  </div>
</section>

<section class="showcase" aria-labelledby="sim-h">
  <div class="wrap showcase-in">
    <div class="showcase-text">
      {label("Interactive engineering", "02", dark=True)}
      <h2 id="sim-h" class="section-h">Explore the control system</h2>
      <p>This is my Pendubot, running live in your browser: two links, one motor at the shoulder, and a free elbow. Pick a controller and try to knock it over.</p>
      <ol class="how">
        <li>Choose PID, LQR, NMPC or fuzzy control.</li>
        <li>Grab link 1 and shove it, as hard as you like.</li>
        <li>Watch the scopes and telemetry as it recovers, or reset it upright or hanging and start the motor yourself.</li>
      </ol>
      <a class="more-link more-link-dark" href="projects/pendubot.html">Read the Pendubot write-up {ARROW}</a>
    </div>
    {SIM}
  </div>
</section>

<section class="band wrap" aria-labelledby="now-h">
  <div class="band-head">
    <div>{label("Experience", "03")}<h2 id="now-h" class="section-h">Where I work</h2></div>
    <a class="more-link" href="experience.html">Experience and skills {ARROW}</a>
  </div>
  <ul class="worklist">{work}</ul>
</section>

<section class="band band-last wrap" aria-labelledby="awards-h">
  <div class="band-head">
    <div>{label("Recognition", "04")}<h2 id="awards-h" class="section-h">Awards</h2></div>
  </div>
  <ul class="worklist">
    <li><span class="w-org">IdeaHacks 2026</span><span class="w-role">2nd place for <a href="{DEVPOST}" rel="noopener">CPR Trainer</a>, an ESP32 CPR trainer with real-time feedback</span><span class="w-when">2026</span></li>
  </ul>
</section>
"""
    person = {"@context": "https://schema.org", "@type": "Person", "name": "Wesley Hon", "url": SITE,
              "affiliation": "University of California, Los Angeles", "sameAs": [LINKEDIN, GITHUB]}
    (ROOT / "index.html").write_text(page("Wesley Hon — Power electronics, controls, mechatronics", body, "",
                                          current="home", path="", jsonld=person))


def build_projects():
    chips = '<button type="button" class="chip" aria-pressed="true" data-filter="all">All</button>' + "".join(
        f'<button type="button" class="chip" aria-pressed="false" data-filter="{k}">{e(v)}</button>' for k, v in CATEGORIES)
    cards = "\n".join(card(p, "", i, heading="h2", eager=i < 3) for i, p in enumerate(PROJECTS))
    body = f"""
<section class="wrap page-head" aria-labelledby="pj-h">
  {label("Index of work")}
  <h1 id="pj-h" class="page-h">Projects</h1>
  <p class="page-sub">{len(PROJECTS)} builds, from converter boards to robot arms. Filter by discipline, then open any project for the full write-up.</p>
  <div class="filter-row">
    <div class="chips" role="group" aria-label="Filter projects by discipline">{chips}</div>
    <p class="count" aria-live="polite"><span id="count">{len(PROJECTS)}</span> of {len(PROJECTS)} shown</p>
  </div>
</section>
<section class="wrap" aria-label="Project list">
  <div class="cards cards-all" id="tiles">
{cards}
  </div>
</section>
"""
    (ROOT / "projects.html").write_text(page("Projects — Wesley Hon", body, "", current="projects", path="projects.html",
                                             desc=f"{len(PROJECTS)} engineering projects by Wesley Hon: power electronics, controls, embedded systems, PCB design and mechanical builds."))


def build_project(idx):
    p = PROJECTS[idx]
    root = "../"
    prev_p = PROJECTS[idx - 1]
    next_p = PROJECTS[(idx + 1) % len(PROJECTS)]

    spec = []
    if p.get("when"):
        spec.append(("When", p["when"]))
    if p.get("org"):
        spec.append(("Where", p["org"]))
    if p.get("role"):
        spec.append(("Role", p["role"]))
    if p.get("status"):
        spec.append(("Status", p["status"]))
    spec_html = "".join(f"<div><dt>{a}</dt><dd>{e(b)}</dd></div>" for a, b in spec)
    areas = cats_text(p) if "course" not in p["cats"] else ", ".join(CAT[c] for c in p["cats"])
    tools = "".join(f"<li>{e(t)}</li>" for t in p.get("tools", []))
    docs = "".join(f'<li><a href="{root}assets/docs/{f}">{e(l)} <span>PDF</span></a></li>' for l, f in p.get("docs", []))

    if p["cover"]:
        cover_alt = next((a for f, a in p["images"] if f == p["cover"]), p["title"])
        hero = (f'<figure class="p-hero-fig"><div class="p-hero fit-{fit(p["cover"])}" style="view-transition-name: p-{p["slug"]}">'
                f'{pic("assets/img/" + p["cover"], cover_alt, root, sizes="(min-width: 1280px) 1200px, 100vw", lazy=False, priority=True)}</div>'
                f'<figcaption><span class="idx">Fig. 1</span>{e(cover_alt)}</figcaption></figure>')
    else:
        hero = ""

    # the cover is Fig. 1 above; the rest are numbered after it
    rest = [(f, a) for f, a in p["images"] if f != p["cover"]]
    first = 2 if p["cover"] else 1
    figures = ""
    if rest:
        figs = "".join(
            f'<figure class="fig fit-{fit(f)}"><button class="shot" type="button" data-full="{root}assets/img/{f}" aria-label="Enlarge figure {n}: {e(a)}">'
            f'{pic("assets/img/" + f, a, root, sizes="(min-width: 960px) 600px, 100vw")}</button>'
            f'<figcaption><span class="idx">Fig. {n}</span>{e(a)}</figcaption></figure>'
            for n, (f, a) in enumerate(rest, first))
        figures = f'<section class="figs" aria-labelledby="figs-h"><h2 id="figs-h" class="figs-h">Figures</h2><div class="fig-grid">{figs}</div></section>'

    video = ""
    if p.get("video"):
        video = (f'<section class="p-sec"><h2>On track</h2><video class="p-video" controls preload="none" playsinline '
                 f'poster="{root}assets/img/{p["poster"]}"><source src="{root}assets/video/{p["video"]}" type="video/mp4"></video></section>')

    sim = ""
    if p.get("sim"):
        sim = f"""<section class="showcase showcase-inline" aria-labelledby="try-h">
  <div class="showcase-in">
    <div class="showcase-text">
      {label("Interactive", dark=True)}
      <h2 id="try-h" class="section-h">Try it</h2>
      <p>The same dynamics, running in your browser. Pick a controller, then grab link 1 and shove it as hard as you like. The elbow is unactuated, so link 2 only reacts through the dynamics. Watch the telemetry as it swings back up and catches.</p>
    </div>
    {SIM}
  </div>
</section>"""
    impact = f'<p class="impact">{e(p["impact"])}</p>' if p.get("impact") else ""
    sections = "".join(section(s) for s in p["sections"])

    def nav_card(q, lab):
        img = pic("assets/img/" + q["cover"], "", root, sizes="160px") if q["cover"] else ""
        return (f'<a class="pn pn-{lab.lower()}" href="{q["slug"]}.html"><span class="pn-text"><span class="pn-label">{lab}</span>'
                f'<span class="pn-title">{e(q["title"])}</span></span><span class="pn-img fit-{fit(q["cover"])}">{img}</span></a>')

    body = f"""
<article class="proj-page">
  <div class="wrap">
    <p class="crumb"><a href="{root}projects.html"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16 10H5M9 5l-5 5 5 5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>All projects</a></p>
    <header class="p-head">
      <p class="label">{e(areas)}</p>
      <h1>{e(p['title'])}</h1>
      <p class="p-short">{e(p['short'])}</p>
      {f'<dl class="spec-strip">{spec_html}</dl>' if spec_html else ''}
    </header>
    {hero}
    <div class="p-grid">
      <div class="p-content">
        <p class="p-summary">{e(p['summary'])}</p>
        {impact}
        {sections}
        {video}
      </div>
      <aside class="p-aside" aria-label="Project details">
        {f'<h2>Tools</h2><ul class="toollist">{tools}</ul>' if tools else ''}
        {f'<h2>Documents</h2><ul class="doclist">{docs}</ul>' if docs else ''}
      </aside>
    </div>
  </div>
  {sim}
  <div class="wrap">
    {figures}
    <nav class="prevnext" aria-label="More projects">
      {nav_card(prev_p, "Previous")}
      {nav_card(next_p, "Next")}
    </nav>
  </div>
</article>
"""
    out = ROOT / "projects" / f"{p['slug']}.html"
    out.parent.mkdir(exist_ok=True)
    img = f"assets/img/{p['cover']}" if p["cover"] else "assets/img/og-card.png"
    out.write_text(page(f"{p['title']} — Wesley Hon", body, root, desc=p["short"], path=f"projects/{p['slug']}.html", image=img))


def build_experience():
    body = f"""
<section class="wrap page-head" aria-labelledby="exp-h">
  {label("Résumé, in detail")}
  <h1 id="exp-h" class="page-h">Experience</h1>
</section>
<section class="wrap exp-page">
  <ol class="timeline">
    <li>
      <p class="t-when">November 2026 to present</p>
      <div class="t-body">
        <h2>Undergraduate researcher</h2>
        <p class="t-org">Ozcan Lab, UCLA</p>
        <ul class="did">
          <li>Revising a Raspberry Pi HAT that drives three heaters and reads three thermistors: input protection and filtering, power routing fixes and connector changes from design review.</li>
        </ul>
        <p class="t-link"><a href="projects/heater-control-pcb.html">Read the project write-up</a></p>
      </div>
    </li>
    <li>
      <p class="t-when">October 2026 to present</p>
      <div class="t-body">
        <h2>Undergraduate researcher</h2>
        <p class="t-org">Emergence of Communication Lab, UCLA</p>
        <ul class="did">
          <li>Evaluating a smaller, lower-quiescent-current buck–boost regulator for the 3.3 V rail from a single Li-ion cell, with a characterization plan covering regulation, efficiency, load steps, ripple and thermals.</li>
        </ul>
        <p class="t-link"><a href="projects/buck-boost.html">Read the project write-up</a></p>
      </div>
    </li>
    <li>
      <p class="t-when">June 2026 to present</p>
      <div class="t-body">
        <h2>Undergraduate researcher</h2>
        <p class="t-org">Power Electronics and Energy Conversion Lab, UCLA</p>
        <ul class="did">
          <li>Designed DC–DC boost converter PCBs from schematic through layout, and modeled converter dynamics in MATLAB/Simulink and LTspice with state-space models, transfer functions, Bode plots and stability criteria.</li>
          <li>Developed a nonlinear model predictive controller for DC-bus voltage regulation under constant power loads, optimizing duty cycles and PWM for MOSFET switching. The bus recovers to reference in under 0.1 s after load disturbances.</li>
          <li>Evaluated transient response, stability and disturbance rejection under load steps. Did hardware bring-up and root-cause analysis with DSOs, differential probes and electronic loads to characterize gate ringing, conduction losses and VDS switching transients.</li>
        </ul>
        <p class="t-link"><a href="projects/dc-microgrid-nmpc.html">Read the project write-up</a></p>
      </div>
    </li>
    <li>
      <p class="t-when">April 2025 to present</p>
      <div class="t-body">
        <h2>Electronics project lead</h2>
        <p class="t-org">UCLA Bruin Racing SAE</p>
        <ul class="did">
          <li>Built an eCVT hardware-in-the-loop actuator testbench, with root-cause failure analysis to improve dynamic shifting for Baja SAE.</li>
          <li>Architected an ESP32-S3 controls and DAQ PCB: CAN transceivers, sensor-input and actuator-driver interfaces, custom UART firmware and a Raspberry Pi logging pipeline for real-time telemetry.</li>
          <li>Led the KiCad UI PCB team for Supermileage through board bring-up, component selection, power distribution and electrical interface reviews.</li>
        </ul>
        <p class="t-link"><a href="projects/actuator-testbench.html">Actuator testbench</a><a href="projects/baja-daq.html">DAQ board</a><a href="projects/supermileage-ui.html">Supermileage UI board</a></p>
      </div>
    </li>
  </ol>

  <div class="exp-grid">
    <section aria-labelledby="aw-h">
      <h2 id="aw-h" class="sub-h">Awards</h2>
      <ul class="awards">
        <li><b>2nd place, IdeaHacks 2026</b><span><a href="{DEVPOST}" rel="noopener">CPR Trainer</a>: a low-cost ESP32 CPR trainer with real-time feedback</span></li>
      </ul>
    </section>
    <section aria-labelledby="ed-h">
      <h2 id="ed-h" class="sub-h">Education</h2>
      <div class="edu">
        <h3>University of California, Los Angeles</h3>
        <p>Power electronics and controls, autonomous systems, mechatronics. BS expected 2028, MS expected 2029.</p>
        <p class="muted">Coursework: power electronics, principles of feedback control, dynamics, circuit theory, signal processing.</p>
      </div>
    </section>
    <section aria-labelledby="sk-h" class="exp-skills">
      <h2 id="sk-h" class="sub-h">Skills</h2>
      <div class="skills">
        <div><h3>Hardware and controls</h3><p>Altium Designer, KiCad, PCB layout, oscilloscopes and differential probes, CAN, UART, I2C, PWM, PID, LQR, NMPC</p></div>
        <div><h3>Software and simulation</h3><p>Embedded C/C++, MATLAB, Simulink, LTspice, SolidWorks, Onshape, OpenCV, PyTorch</p></div>
      </div>
    </section>
  </div>
  <p class="actions"><a class="btn btn-primary" href="{RESUME}">Download resume (PDF)</a></p>
</section>
"""
    (ROOT / "experience.html").write_text(page("Experience — Wesley Hon", body, "", current="experience", path="experience.html",
                                               desc="Wesley Hon's research and engineering experience: UCLA power electronics, communication and Ozcan labs, and Bruin Racing SAE."))


ABOUT = [
    ("Hiking", "My favorite hikes end somewhere high with a long view. Yosemite has given me a few of the best.", [
        ("half-dome.jpg", "Half Dome, Yosemite"),
        ("mist-trail-group.jpg", "Liberty Cap and Nevada Fall on a group hike in Yosemite"),
        ("ridge-photo.jpg", "Stopping to get the shot"),
        ("snow-sunset.jpg", "Sunset in the snow with friends"),
    ]),
    ("Viewpoints", "I'll go a long way for a good view, especially at sunset. Lately I've been bringing a drone along too.", [
        ("summit-sunset.jpg", "Sunset above the clouds"),
        ("drone-sunset.jpg", "Golden hour over the coast, from the drone"),
        ("beach-sunset.jpg", "Sunset on the coast"),
    ]),
    ("Sports", "In the pool or on a field. I swim, play flag football, and will try anything once, including skiing (results vary).", [
        ("swimming.jpg", "On the blocks at a swim meet"),
        ("flag-football.jpg", "Flag football at UCLA"),
        ("ski-wipeout.jpg", "Skiing, mid-wipeout"),
        ("flag-football-team.jpg", "Flag football team"),
        ("rose-bowl.jpg", "Cheering on UCLA football at the Rose Bowl"),
    ]),
    ("Off-road", "Where the fun and the engineering overlap: testing day with the Bruin Racing Baja car.", [
        ("baja-car.jpg", "The Baja car on the test track"),
    ]),
    ("Good company", "Most of the best views were better because of who I was with.", [
        ("friends-camp.jpg", "Friends"),
        ("volunteer-group.jpg", "With the team at an event"),
    ]),
]


def build_about():
    secs = []
    for n, (title, text, photos) in enumerate(ABOUT, 1):
        figs = "".join(
            f'<figure class="ab-fig"><button class="shot" type="button" data-full="assets/img/about/{f}" aria-label="Enlarge: {e(c)}">'
            f'{pic("assets/img/about/" + f, c, "", sizes="(min-width: 1000px) 400px, (min-width: 600px) 50vw, 100vw")}</button><figcaption>{e(c)}</figcaption></figure>'
            for f, c in photos)
        if title == "Off-road":
            figs = ('<figure class="ab-fig ab-video"><video controls preload="none" playsinline poster="assets/img/about/baja-drive-poster.jpg">'
                    '<source src="assets/video/baja-drive.mp4" type="video/mp4"></video><figcaption>Testing day, on video</figcaption></figure>') + figs
        slug = title.lower().replace(" ", "-")
        secs.append(f"""
  <section class="ab-sec" aria-labelledby="ab-{slug}">
    <div class="ab-head">
      <h2 id="ab-{slug}" class="section-h"><span class="idx">{n:02d}</span>{e(title)}</h2>
      <p>{e(text)}</p>
    </div>
    <div class="ab-grid">{figs}</div>
  </section>""")
    hero = pic("assets/img/about/drone-sunset-wide.jpg", "Golden-hour sunset over a coastline and forested hills, shot from a drone",
               "", sizes="100vw", lazy=False, priority=True)
    body = f"""
<article class="about-page">
  <div class="wrap page-head">
    {label("Outside the lab")}
    <h1 class="page-h">About</h1>
    <p class="ab-lede">Outside the lab I'm usually outdoors: on a trail, in the pool or on a field, or somewhere high up waiting for the sun to go down.</p>
  </div>
  <figure class="ab-hero">{hero}</figure>
  <div class="wrap">
    {"".join(secs)}
    <p class="ab-foot">Looking for the engineering? <a href="projects.html">See my projects</a> or <a href="experience.html">my experience</a>.</p>
  </div>
</article>
"""
    (ROOT / "about.html").write_text(page("About — Wesley Hon", body, "", current="about", path="about.html",
                                          desc="Wesley Hon outside of engineering: hiking, viewpoints and sports.",
                                          image="assets/img/about/drone-sunset-wide.jpg"))


if __name__ == "__main__":
    build_home()
    build_projects()
    for i in range(len(PROJECTS)):
        build_project(i)
    build_experience()
    build_about()
    print(f"Built home, about, projects, experience and {len(PROJECTS)} project pages.")
