from datetime import date
import time
import spotipy
import sqlite3
import logging
from spotipy.oauth2 import SpotifyClientCredentials

# Import our Spotify utilities
from spotify_utils import (
    safe_spotify_artist,
    rate_limit_delay
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TBL_ID = 0
TBL_LINK_AREA = 1
TBL_NAME = 2
TBL_POPULARITY = 3
TBL_FOLLOWERS = 4
TBL_LINK = 5
TBL_PICTURE_SMALL = 6
TBL_PICTURE_LARGE = 7
TBL_BINACTIVATE = 8
TBL_NOTE = 9

#urn = 'spotify:artist:1McJlk2r0wjhhl1ZOvoMyg' # Åke Hedman
#urn = 'spotify:artist:0WV2Nf4dJ9o6vsOhXPTYBg' # Hellsingland
#urn = 'spotify:artist:5ItiASU9qsDEos573QQP9q' # Mårten
#urn = 'spotify:artist:0vxCTDxolIF2USV7vLPHPh' # Han & Hans Vänner
#urn = 'spotify:artist:1eY4H6MS6rcZKfYlA8KY29' # Hion Martell
#urn = 'spotify:artist:20nKo8C8M0JpIznby9Dv5p' # Östen
#urn = 'spotify:artist:0H8GJ568lnrhJZRqqeroUa' # Perssons Pack
#urn = 'spotify:artist:3sV7Sj5dBERkrVCvKAaOsY' # Oscar Gyllenhammar
#urn = 'spotify:artist:44RPeghKstDd42rYnzyZ8v' # Engmans kapell
#urn = 'spotify:artist:5NDvd4Xn0rR69vih4hW0TM' # Evelina Johnsson
#urn = 'spotify:artist:4d9tSm7JD6nSok1r0W25yb' # Mikale Ivarsson
#urn = 'spotify:artist:0mozOjOMyEjWztjE4tD4bn' # Triol
#urn = 'spotify:artist:7CCsPWwM5oSakpnkoC91Sh' # Stefan Olsson
#urn = 'spotify:artist:0kQTdYH7teYMSKE5tKhGYj' # Per Sonerund
#urn = 'spotify:artist:3UcSfA2eIsNSgTfRZHuhg2' # Bränderna
urn = 'spotify:artist:4MfQTKjLQSOdiYCiYGGg11' # Tad Morose
urn = 'spotify:artist:5dYTF0kETzMSgmsEtUOxu8' # Niklas Karlsson
urn = 'spotify:artist:6BLVCOtxdTupt1wqg3kSIL' # No Sons
urn = 'spotify:artist:3zyk3cvf0fwq5NpceYW8gp' # House of say
urn = 'spotify:artist:6YuRBl1rVNVpWDA4neuDqV' # Oestergaards
urn = 'spotify:artist:32gMJkIkZouy0gNB2Xknbd' # Tobias Westling
urn = 'spotify:artist:2FympPk5bcBe37Sp4VIs4L' # Casper the Ghost
urn = 'spotify:artist:0WV2Nf4dJ9o6vsOhXPTYBg' # Hellsingland
urn = 'spotify:artist:74xUyaS4ldVU4aCSKMhYD4' # Gamla mejeriet
urn = 'spotify:artist:0tUfqypVbl1m19xo9T9yUL' # Selma och Gustav
#urn = 'spotify:artist:1McJlk2r0wjhhl1ZOvoMyg' # Han & Hans Vänner

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

con = sqlite3.connect('toppen.sqlite3')

# Check for optional columns in artists table
artist_columns = [row[1] for row in con.execute("PRAGMA table_info(artists)").fetchall()]
has_apple_music_link = "apple_music_link" in artist_columns
has_youtube_music_link = "youtube_music_link" in artist_columns

#for album in albums:
#  print(album['name'])

cur = con.cursor()
cur_write = con.cursor()
for row in cur.execute('SELECT * FROM artists ORDER BY id'):
  #print(row[TBL_ID])
  urn = row[TBL_ID]
  
  # Use safe Spotify call with retry handling
  artist = safe_spotify_artist(sp, urn)
  if not artist:
     logger.error(f"Failed to get artist data for URN: {urn}")
     continue
  #print(artist)
  print("Name: ",artist['name'])
  if row[TBL_BINACTIVATE] != 0:
    continue
  name = artist['name']
  name = name.replace("\"","''")
  #print("--------------------------------------------------------")
  #print("Popularity: ",artist['popularity'])
  popularity = artist['popularity']
  #print("Followers: ",artist['followers']['total'])
  followers = artist['followers']['total']
  #print("Link: ",artist['external_urls']['spotify'])
  link = artist['external_urls']['spotify']
  picture_small = ""
  picture_large = ""
  if artist['images'].__len__() > 0:
    #print("Picture large: ",artist['images'][0]['url'])
    picture_large = artist['images'][0]['url']
  if artist['images'].__len__() > 1:  
    #print("Picture small: ",artist['images'][1]['url'])
    picture_small = artist['images'][1]['url']
  print("\n")
  sqlstr = 'UPDATE artists SET name = "'
  sqlstr += name
  sqlstr += '", popularity = '
  sqlstr += str(popularity)
  sqlstr += ', followers = '
  sqlstr += str(followers)
  sqlstr += ', link = "'
  sqlstr += link
  sqlstr += '", picture_small = "'
  sqlstr += picture_small
  sqlstr += '", picture_large = "'
  sqlstr += picture_large
  sqlstr += '" WHERE id = "'
  sqlstr += urn
  sqlstr += '"'
  #print("---->",sqlstr)
  cur_write.execute(sqlstr)  
  con.commit()
  # results = sp.artist_albums(urn, album_type='album,single')
  # albums = results['items']
  # while results['next']:
  #  results = sp.next(results)
  #  albums.extend(results['items'])

f = open('topplista-' + str(date.today()) + ".html", 'w')
f.write('''<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=UA-69888-1"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag("js", new Date());
    gtag("config", "UA-69888-1");
  </script>
  <title>Topplista Hälsingland ''' + str(date.today()) + '''</title>
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
    .intro {
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
      line-height: 1.5;
    }
    .intro p {
      margin: 0 0 0.75rem 0;
    }
    .intro p:last-child {
      margin-bottom: 0;
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
    .artist-rank {
      font-size: 1.5rem;
      font-weight: 700;
      color: #1db954;
      min-width: 40px;
      text-align: center;
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
      gap: 0.35rem;
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
    .artist-stats {
      display: flex;
      gap: 0.75rem;
      color: #666;
      font-size: 0.85rem;
    }
    .stat-item {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }
    .stat-label {
      color: #888;
    }
    .stat-value {
      font-weight: 600;
      color: #333;
    }
    .music-links {
      display: flex;
      align-items: center;
      gap: 0.45rem;
      flex-wrap: wrap;
      margin-top: 0.35rem;
    }
    .spotify-btn {
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
  </style>
</head>
<body>
''')
f.write('<h1>Topplista Hälsingland ' + str(date.today()) + '</h1>\n')

f.write('<div class="intro">\n')
f.write('<p>Topplista med artister från Hälsingland baserad på Spotifys ')
f.write('<a href="https://community.spotify.com/t5/Content-Questions/Artist-popularity/td-p/4415259">popularitets index (0-100)</a> ')
f.write('som är konstruerat utifrån hur mycket en artists alla låtar är spelade över tid. Artister som har samma popularitet ')
f.write('är i sin tur ordnade i antal följare. Vill du att din favoritartist skall komma högre upp på den här listan så följ artisten och ')
f.write('spela artistens musik. Svårare än så är det inte.</p>\n')
f.write('<p>Artisterna som är med har någon form av koppling till Hälsingland. Saknar du en artist skicka artistens Spotifylänk till ')
f.write('mig på email <a href="mailto:akhe@grodansparadis.com">akhe@grodansparadis.com</a> och tala om vilken koppling artisten har till Hälsingland.</p>\n')
f.write('<p>Lista med alla artisters topplåtar finns <a href="songs.html" target="main">här</a>. Spellista med alla Häsingeartisters populäraste låtar finns <a href="https://open.spotify.com/playlist/7zXnbJOPoNFnQmp8JfiwZ4">här</a>.</p>\n')
f.write('<p>Listan uppdateras på fredagar.</p>\n')
f.write('</div>\n')

f.write('<div class="search-wrap">\n')
f.write('  <div class="search-row">\n')
f.write('    <input id="artistSearch" class="search-input" type="search" placeholder="Sök artist..." aria-label="Sök artist">\n')
f.write('    <button id="clearSearch" class="search-clear-btn" type="button">Rensa</button>\n')
f.write('  </div>\n')
f.write('  <div id="searchStatus" class="search-status"></div>\n')
f.write('</div>\n')
f.write('<ul class="artist-list">\n')

# Build column selection for optional fields
select_cols = "id, link_area, name, popularity, followers, link, picture_small, picture_large, bInactivate, note"
if has_apple_music_link:
  select_cols += ", apple_music_link"
if has_youtube_music_link:
  select_cols += ", youtube_music_link"

cnt = 1
for row in cur.execute(f'SELECT {select_cols} FROM artists ORDER BY popularity DESC'):

  urn = row[0]  # id

  if row[8] != 0:  # bInactivate
    continue

  # Use safe Spotify call with retry handling
  artist = safe_spotify_artist(sp, urn)
  if not artist:
    logger.error(f"Failed to get artist data for {row[2]} (URN: {urn})")
    continue
  
  print(str(cnt) + ". " + str(artist['popularity']) + " " + artist['name'] + " (" + str(artist['followers']['total']) + ")")

  artist_name = artist['name']
  spotify_link = artist['external_urls']['spotify']
  popularity = artist['popularity']
  followers = artist['followers']['total']
  image_url = ""
  if artist['images'].__len__() > 0:
    image_url = artist['images'][0]['url']
  
  # Get optional music links from database
  apple_music_link = ""
  youtube_music_link = ""
  col_idx = 10  # After the standard columns
  if has_apple_music_link:
    apple_music_link = (row[col_idx] or "").strip()
    col_idx += 1
  if has_youtube_music_link:
    youtube_music_link = (row[col_idx] or "").strip()

  f.write(f'  <li class="artist-item" data-artist-name="{artist_name.lower()}">\n')
  f.write('    <div class="artist-main">\n')
  f.write(f'      <span class="artist-rank">{cnt}</span>\n')
  f.write('      <div class="artist-main-content">\n')
  if image_url:
    f.write(f'        <img class="artist-image" src="{image_url}" alt="{artist_name}">\n')
  else:
    f.write('        <div class="artist-image"></div>\n')
  f.write('        <div class="artist-text">\n')
  f.write(f'          <span class="artist-name">{artist_name}</span>\n')
  f.write('          <div class="artist-stats">\n')
  f.write(f'            <span class="stat-item"><span class="stat-label">Popularitet:</span> <span class="stat-value">{popularity}</span></span>\n')
  f.write(f'            <span class="stat-item"><span class="stat-label">Följare:</span> <span class="stat-value">{followers:,}</span></span>\n')
  f.write('          </div>\n')
  f.write('          <div class="music-links">\n')
  f.write(f'            <a class="spotify-btn" href="{spotify_link}" target="_blank" rel="noopener noreferrer"><img class="spotify-icon" src="https://open.spotify.com/favicon.ico" alt="">Spotify</a>\n')
  if apple_music_link:
    f.write(f'            <a class="spotify-btn apple-music-btn" href="{apple_music_link}" target="_blank" rel="noopener noreferrer"> Apple Music</a>\n')
  if youtube_music_link:
    f.write(f'            <a class="spotify-btn youtube-music-btn" href="{youtube_music_link}" target="_blank" rel="noopener noreferrer">YouTube Music</a>\n')
  f.write('          </div>\n')
  f.write('        </div>\n')
  f.write('      </div>\n')
  f.write('    </div>\n')
  f.write('  </li>\n')

  cnt = cnt + 1
  
  # Add rate limiting delay between requests
  rate_limit_delay()

f.write('</ul>\n')

f.write('''<script>
  const searchInput = document.getElementById('artistSearch');
  const clearSearchButton = document.getElementById('clearSearch');
  const searchStatus = document.getElementById('searchStatus');
  const artistList = document.querySelector('.artist-list');
  const artistItems = Array.from(document.querySelectorAll('.artist-item'));

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
  updateSearchStatus(artistItems.length);
</script>
''')

f.write('<p style="text-align: center; margin-top: 2rem;">Listan sammanställd av <a href="https://www.akehedman.se/">Åke Hedman</a></p>\n')

f.write('</body></html>\n') 
f.close()
con.close()
