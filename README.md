# Wesley Hon — Engineering Portfolio

Live at https://honwesley.github.io/honwesley-portfolio/

A static site (plain HTML, CSS and JS, no build step) for GitHub Pages.

## Deploy on GitHub Pages

1. Create a new repository on GitHub. Name it `<your-username>.github.io` if you want the site at `https://<your-username>.github.io`, or use any name (such as `portfolio`) to get `https://<your-username>.github.io/portfolio`.
2. Upload everything in this folder to the repository root, keeping `index.html` at the top level:
   ```bash
   git init
   git add .
   git commit -m "Portfolio site"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo>.git
   git push -u origin main
   ```
   Or drag the files into GitHub's "Add file → Upload files" page.
3. In the repository, open **Settings → Pages**. Under "Build and deployment", choose **Deploy from a branch**, branch `main`, folder `/ (root)`, then **Save**.
4. Wait a minute or two for the site to go live at the URL shown on that page.

## Pages

```
index.html                 Home: intro, live Pendubot, selected work
projects.html              All projects, filterable, photos flip on hover
projects/<name>.html       One page per project (15)
experience.html            Experience, education, skills
styles.css / main.js       Design and interactions, shared by every page
assets/img, docs, video    Photos, renders, PDFs and the go-kart clip
_build/                    The generator that writes all the pages
.nojekyll                  Tells GitHub Pages to serve files as-is
```

## Editing projects

All project content lives in one file: `_build/projects.py`. To change text, add photos or add a whole new project:

1. Edit `_build/projects.py`. Each project is a `dict(...)` block; copy an existing one to add a new project.
2. Put any new images in `assets/img/` (about 1400 px on the long side keeps pages fast) and PDFs in `assets/docs/`.
3. From the site folder, run:
   ```bash
   python3 _build/build.py
   ```
   This rewrites every page. It only needs Python 3, no installs.
4. Commit and push (or upload the changed files on GitHub).

Small text fixes can also be made directly in the HTML files on GitHub, but those edits are overwritten the next time you run the build script, so prefer editing `projects.py`.

**Resume:** replace `assets/docs/Wesley_Hon_Resume.pdf`, keeping the same name.

## The hero simulation

`main.js` simulates the Pendubot with the real link geometry (6061 aluminum, 2 in × 1/4 in, 8 in and 14 in long) at 1 kHz with RK4 and a 3 N·m motor limit.

The motor torque acts on the shoulder only. The elbow is a free, frictionless pin: link 2 moves only under gravity and the motion of link 1. Visitors can grab and shove link 1 only. A force on link 1 enters the equations as a shoulder torque (τ = Jᵀ F), so nothing ever acts on the elbow directly.

The motor never switches off. A supervisor switches between two modes:

- **Swing-up:** energy pumping through collocated partial feedback linearization of the shoulder. Because the motor can only change the arm's energy by moving link 1, the commanded link 1 acceleration includes a term proportional to link 2's velocity times the energy error. Without it, link 1 could sit still while link 2 spins forever over the frictionless elbow.
- **Balance:** the controller picked in the panel. It takes over once the LQR cost-to-go xᵀPx drops below 40, and hands back to swing-up above 120.
  - **PID:** two PID loops, on the link 1 angle and the absolute link 2 angle, with the integral on link 1.
  - **LQR:** Q = diag(10, 40, 1, 1), R = 2, on the linearization about upright.
  - **NMPC:** pre-stabilized nonlinear MPC: u = sat(−Kx + v), with v piecewise constant over four blocks of a 0.2 s horizon, re-solved at 50 Hz by gradient descent on the full nonlinear model.
  - **Fuzzy:** 5×5 rule base on the LQR-projected angle error and rate error, with product inference and weighted-average defuzzification.

Gains were tuned offline on the same model. Each controller recovered from hanging straight down, from link 2 spinning at up to 20 rad/s, and from random states up to 10 rad/s on link 1 and 20 rad/s on link 2. The slowest recovery was 7.7 s. The simulation code also lives in `_build/pendubot.js` for reference.
