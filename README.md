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

`main.js` simulates the Pendubot using the real link geometry (6061 aluminum, 2 in × 1/4 in, 8 in and 14 in long). It runs RK4 at 1 kHz with an LQR controller designed on the linearization about upright (Q = diag(10, 40, 1, 1), R = 2), and the torque is saturated at 3 N·m. To show a different controller, change `K` and `UMAX`.
