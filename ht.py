from datetime import date
import time
import spotipy
import sqlite3
from spotipy.oauth2 import SpotifyClientCredentials

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

#for album in albums:
#  print(album['name'])

cur = con.cursor()
cur_write = con.cursor()
for row in cur.execute('SELECT * FROM artists ORDER BY id'):
  print(row[TBL_ID])
  urn = row[TBL_ID]
  try:
     artist = sp.artist(urn)
  except:
     print("* * * * * * * ------>",urn,"Not found")
     continue
  print(artist)
  print("Name: ",artist['name'])
  if row[TBL_BINACTIVATE] != 0:
    continue
  name = artist['name']
  name = name.replace("\"","''")
  print("--------------------------------------------------------")
  print("Popularity: ",artist['popularity'])
  popularity = artist['popularity']
  print("Followers: ",artist['followers']['total'])
  followers = artist['followers']['total']
  print("Link: ",artist['external_urls']['spotify'])
  link = artist['external_urls']['spotify']
  picture_small = ""
  picture_large = ""
  if artist['images'].__len__() > 0:
    print("Picture large: ",artist['images'][0]['url'])
    picture_large = artist['images'][0]['url']
  if artist['images'].__len__() > 1:  
    print("Picture small: ",artist['images'][1]['url'])
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
  #results = sp.artist_albums(urn, album_type='album,single')
  #albums = results['items']
  #while results['next']:
  #  results = sp.next(results)
  #  albums.extend(results['items'])

f = open('topplista-' + str(date.today()) + ".html", 'w')
f.write('<html><head>\n') 
f.write('<!-- Global site tag (gtag.js) - Google Analytics -->')
f.write('<script async src="https://www.googletagmanager.com/gtag/js?id=G-SNRXECZNJX"></script>')
f.write('<script>')
f.write('  window.dataLayer = window.dataLayer || [];')
f.write('  function gtag(){dataLayer.push(arguments);}')
f.write('  gtag('js', new Date());')
f.write('')
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
f.write('<h1>Topplista Hälsingland ' + str(date.today()) + '</h1>\n')

f.write('<p>Topplista med artister från Hälsingland baserad på Spotifys ')
f.write('<a href="https://community.spotify.com/t5/Content-Questions/Artist-popularity/td-p/4415259">popularitets index (0-100)</a> ')
f.write('som är konstruerat utifrån hur mycket en artists alla låtar är spelade över tid. Artister som har samma popularitet ')
f.write('är i sin tur ordnade i antal följare. Vill du att din favoritartist skall komma högre upp på den här listan så följ artisten och ')
f.write('spela artistens musik. Svårare än så är det inte.</p>')
f.write('<p>Artisterna som är med har någon form av koppling till Hälsingland. Saknar du en artist skicka artistens Spotifylänk till ')
f.write('mig på email <a href="mailto:akhe@grodansparadis.com">akhe@grodansparadis.com</a> och tala om vilken koppling artisten har till Hälsingland.')
f.write('<p>Listan kommer att uppdateras på fredagar fortsättningsvis.</p>')

f.write('<p><table border="1">\n')
f.write('<tr><th>Plats</th><th>Artist</th><th>Popularitet</th><th>Följare</th><th></th></tr>\n')

cnt = 1
for row in cur.execute('SELECT * FROM artists ORDER BY popularity DESC'):

  urn = row[TBL_ID]

  if row[TBL_BINACTIVATE] != 0:
    continue

  try:
    artist = sp.artist(urn)
  except:
    print(row[TBL_NAME])
    #print(" ------>",artist['name'],urn,"Not found")
    artist = sp.artist(urn)
    #continue
  
  print(str(cnt) + ". " + str(artist['popularity']) + " " + artist['name'] + " (" + str(artist['followers']['total']) + ")")

  f.write('<tr><td style="text-align:center"><b>')
  f.write(str(cnt))
  f.write('</b></td><td>')
  f.write('<a href="')
  f.write(artist['external_urls']['spotify'])
  f.write('">')
  f.write(artist['name'])
  f.write('</a></td><td style="text-align:center">')
  f.write(str(artist['popularity']))
  f.write('</td><td style="text-align:center">')
  f.write(str(artist['followers']['total']))
  f.write('</td><td>')
  if artist['images'].__len__() > 0:
    f.write('<img src="' + artist['images'][0]['url'] + '" width="100" height="100">')
  f.write('</td></tr>\n')

  cnt = cnt + 1
  #time.sleep(2)

f.write('</table></p>\n')

f.write('<p>Listan sammanställd av <a href="https://www.akehedman.se/">Åke Hedman</a></p>')

f.write('</body></html>\n') 
f.close()
con.close()
