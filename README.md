# Cooking With Heart

Ginny Bonnie Owen's family cookbook (Edition 2010.1) as a website: 142 recipes, her stories, search, cook mode, a family album and a review page for her corrections.

- `index.html`, `data.js`, `photos/`, `clips/` are the site. It is plain HTML and needs no build step to serve.
- `build/` holds the scripts that turn the cookbook text into `data.js`, and `build/page.html`, the page template.
  - `parse2.py` reads `build/source/c2010.html` (the Word file converted to HTML) into chapters and recipes.
  - `structure.py` splits each recipe into story, ingredients, steps and notes. `overrides.py` holds hand-corrected ingredient lists. `edits.py` holds spelling fixes, marked corrections and open questions.
  - `build_data.py` writes `data.js` and `index.html`. `media.py` prepares web-sized photos and clips.
  - The scripts use absolute paths from the workspace they were written in; adjust `S` at the top of each before running.
- Family notes are stored in a Google Sheet through a small Apps Script. Set `COMMENTS_URL` near the top of the script in `build/page.html`.
