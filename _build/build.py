"""Builds every page of the site from projects.py.

    python3 _build/build.py

Writes index.html, projects.html, experience.html and projects/<slug>.html
into the site root. Plain Python 3, no packages needed.
"""
from html import escape as e
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from projects import PROJECTS, CATEGORIES  # noqa: E402

CAT = dict(CATEGORIES)
SITE = "https://honwesley.github.io/honwesley-portfolio/"
EMAIL = "wesleyhon@gmail.com"
LINKEDIN = "https://linkedin.com/in/wesleyhon"
GITHUB = "https://github.com/honwesley"
FEATURED = ["pendubot", "dc-microgrid-nmpc", "actuator-testbench"]

# Images that are drawings, schematics or plots: shown whole on white instead of cropped.
CONTAIN = ("schematic", "block", "buckboost", "signet-cad", "pendubot", "brewbird",
           "smv", "peec-simulink", "baja-power", "baja-controls", "ee141-circuit")
# Dark MATLAB plots: shown whole on navy.
DARK = ("ee141", "ece131")


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


def page(title, body, root="", desc="Engineering portfolio of Wesley Hon: power electronics, controls, embedded hardware and PCB design.", current="", path=""):
    nav = [("index.html", "Home", "home"), ("projects.html", "Projects", "projects"), ("experience.html", "Experience", "experience")]
    links = "".join(
        f'<a href="{root}{h}"{" aria-current=\"page\"" if k == current else ""}>{t}</a>' for h, t, k in nav)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{SITE}assets/img/peec-pcb-3d.jpg">
