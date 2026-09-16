# ORBITAL — Space Network Testbed

Complete static source for the ORBITAL website. No npm installation, build step, database, API key, or ChatGPT hosting dependency is required.

## Files to edit

| File | Purpose |
| --- | --- |
| `index.html` | Website title, navigation, mission pitch, architecture, six use cases, evaluation workflow, and footer |
| `style.css` | Colors, typography, spacing, responsive layouts, and diagram styles |
| `app.js` | Four scenario descriptions, scenario switching, and animated orbital visualization |
| `.nojekyll` | Tells GitHub Pages to serve the static files without Jekyll processing |

## Deploy using the GitHub website

1. Create a repository or open the repository where you want to host this site.
2. Extract this ZIP on your computer.
3. Upload `index.html`, `style.css`, `app.js`, and `.nojekyll` to the repository root. You may also upload this README. Upload the extracted files, not the ZIP or its enclosing folder. Preserve unrelated files in an existing repository; check for filename conflicts before uploading.
4. Commit the files to your publishing branch (typically `main`).
5. Open repository **Settings → Pages**.
6. Under **Build and deployment**, select **Deploy from a branch**.
7. Select your publishing branch and **/ (root)**, then save.
8. When deployment finishes, use **Visit site** on the Pages settings screen.

A project site normally uses `https://YOUR-USERNAME.github.io/YOUR-REPOSITORY/`. A repository named `YOUR-USERNAME.github.io` normally uses `https://YOUR-USERNAME.github.io/`. The relative CSS and JavaScript paths support either layout.

GitHub Pages availability and visibility depend on your account and organization settings. This export does not carry over the private access controls of the original hosted site.

Official instructions: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Update the content manually

Open a file in GitHub, choose Edit, make your changes, and commit to the publishing branch. GitHub Pages republishes changes automatically; publication can take a few minutes.

- **Brand:** search `ORBITAL` in `index.html`. Change the browser title in `<title>` and the description in `<meta name="description">` too.
- **Hero text:** edit the `<h1>` and paragraph with `class="lead"`.
- **Architecture:** edit the section with `id="architecture"`.
- **Use cases:** edit the six `<article>` elements inside `id="missions"`.
- **Evaluation:** edit the section with `id="evaluation"`.
- **Colors:** edit the variables at the beginning of `style.css`, such as `--bg`, `--gold`, and `--cyan`.
- **Scenario descriptions:** edit the `scenarios` object at the beginning of `app.js`. Its keys are `nominal`, `handover`, `outage`, and `congestion`. If you change the initial nominal scenario, update the initial scenario text in `index.html` as well.

Preserve element IDs and `data-scenario` attributes unless you update their corresponding JavaScript references. A code editor's Format Document command can expand the compact source for easier editing.

## Preview locally

Open `index.html` directly in a modern browser, or serve the extracted directory with Python:

```sh
python -m http.server 8000
```

Then visit `http://localhost:8000`. Stop the server with Ctrl+C.

## Dependencies and scope

The fonts are requested from Google Fonts in the first line of `style.css`. If unavailable, local fallback fonts are used. Remove that import to avoid the external font request. All orbital and packet-path graphics are rendered locally using Canvas and SVG; no external image files are needed.

The website presents a proposed platform. Its scenario explorer is illustrative: it does not run ns-3, Docker containers, or a live mission simulation. It contains no measured performance claims. Reduced-motion preferences and the animation pause control are supported.

This package contains the website assets and deployment documentation, excluding hosting-specific configuration and Git credentials.
