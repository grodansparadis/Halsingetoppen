from datetime import date
import time
import spotipy
import sqlite3
from spotipy.oauth2 import SpotifyClientCredentials

TBL_ID = 0
TBL_ARTIST_ID = 1
TBL_NAME = 2
TBL_POPULARITY = 3
TBL_ALBUM_TYPE = 4
TBL_URL = 5
TBL_RELEASE_DATE = 6

sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

con = sqlite3.connect('toppen.sqlite3')

print("Topp songs")
f = open('songs.html', 'w')
f.write('<html><head>\n') 
f.write('<!-- Global site tag (gtag.js) - Google Analytics -->')
f.write('<script async src="https://www.googletagmanager.com/gtag/js?id=G-SNRXECZNJX"></script>')
f.write('<script>')
f.write('  window.dataLayer = window.dataLayer || [];')
f.write('  function gtag(){dataLayer.push(arguments);}')
f.write("  gtag('js', new Date());")
f.write('                                 ')
f.write("  gtag('config', 'G-SNRXECZNJX');")
f.write('</script>')
f.write('<meta charset="utf-8"/>\n')
f.write('<style>\n')
f.write('  table, th, td {\n')
f.write('  border: 1px solid black;\n')
f.write('  padding: 10px;\n')
f.write('  border-collapse: collapse;}\n')
f.write('p {\n')
f.write(' border-bottom:1px dotted;\n')
f.write(' margin-left:auto;\n')
f.write(' margin-right:auto;\n')
f.write(' text-align:left;\n')
f.write(' width: 60%;\n')
f.write('}\n')
f.write('h1 {\n')
f.write(' text-align:center;\n')
f.write('}\n')
f.write('</style>\n')
f.write('</head><body>\n') 
f.write('<h1>Topplista Hälsingland - Mest lyssnade spår i alfabetisk ordning</h1>\n')

f.write('<p>Här listas topplistans alla artisters mest lyssnade spår (max tio spår per artist). Eftersom Spotify inte delar antal lysningar per låt listas låtarna i alfabetisk ordning. Spår som finns både som singel och i ett album listas separat om båda är bland de mest avlyssnade.</p>\n')

f.write('<p>Spellista med alla spår finns <a href="https://open.spotify.com/playlist/7zXnbJOPoNFnQmp8JfiwZ4">här</a>.</p>')

f.write('<p><a href="index.html">Gå tillbaks till huvudsida.</a></p>\n')

f.write('<p><table border="1">\n')
f.write('<tr><th>Track</th><th>Artist</th><th>Info</th></tr>\n')

cur = con.cursor()
cur_write = con.cursor()

idx = 0;
for row in cur.execute('SELECT * FROM tracks ORDER BY name'):  
  urn = row[TBL_ARTIST_ID]
  try:
     print(urn,row[TBL_NAME])
     artist = sp.artist(urn)
  except:
     print("* * * * * * * ------>",urn,"Not found")
     continue
  print(row[TBL_NAME]," - ",artist['name'],",",row[TBL_ALBUM_TYPE],",",row[TBL_RELEASE_DATE],row[TBL_URL])
  idx = idx + 1

  f.write('<tr><td><a href="')
  f.write(row[TBL_URL])
  f.write('" target="main">')
  f.write(row[TBL_NAME])
  f.write('</a></td><td><a href="')
  f.write(artist['external_urls']['spotify'])
  f.write('" target="main">')
  f.write(artist['name'])
  f.write('</a></td><td>')
  f.write(row[TBL_ALBUM_TYPE])
  f.write(",")
  f.write(row[TBL_RELEASE_DATE])
  f.write('</td></tr>\n')

f.write('</table></p>\n')

f.write('<p>Listan sammanställd av <a href="https://www.akehedman.se/">Åke Hedman</a></p>')

f.write('</body></html>\n') 
f.close()
con.close()