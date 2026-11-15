# Wesley Hon — Engineering Portfolio

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

## Files

```
index.html          all page content
styles.css          design tokens and layout
main.js             Pendubot simulation (hero) and image lightbox
assets/img/         photos, renders and schematic previews (converted from HEIC/PDF)
assets/docs/        resume, schematics and reports linked from the page
assets/video/       go-kart lap clip
assets/favicon.svg
.nojekyll           tells GitHub Pages to serve files as-is
```

## Editing

- **Text:** every project is an `<article class="proj">` (main projects) or `<article class="bin">` (More builds) in `index.html`. Edit the text in place.
- **Images:** add a `.jpg` to `assets/img/` (about 1400 px on the long side keeps the page fast), then add a button inside a project's `.gallery`:
  ```html
  <button class="shot" data-full="assets/img/new.jpg"><img src="assets/img/new.jpg" alt="Describe the photo" loading="lazy"></button>
  ```
- **Resume:** replace `assets/docs/Wesley_Hon_Resume.pdf`, keeping the same file name.
- **GitHub link:** add one to the header and footer once you have a profile to point to.

## The hero simulation

`main.js` simulates the Pendubot using the real link geometry (6061 aluminum, 2 in × 1/4 in, 8 in and 14 in long). It runs RK4 at 1 kHz with an LQR controller designed on the linearization about upright (Q = diag(10, 40, 1, 1), R = 2), and the torque is saturated at 3 N·m. To show a different controller, change `K` and `UMAX`.