<link rel="canonical" href="{SITE}{path}">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=Inter+Tight:wght@300..800&display=swap" rel="stylesheet">
<meta name="theme-color" content="#F4EFE4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#211D15" media="(prefers-color-scheme: dark)">
<script>try{{var t=localStorage.getItem("theme");if(t!=="light"&&t!=="dark")t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
<link rel="stylesheet" href="{root}styles.css">
</head>
<body class="pg-{current or 'project'}">
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand">
    <a class="mark" href="{root}index.html">Wesley Hon</a>
    <button type="button" class="theme-toggle" role="switch" aria-checked="false" aria-label="Dark mode">
      <svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>
      <svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/></svg>
      <span class="knob"></span>
    </button>
  </div>
  <nav aria-label="Site">
    {links}
    <a href="{GITHUB}" rel="noopener">GitHub</a>
    <a class="nav-cta" href="{root}assets/docs/Wesley_Hon_Resume.pdf">Resume</a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <h2>Let's talk hardware.</h2>
  <p>Looking for internships and research in power electronics, controls and embedded systems.</p>
  <div class="actions">
    <a class="btn primary" href="mailto:{EMAIL}">{EMAIL}</a>
    <a class="btn" href="{LINKEDIN}" rel="noopener">LinkedIn</a>
    <a class="btn" href="{GITHUB}" rel="noopener">GitHub</a>
    <a class="btn" href="{root}assets/docs/Wesley_Hon_Resume.pdf">Resume (PDF)</a>
  </div>
  <p class="fine">© 2026 Wesley Hon</p>
</footer>
<dialog id="lightbox" aria-label="Image viewer">
  <button class="lb-close" type="button">Close</button>
  <img alt="">
  <p class="lb-cap"></p>
</dialog>
<script src="{root}main.js"></script>
</body>
</html>
"""


# ---------- shared pieces ----------

def tile(p, root="", i=0, size=None):
    size = size or p["size"]
    imgs = ([p["cover"]] if p["cover"] else []) + [f for f, _ in p["images"] if f != p["cover"]]
    imgs = imgs[:4]
    if imgs:
        layers = "".join(
            f'<img src="{root}assets/img/{f}" alt="" class="fit-{fit(f)}{" on" if k == 0 else ""}" loading="{"eager" if i < 3 else "lazy"}">'
            for k, f in enumerate(imgs))
        ticks = '<span class="ticks" aria-hidden="true">' + "<i></i>" * len(imgs) + "</span>" if len(imgs) > 1 else ""
        media = f'<span class="tile-media" style="view-transition-name: p-{p["slug"]}">{layers}{ticks}</span>'
    else:
        media = f'<span class="tile-media tile-type" style="view-transition-name: p-{p["slug"]}"><span>{e(p["title"])}</span></span>'
    when = p.get("when") or p.get("org", "")
    return f"""<a class="tile tile-{size}" href="{root}projects/{p['slug']}.html" data-cats="{' '.join(p['cats'])}" style="--i:{i}">
  {media}
  <span class="tile-info">
    <span class="tile-title">{e(p['title'])}</span>
    <span class="tile-short">{e(p['short'])}</span>
    <span class="tile-meta"><span>{e(when)}</span><span>{e(cats_text(p))}</span></span>
  </span>
</a>"""


SIM = """<figure class="rig" aria-labelledby="rig-cap">
  <div class="rig-stage">
    <canvas id="pendubot" role="img" aria-label="Simulated Pendubot. Drag the arm to disturb it; the controller swings it back up and balances it."></canvas>
    <span class="grab-hint">Grab the arm and throw it</span>
  </div>
  <div class="rig-bar">
    <div class="ctl-pick" role="group" aria-label="Balance controller">
      <button type="button" data-ctl="pid" aria-pressed="false">PID</button>
      <button type="button" data-ctl="lqr" aria-pressed="true">LQR</button>
      <button type="button" data-ctl="nmpc" aria-pressed="false">NMPC</button>
      <button type="button" data-ctl="fuzzy" aria-pressed="false">Fuzzy</button>
    </div>
    <p class="ctl-note" id="ctl-note">Full-state feedback from the Riccati solution on the linearized model.</p>
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
  <figcaption id="rig-cap">My Pendubot, simulated live at 1 kHz with the real link geometry and a 3 N·m motor limit. The motor never switches off: when the arm falls, an energy-based swing-up brings it back and hands off to the controller you pick.</figcaption>
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


# ---------- pages ----------

def build_home():
    feats = [next(p for p in PROJECTS if p["slug"] == s) for s in FEATURED]
    tiles = "\n".join(tile(p, "", i, "l" if i else "xl") for i, p in enumerate(feats))
    body = f"""
<section class="hero wrap">
  <div class="hero-text">
    <h1>Wesley<br>Hon</h1>
    <p class="lede">Electrical engineering at UCLA. I design power converters, the controllers that keep them stable, and the boards they run on, then take them to the bench to see what breaks.</p>
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
    <div class="actions">
      <a class="btn primary" href="projects.html">See my projects</a>
      <a class="btn" href="assets/docs/Wesley_Hon_Resume.pdf">Resume</a>
      <a class="btn" href="mailto:{EMAIL}">Email me</a>
    </div>
  </div>
  {SIM}
</section>

<section class="wrap band" aria-labelledby="sel-h">
  <div class="band-head">
    <h2 id="sel-h" class="section-h">Selected work</h2>
    <a class="more-link" href="projects.html">All {len(PROJECTS)} projects</a>
  </div>
  <div class="tiles tiles-home">
{tiles}
  </div>
</section>

<section class="wrap band" aria-labelledby="now-h">
  <div class="band-head">
    <h2 id="now-h" class="section-h">Where I work</h2>
    <a class="more-link" href="experience.html">Experience and skills</a>
  </div>
  <ul class="where">
    <li><b>Power Electronics and Energy Conversion Lab</b><span>Undergraduate researcher, June 2026 to present</span></li>
    <li><b>Emergence of Communication Lab</b><span>Undergraduate researcher, October 2026 to present</span></li>
    <li><b>Ozcan Lab</b><span>Undergraduate researcher, November 2026 to present</span></li>
    <li><b>UCLA Bruin Racing SAE</b><span>Electronics project lead, April 2025 to present</span></li>
  </ul>
</section>

<section class="wrap band" aria-labelledby="awards-h">
  <div class="band-head">
    <h2 id="awards-h" class="section-h">Awards</h2>
  </div>
  <ul class="where">
    <li><b>IdeaHacks 2026</b><span>2nd place, hardware hackathon</span></li>
  </ul>
</section>
"""
    (ROOT / "index.html").write_text(page("Wesley Hon — Power electronics, controls, mechatronics", body, "", current="home", path=""))


def build_projects():
    chips = '<button type="button" class="chip" aria-pressed="true" data-filter="all">All</button>' + "".join(
        f'<button type="button" class="chip" aria-pressed="false" data-filter="{k}">{e(v)}</button>' for k, v in CATEGORIES)
    tiles = "\n".join(tile(p, "", i) for i, p in enumerate(PROJECTS))
    body = f"""
<section class="wrap pj-head">
  <h1 class="page-h">Projects</h1>
  <p class="page-sub">{len(PROJECTS)} builds, from converter boards to robot arms. Hover a project to flip through it, then click in for the full write-up.</p>
  <div class="chips" role="group" aria-label="Filter projects">{chips}</div>
  <p class="count" aria-live="polite"><span id="count">{len(PROJECTS)}</span> shown</p>
</section>
<section class="wrap">
  <div class="tiles tiles-all" id="tiles">
{tiles}
  </div>
</section>
"""
    (ROOT / "projects.html").write_text(page("Projects — Wesley Hon", body, "", current="projects", path="projects.html"))


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
    spec.append(("Areas", cats_text(p) if "course" not in p["cats"] else ", ".join(CAT[c] for c in p["cats"])))
    spec_html = "".join(f"<div><dt>{a}</dt><dd>{e(b)}</dd></div>" for a, b in spec)
    tools = "".join(f"<li>{e(t)}</li>" for t in p.get("tools", []))
    docs = "".join(f'<li><a href="{root}assets/docs/{f}">{e(l)} <span>(PDF)</span></a></li>' for l, f in p.get("docs", []))

    if p["cover"]:
        cover_alt = next((a for f, a in p["images"] if f == p["cover"]), p["title"])
        hero = f'<figure class="p-hero fit-{fit(p["cover"])}" style="view-transition-name: p-{p["slug"]}"><img src="{root}assets/img/{p["cover"]}" alt="{e(cover_alt)}"></figure>'
    else:
        hero = f'<figure class="p-hero tile-type" style="view-transition-name: p-{p["slug"]}"><span>{e(p["title"])}</span></figure>'

    gallery = ""
    if len(p["images"]) > 1 or (p["images"] and p["images"][0][0] != p["cover"]):
        gallery = '<section class="p-sec"><h2>Gallery</h2><div class="p-gallery">' + "".join(
            f'<button class="shot fit-{fit(f)}" data-full="{root}assets/img/{f}"><img src="{root}assets/img/{f}" alt="{e(a)}" loading="lazy"></button>'
            for f, a in p["images"]) + "</div></section>"

    video = ""
    if p.get("video"):
        video = f'<section class="p-sec"><h2>On track</h2><video class="p-video" controls preload="none" playsinline poster="{root}assets/img/{p["poster"]}"><source src="{root}assets/video/{p["video"]}" type="video/mp4"></video></section>'

    sim = f'<section class="p-sec"><h2>Try it</h2><p>The same dynamics, running in your browser. Pick a controller, then grab the arm and throw it as hard as you like. Watch the telemetry as it swings back up and catches.</p>{SIM}</section>' if p.get("sim") else ""
    impact = f'<p class="impact">{e(p["impact"])}</p>' if p.get("impact") else ""
    sections = "".join(section(s) for s in p["sections"])

    def nav_card(q, label):
        img = f'<img src="{root}assets/img/{q["cover"]}" alt="" class="fit-{fit(q["cover"])}" loading="lazy">' if q["cover"] else ""
        return f'<a class="pn" href="{q["slug"]}.html"><span class="pn-label">{label}</span><span class="pn-title">{e(q["title"])}</span>{img}</a>'

    body = f"""
<article class="wrap proj-page">
  <p class="crumb"><a href="{root}projects.html">All projects</a></p>
  <header class="p-head">
    <h1>{e(p['title'])}</h1>
    <p class="p-short">{e(p['short'])}</p>
  </header>
  {hero}
  <div class="p-grid">
    <aside class="spec">
      <dl>{spec_html}</dl>
      {f'<h2>Tools</h2><ul class="toollist">{tools}</ul>' if tools else ''}
      {f'<h2>Documents</h2><ul class="doclist">{docs}</ul>' if docs else ''}
    </aside>
    <div class="p-content">
      <p class="p-summary">{e(p['summary'])}</p>
      {impact}
      {sections}
      {sim}
      {video}
      {gallery}
    </div>
  </div>
  <nav class="prevnext" aria-label="More projects">
    {nav_card(prev_p, "Previous")}
    {nav_card(next_p, "Next")}
  </nav>
</article>
"""
    out = ROOT / "projects" / f"{p['slug']}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page(f"{p['title']} — Wesley Hon", body, root, desc=p["short"], path=f"projects/{p['slug']}.html"))


def build_experience():
    body = f"""
<section class="wrap exp-page">
  <h1 class="page-h">Experience</h1>
  <ol class="timeline">
    <li>
      <p class="t-when">November 2026 to present</p>
      <h2>Undergraduate researcher</h2>
      <p class="t-org">Ozcan Lab, UCLA</p>
      <ul class="did">
        <li>Revising a Raspberry Pi HAT that drives three heaters and reads three thermistors: input protection and filtering, power routing fixes and connector changes from design review.</li>
      </ul>
      <p class="t-link"><a href="projects/heater-control-pcb.html">Read the project write-up</a></p>
    </li>
    <li>
      <p class="t-when">October 2026 to present</p>
      <h2>Undergraduate researcher</h2>
      <p class="t-org">Emergence of Communication Lab, UCLA</p>
      <ul class="did">
        <li>Evaluating a smaller, lower-quiescent-current buck–boost regulator for the 3.3 V rail from a single Li-ion cell, with a characterization plan covering regulation, efficiency, load steps, ripple and thermals.</li>
      </ul>
      <p class="t-link"><a href="projects/buck-boost.html">Read the project write-up</a></p>
    </li>
    <li>
      <p class="t-when">June 2026 to present</p>
      <h2>Undergraduate researcher</h2>
      <p class="t-org">Power Electronics and Energy Conversion Lab, UCLA</p>
      <ul class="did">
        <li>Designed DC–DC boost converter PCBs from schematic through layout, and modeled converter dynamics in MATLAB/Simulink and LTspice with state-space models, transfer functions, Bode plots and stability criteria.</li>
        <li>Developed a nonlinear model predictive controller for DC-bus voltage regulation under constant power loads, optimizing duty cycles and PWM for MOSFET switching. The bus recovers to reference in under 0.1 s after load disturbances.</li>
        <li>Evaluated transient response, stability and disturbance rejection under load steps. Did hardware bring-up and root-cause analysis with DSOs, differential probes and electronic loads to characterize gate ringing, conduction losses and VDS switching transients.</li>
      </ul>
      <p class="t-link"><a href="projects/dc-microgrid-nmpc.html">Read the project write-up</a></p>
    </li>
    <li>
      <p class="t-when">April 2025 to present</p>
      <h2>Electronics project lead</h2>
      <p class="t-org">UCLA Bruin Racing SAE</p>
      <ul class="did">
        <li>Built an eCVT hardware-in-the-loop actuator testbench, with root-cause failure analysis to improve dynamic shifting for Baja SAE.</li>
        <li>Architected an ESP32-S3 controls and DAQ PCB: CAN transceivers, sensor-input and actuator-driver interfaces, custom UART firmware and a Raspberry Pi logging pipeline for real-time telemetry.</li>
        <li>Led the KiCad UI PCB team for Supermileage through board bring-up, component selection, power distribution and electrical interface reviews.</li>
      </ul>
      <p class="t-link"><a href="projects/actuator-testbench.html">Actuator testbench</a><a href="projects/baja-daq.html">DAQ board</a><a href="projects/supermileage-ui.html">Supermileage UI board</a></p>
    </li>
  </ol>

  <h2 class="section-h">Awards</h2>
  <ul class="awards">
    <li><b>2nd place, IdeaHacks 2026</b><span>Hardware hackathon, Los Angeles</span></li>
  </ul>

  <h2 class="section-h">Education</h2>
  <div class="edu">
    <h3>University of California, Los Angeles</h3>
    <p>Power electronics and controls, autonomous systems, mechatronics. BS expected 2028, MS expected 2029.</p>
    <p class="muted">Coursework: power electronics, principles of feedback control, dynamics, circuit theory, signal processing.</p>
  </div>

  <h2 class="section-h">Skills</h2>
  <div class="skills">
    <div><h3>Hardware and controls</h3><p>Altium Designer, KiCad, PCB layout, oscilloscopes and differential probes, CAN, UART, I2C, PWM, PID, LQR, NMPC</p></div>
    <div><h3>Software and simulation</h3><p>Embedded C/C++, MATLAB, Simulink, LTspice, SolidWorks, Onshape, OpenCV, PyTorch</p></div>
  </div>
  <p class="actions"><a class="btn primary" href="assets/docs/Wesley_Hon_Resume.pdf">Download resume (PDF)</a></p>
</section>
"""
    (ROOT / "experience.html").write_text(page("Experience — Wesley Hon", body, "", current="experience", path="experience.html"))


if __name__ == "__main__":
    build_home()
    build_projects()
    for i in range(len(PROJECTS)):
        build_project(i)
    build_experience()
    print(f"Built home, projects, experience and {len(PROJECTS)} project pages.")
