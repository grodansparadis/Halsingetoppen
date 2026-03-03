#!/usr/bin/env python3
"""Generate a randomized HTML list of artists from the database."""

from datetime import datetime
from html import escape
import sqlite3

DB_PATH = "toppen.sqlite3"
OUTPUT_FILE = "artistlista_random.html"


def generate_random_artist_list(db_path: str = DB_PATH, output_file: str = OUTPUT_FILE) -> str:
    """Generate an HTML artist list with random ordering for each run."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    artist_columns = [row[1] for row in conn.execute("PRAGMA table_info(artists)").fetchall()]
    has_added_at = "added_at" in artist_columns
    has_markdown_info = "markdown_info" in artist_columns
    has_apple_music_link = "apple_music_link" in artist_columns
    has_youtube_music_link = "youtube_music_link" in artist_columns

    added_at_select = "added_at" if has_added_at else "NULL as added_at"
    markdown_info_select = "markdown_info" if has_markdown_info else "NULL as markdown_info"
    apple_music_link_select = "apple_music_link" if has_apple_music_link else "NULL as apple_music_link"
    youtube_music_link_select = "youtube_music_link" if has_youtube_music_link else "NULL as youtube_music_link"

    artists = conn.execute(
      f"""
      SELECT rowid as artist_rowid, name, link, picture_large, picture_small, {added_at_select}, {markdown_info_select}, {apple_music_link_select}, {youtube_music_link_select}
        FROM artists
        WHERE bInactivate = 0 OR bInactivate IS NULL
        ORDER BY RANDOM()
      """
    ).fetchall()

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(
            """<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hälsingeartister</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 960px;
      margin: 0 auto;
      padding: 1rem;
      background: #f5f5f5;
    }
    h1 {
      text-align: center;
    }
    .meta {
      text-align: center;
      color: #555;
      margin-bottom: 1rem;
    }
    .search-wrap {
      margin-bottom: 1rem;
    }
    .search-row {
      display: flex;
      gap: 0.5rem;
    }
    .search-input {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid #ccc;
      border-radius: 8px;
      padding: 0.65rem 0.75rem;
      font: inherit;
      background: #fff;
      flex: 1;
    }
    .search-clear-btn {
      border: 1px solid #ccc;
      background: #fff;
      border-radius: 8px;
      padding: 0.65rem 0.9rem;
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      color: #333;
      white-space: nowrap;
    }
    .search-clear-btn:hover {
      background: #f1f1f1;
    }
    .search-status {
      margin-top: 0.5rem;
      color: #666;
      font-size: 0.9rem;
    }
    .toolbar {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    .randomize-btn {
      border: 1px solid #ccc;
      background: #fff;
      border-radius: 8px;
      padding: 0.6rem 0.9rem;
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      color: #333;
    }
    .randomize-btn:hover {
      background: #f1f1f1;
    }
    .artist-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 0.75rem;
    }
    .artist-item {
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 0.75rem;
      display: block;
    }
    .artist-main {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .artist-main-content {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex: 1;
    }
    .artist-text {
      display: flex;
      flex-direction: column;
      gap: 0.45rem;
    }
    .artist-image {
      width: 64px;
      height: 64px;
      border-radius: 8px;
      object-fit: cover;
      background: #eee;
      flex-shrink: 0;
    }
    .artist-name {
      color: #222;
      font-weight: 700;
      font-size: 1.05rem;
    }
    .artist-added {
      color: #666;
      font-size: 0.8rem;
    }
    .music-links {
      display: flex;
      align-items: center;
      gap: 0.45rem;
      flex-wrap: wrap;
    }
    .spotify-btn {
      display: inline-block;
      width: fit-content;
      display: inline-flex;
      align-items: center;
      text-decoration: none;
      border-radius: 6px;
      padding: 0.35rem 0.65rem;
      background: #1db954;
      color: #fff;
      font-size: 0.85rem;
      font-weight: 700;
    }
    .spotify-icon {
      width: 14px;
      height: 14px;
      margin-right: 0.35rem;
      display: inline-block;
    }
    .spotify-btn:hover {
      background: #18a449;
    }
    .apple-music-btn {
      background: #111;
      color: #fff;
    }
    .apple-music-btn:hover {
      background: #000;
    }
    .youtube-music-btn {
      background: #ff0000;
      color: #fff;
    }
    .youtube-music-btn:hover {
      background: #d80000;
    }
    .tip-btn {
      background: #0d6efd;
      border: none;
      color: #fff;
      font-weight: 700;
      border-radius: 6px;
      width: 36px;
      height: 36px;
      padding: 0;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .tip-btn:hover {
      background: #0b5ed7;
    }
    .tip-btn svg {
      width: 18px;
      height: 18px;
      fill: currentColor;
    }
    .info-btn {
      background: #5a5a5a;
      border: none;
      color: #fff;
      font-weight: 700;
      border-radius: 6px;
      width: 36px;
      height: 36px;
      padding: 0;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.95rem;
    }
    .info-btn:hover {
      background: #444;
    }
    .artist-actions {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }
    .artist-info-panel {
      display: none;
      margin-top: 0.65rem;
      border-top: 1px solid #e5e5e5;
      padding-top: 0.65rem;
    }
    .artist-info-panel.open {
      display: block;
    }
    .artist-info-content {
      background: #fafafa;
      border: 1px solid #e5e5e5;
      border-radius: 6px;
      padding: 0.65rem;
      color: #333;
      font-size: 0.92rem;
      line-height: 1.45;
    }
    .artist-info-content p:last-child {
      margin-bottom: 0;
    }
    .tip-form {
      margin-top: 0.75rem;
      padding-top: 0.75rem;
      border-top: 1px solid #e5e5e5;
      display: none;
    }
    .tip-form.open {
      display: block;
    }
    .tip-form label {
      display: block;
      margin-bottom: 0.5rem;
      color: #333;
      font-size: 0.95rem;
    }
    .tip-form input,
    .tip-form textarea {
      width: 100%;
      box-sizing: border-box;
      margin-top: 0.25rem;
      border: 1px solid #ccc;
      border-radius: 6px;
      padding: 0.5rem;
      font: inherit;
    }
    .tip-form textarea {
      min-height: 100px;
      resize: vertical;
    }
    .tip-form-actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 0.5rem;
    }
    .tip-submit,
    .tip-cancel {
      border: none;
      border-radius: 6px;
      padding: 0.5rem 0.75rem;
      cursor: pointer;
      font-weight: 700;
    }
    .tip-submit {
      background: #1db954;
      color: #fff;
    }
    .tip-cancel {
      background: #ddd;
      color: #222;
    }
    .tip-note {
      color: #666;
      font-size: 0.85rem;
      margin-top: 0.5rem;
      margin-bottom: 0;
    }
    .help-wrap {
      margin-top: 0.5rem;
      position: relative;
      display: inline-block;
    }
    .help-icon {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: 1px solid #888;
      color: #555;
      background: #fff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.8rem;
      cursor: help;
      user-select: none;
    }
    .help-bubble {
      display: none;
      position: absolute;
      z-index: 10;
      left: 26px;
      top: -6px;
      min-width: 260px;
      max-width: 340px;
      background: #333;
      color: #fff;
      border-radius: 6px;
      padding: 0.5rem 0.6rem;
      font-size: 0.8rem;
      line-height: 1.35;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    .help-wrap:hover .help-bubble {
      display: block;
    }
  </style>
</head>
<body>
"""
        )

        f.write("<h1>Hälsingeartister</h1>\n")
        f.write(
          f"<p class=\"meta\">Detta är en lista med artister från Hälsingland. Listan visas i slumpmässig ordning. • Genererad {escape(datetime.now().strftime('%Y-%m-%d %H:%M'))}</p>\n"
        )
        f.write("<div class=\"toolbar\">\n")
        f.write("  <button type=\"button\" class=\"randomize-btn toggle-tip-form\" data-form-id=\"general-tip-form\">Tipsa om artist som saknas</button>\n")
        f.write("  <button id=\"showLatest\" class=\"randomize-btn\" type=\"button\">Visa senaste tillagda</button>\n")
        f.write("  <button id=\"randomizeList\" class=\"randomize-btn\" type=\"button\">Randomisera ordning</button>\n")
        f.write("</div>\n")

        f.write("<form id=\"general-tip-form\" class=\"tip-form\" action=\"/api/artist-tip\" method=\"post\">\n")
        f.write("  <label>Artistens namn<input type=\"text\" name=\"artist\" required></label>\n")
        f.write("  <label>Koppling till Hälsingland<textarea name=\"halsingland_connection\" required></textarea></label>\n")
        f.write("  <label>Spotify-länk<input type=\"url\" name=\"spotify_link\" placeholder=\"https://open.spotify.com/artist/...\"></label>\n")
        f.write("  <label>Apple Music-länk<input type=\"url\" name=\"apple_music_link\" placeholder=\"https://music.apple.com/...\"></label>\n")
        f.write("  <label>YouTube Music-länk<input type=\"url\" name=\"youtube_music_link\" placeholder=\"https://music.youtube.com/...\"></label>\n")
        f.write("  <input type=\"hidden\" name=\"source_url\" class=\"source-url-field\" value=\"\">\n")
        f.write("  <label>Ditt namn<input type=\"text\" name=\"namn\" required></label>\n")
        f.write("  <label>Din e-post<input type=\"email\" name=\"epost\" required></label>\n")
        f.write("  <label>Information om artisten<textarea name=\"information\" required></textarea></label>\n")
        f.write("  <div class=\"tip-form-actions\">\n")
        f.write("    <button type=\"submit\" class=\"tip-submit\">Skicka</button>\n")
        f.write("    <button type=\"button\" class=\"tip-cancel close-tip-form\" data-form-id=\"general-tip-form\">Stäng</button>\n")
        f.write("  </div>\n")
        f.write("  <div class=\"help-wrap\">\n")
        f.write("    <span class=\"help-icon\" aria-label=\"Hjälp\" title=\"Hjälp\">i</span>\n")
        f.write("    <span class=\"help-bubble\">Skicka tips om en artist som ännu inte finns i listan.</span>\n")
        f.write("  </div>\n")
        f.write("</form>\n")
        f.write("<div class=\"search-wrap\">\n")
        f.write("  <div class=\"search-row\">\n")
        f.write("    <input id=\"artistSearch\" class=\"search-input\" type=\"search\" placeholder=\"Sök artist...\" aria-label=\"Sök artist\">\n")
        f.write("    <button id=\"clearSearch\" class=\"search-clear-btn\" type=\"button\">Rensa</button>\n")
        f.write("  </div>\n")
        f.write("  <div id=\"searchStatus\" class=\"search-status\"></div>\n")
        f.write("</div>\n")
        f.write("<ul class=\"artist-list\">\n")

        for index, artist in enumerate(artists, start=1):
            artist_name_raw = (artist["name"] or "Okänd artist").strip()
            name = escape(artist_name_raw)
            spotify_link = (artist["link"] or "").strip()
            apple_music_link = (artist["apple_music_link"] or "").strip()
            youtube_music_link = (artist["youtube_music_link"] or "").strip()
            image_url = (artist["picture_large"] or artist["picture_small"] or "").strip()
            artist_rowid = int(artist["artist_rowid"])
            added_at = (artist["added_at"] or "okänt")
            markdown_info_raw = (artist["markdown_info"] or "").strip()
            form_id = f"tip-form-{index}"
            info_panel_id = f"artist-info-{index}"

            f.write(
              f"  <li class=\"artist-item\" data-artist-name=\"{escape(artist_name_raw.lower(), quote=True)}\" data-artist-rowid=\"{artist_rowid}\">\n"
            )
            f.write("    <div class=\"artist-main\">\n")
            f.write("      <div class=\"artist-main-content\">\n")

            if image_url:
                f.write(
                    f"        <img class=\"artist-image\" src=\"{escape(image_url, quote=True)}\" alt=\"{name}\">\n"
                )
            else:
                f.write("        <div class=\"artist-image\"></div>\n")

            f.write("        <div class=\"artist-text\">\n")
            f.write(f"          <span class=\"artist-name\">{name}</span>\n")
            f.write(f"          <span class=\"artist-added\">Tillagd: {escape(str(added_at))}</span>\n")
            f.write("          <div class=\"music-links\">\n")
            if spotify_link:
              f.write(
                f"          <a class=\"spotify-btn\" href=\"{escape(spotify_link, quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\"><img class=\"spotify-icon\" src=\"https://open.spotify.com/favicon.ico\" alt=\"\">Spotify</a>\n"
              )
            if apple_music_link:
                f.write(
                    f"          <a class=\"spotify-btn apple-music-btn\" href=\"{escape(apple_music_link, quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\"> Apple Music</a>\n"
                )
            if youtube_music_link:
              f.write(
                f"          <a class=\"spotify-btn youtube-music-btn\" href=\"{escape(youtube_music_link, quote=True)}\" target=\"_blank\" rel=\"noopener noreferrer\"><i class=\"fab fa-youtube\" aria-hidden=\"true\"></i>&nbsp;YouTube Music</a>\n"
              )
            f.write("          </div>\n")
            f.write("        </div>\n")

            f.write("      </div>\n")
            f.write("      <div class=\"artist-actions\">\n")
            f.write(
              f"        <button type=\"button\" class=\"info-btn toggle-artist-info\" data-info-id=\"{info_panel_id}\" aria-label=\"Visa artistinfo\" title=\"Visa artistinfo\">i</button>\n"
            )
            f.write(
              f"        <button type=\"button\" class=\"tip-btn toggle-tip-form\" data-form-id=\"{form_id}\" aria-label=\"Tipsa om artist\" title=\"Tipsa om artist\"><svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M4 4h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H9l-5 4v-4H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm3 5v2h10V9H7zm0 4v2h7v-2H7z\"/></svg></button>\n"
            )
            f.write("      </div>\n")
            f.write("    </div>\n")

            f.write(f"    <div id=\"{info_panel_id}\" class=\"artist-info-panel\">\n")
            f.write("      <div class=\"artist-info-content\" data-rendered=\"false\"></div>\n")
            f.write(
              f"      <textarea class=\"artist-markdown-source\" hidden>{escape(markdown_info_raw or 'Ingen information tillgänglig ännu.')}</textarea>\n"
            )
            f.write("    </div>\n")

            f.write(
              f"    <form id=\"{form_id}\" class=\"tip-form\" action=\"/api/artist-tip\" method=\"post\">\n"
            )
            f.write(
                f"      <input type=\"hidden\" name=\"artist\" value=\"{escape(artist_name_raw, quote=True)}\">\n"
            )
            f.write("      <input type=\"hidden\" name=\"source_url\" class=\"source-url-field\" value=\"\">\n")
            f.write("      <label>Ditt namn<input type=\"text\" name=\"namn\" required></label>\n")
            f.write("      <label>Din e-post<input type=\"email\" name=\"epost\" required></label>\n")
            f.write("      <label>Information om artisten<textarea name=\"information\" required></textarea></label>\n")
            f.write("      <div class=\"tip-form-actions\">\n")
            f.write("        <button type=\"submit\" class=\"tip-submit\">Skicka</button>\n")
            f.write(
                f"        <button type=\"button\" class=\"tip-cancel close-tip-form\" data-form-id=\"{form_id}\">Stäng</button>\n"
            )
            f.write("      </div>\n")
            f.write("      <div class=\"help-wrap\">\n")
            f.write("        <span class=\"help-icon\" aria-label=\"Hjälp\" title=\"Hjälp\">i</span>\n")
            f.write("        <span class=\"help-bubble\">Informationen skickas till toppen@grodansparadis.com.</span>\n")
            f.write("      </div>\n")
            f.write("    </form>\n")
            f.write("  </li>\n")

        f.write("</ul>\n")
        f.write(
            """<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
  document.querySelectorAll('.toggle-tip-form').forEach(function(button) {
    button.addEventListener('click', function() {
      const form = document.getElementById(button.dataset.formId);
      if (!form) return;
      form.classList.toggle('open');
    });
  });

  document.querySelectorAll('.toggle-artist-info').forEach(function(button) {
    button.addEventListener('click', function() {
      const panel = document.getElementById(button.dataset.infoId);
      if (!panel) return;

      const content = panel.querySelector('.artist-info-content');
      const source = panel.querySelector('.artist-markdown-source');
      if (content && source && content.dataset.rendered !== 'true') {
        const markdownText = source.value || '';
        if (window.marked && typeof window.marked.parse === 'function') {
          content.innerHTML = window.marked.parse(markdownText);
        } else {
          content.textContent = markdownText;
        }
        content.dataset.rendered = 'true';
      }

      panel.classList.toggle('open');
    });
  });

  document.querySelectorAll('.close-tip-form').forEach(function(button) {
    button.addEventListener('click', function() {
      const form = document.getElementById(button.dataset.formId);
      if (!form) return;
      form.classList.remove('open');
    });
  });

  function fallbackToMailto(formData) {
    const recipient = 'toppen@grodansparadis.com';
    const artist = formData.get('artist') || '';
    const senderName = formData.get('namn') || '';
    const senderEmail = formData.get('epost') || '';
    const halsinglandConnection = formData.get('halsingland_connection') || '';
    const spotifyLink = formData.get('spotify_link') || '';
    const appleMusicLink = formData.get('apple_music_link') || '';
    const youtubeMusicLink = formData.get('youtube_music_link') || '';
    const info = formData.get('information') || '';
    const sourceUrl = formData.get('source_url') || window.location.href;

    const subject = 'Artisttips: ' + artist;
    const body = [
      'Artist: ' + artist,
      'Namn: ' + senderName,
      'E-post: ' + senderEmail,
      'Källa: ' + sourceUrl,
      'Koppling till Hälsingland: ' + (halsinglandConnection || '-'),
      'Spotify-länk: ' + (spotifyLink || '-'),
      'Apple Music-länk: ' + (appleMusicLink || '-'),
      'YouTube Music-länk: ' + (youtubeMusicLink || '-'),
      '',
      'Information:',
      info
    ].join('\\n');

    window.location.href = 'mailto:' + encodeURIComponent(recipient)
      + '?subject=' + encodeURIComponent(subject)
      + '&body=' + encodeURIComponent(body);
  }

  document.querySelectorAll('.tip-form').forEach(function(form) {
    form.addEventListener('submit', async function(event) {
      event.preventDefault();
      const formData = new FormData(form);

      try {
        const response = await fetch('/api/artist-tip', {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          fallbackToMailto(formData);
          return;
        }

        alert('Tack! Ditt tips har skickats.');
        form.reset();
        form.querySelectorAll('.source-url-field').forEach(function(field) {
          field.value = window.location.href;
        });
        form.classList.remove('open');
      } catch (error) {
        fallbackToMailto(formData);
      }
    });
  });

  const searchInput = document.getElementById('artistSearch');
  const clearSearchButton = document.getElementById('clearSearch');
  const showLatestButton = document.getElementById('showLatest');
  const randomizeButton = document.getElementById('randomizeList');
  const searchStatus = document.getElementById('searchStatus');
  const artistList = document.querySelector('.artist-list');
  const artistItems = Array.from(document.querySelectorAll('.artist-item'));

  function shuffleVisibleArtists() {
    const visibleItems = artistItems.filter(function(item) {
      return item.style.display !== 'none';
    });

    for (let i = visibleItems.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      const temp = visibleItems[i];
      visibleItems[i] = visibleItems[j];
      visibleItems[j] = temp;
    }

    visibleItems.forEach(function(item) {
      artistList.appendChild(item);
    });
  }

  function showLatestVisibleArtists() {
    const visibleItems = artistItems.filter(function(item) {
      return item.style.display !== 'none';
    });

    visibleItems.sort(function(a, b) {
      return Number(b.dataset.artistRowid) - Number(a.dataset.artistRowid);
    });

    visibleItems.forEach(function(item) {
      artistList.appendChild(item);
    });
  }

  function updateSearchStatus(visibleCount) {
    searchStatus.textContent = 'Visar ' + visibleCount + ' av ' + artistItems.length + ' artister';
  }

  function filterArtists() {
    const query = (searchInput.value || '').trim().toLowerCase();
    let visibleCount = 0;

    artistItems.forEach(function(item) {
      const artistName = item.dataset.artistName || '';
      const isMatch = artistName.includes(query);
      item.style.display = isMatch ? 'block' : 'none';
      if (isMatch) {
        visibleCount += 1;
      }
    });

    updateSearchStatus(visibleCount);
  }

  searchInput.addEventListener('input', filterArtists);
  searchInput.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      searchInput.value = '';
      filterArtists();
    }
  });
  clearSearchButton.addEventListener('click', function() {
    searchInput.value = '';
    filterArtists();
    searchInput.focus();
  });
  randomizeButton.addEventListener('click', function() {
    shuffleVisibleArtists();
  });
  showLatestButton.addEventListener('click', function() {
    showLatestVisibleArtists();
  });
  updateSearchStatus(artistItems.length);
</script>
"""
        )
        f.write(
            """<script>
  document.querySelectorAll('.source-url-field').forEach(function(field) {
    field.value = window.location.href;
  });
</script>
"""
        )
        f.write("</body>\n</html>\n")

    conn.close()
    return output_file


if __name__ == "__main__":
    output = generate_random_artist_list()
    print(f"Generated: {output}")
