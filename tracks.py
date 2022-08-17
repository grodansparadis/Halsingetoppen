# https://spotipy.readthedocs.io/en/master/
# https://stackoverflow.com/questions/60958514/spotify-api-authorization-to-create-a-playlist
# https://medium.com/@ethanj129/building-a-cli-spotify-playlist-generator-using-python-spotipy-3b32b63a25da

# usage: python tracks.py userid

import datetime
import sys
import time
import sqlite3
import spotipy
import spotipy.util as util
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

urn = 'spotify:artist:2FympPk5bcBe37Sp4VIs4L' # Casper the Ghost

if len(sys.argv) > 1:
  username = sys.argv[1]
else:
  print("Usage: %s username" % (sys.argv[0],))
  sys.exit()

token = util.prompt_for_user_token(
    username=username,
    scope='playlist-modify-public',     
    redirect_uri="http://localhost:8888/callback"
)
sp = spotipy.Spotify(auth=token)

scope = 'playlist-modify-public'
try:
  list_name = 'Hälsingetoppen-' + datetime.datetime.now().strftime("%b %d %Y")
  pp = sp.user_playlist_create(username, list_name, public=True, collaborative=False, description='En publik spellista baserad på Hälsingetoppen - http://www.hälsingetoppen.online')
except:
  print("* * * * * * * ------> Failed to create playlist " + list_name)
  sys.exit()

# List users public playlists
# playlists = sp.user_playlists(username)
# while playlists:
#   for i, playlist in enumerate(playlists['items']):
#       print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
#   if playlists['next']:
#       playlists = sp.next(playlists)
#   else:
#       playlists = None

con = sqlite3.connect('toppen.sqlite3')

#for album in albums:
#  print(album['name'])

cur = con.cursor()
cur_write = con.cursor()

# Remove all enteries from table tracks
try:
  cur_write.execute("delete from tracks;")  
  con.commit()
except:
  print("* * * * * * * Failed to remove all tracks ")

for row in cur.execute('SELECT * FROM artists ORDER BY id'):
  
  # Get artist id
  urn = row[TBL_ID]

  try:
     artist = sp.artist(urn)
  except:
     print("* * * * * * * ------>",urn,"Not found")
     continue
  
  # Get top tracks for artist
  try:
    tracks = sp.artist_top_tracks(urn)
  except:
    print("* * * * * * * ------>",urn,"Not found",artist['name'])
    continue

  #print(pp)  

  track_add_lst = []
  for item in tracks['tracks']:
    # Fix invalid JSON
    #print(item)
    #if item['position'] == "'position': None":
    #  item['position'] = 0
    #print(item['popularity'], item['name'], item['album']['album_type'], item['album']['release_date'],  item['external_urls']['spotify'] ) 
    track_add_lst.append(item['id'])
    sqlstr = "insert into tracks (id, artist_id, name, popularity, album_type, url, release_date) values ("
    sqlstr += "'" + item['id'] + "',"
    sqlstr += "'" + artist['id'] + "',"
    # Remove special characters from name
    song = item['name']
    song = song.replace("\"","''")
    sqlstr += "\"" + song + " \","
    sqlstr += str(item['popularity']) + ","
    sqlstr += "'" + item['album']['album_type'] + "',"
    sqlstr += "'" + item['external_urls']['spotify'] + "',"
    sqlstr += "'" + item['album']['release_date'] + "'"
    sqlstr += ");"
    try:
      cur_write.execute(sqlstr)  
      con.commit()
    except:
      print("* * * * * * * Failed to add track to db", sqlstr)
      continue  

  # Add tracks to playlist
  try:
    sp.user_playlist_add_tracks(username, pp['id'], track_add_lst, position=None)
  except:
    print("* * * * * * * ------> Failed to add tracks to playlist " + list_name + " for " + artist['name'] + " - '" + item['name'] + "'")
    continue
    


# while artist['next']:
#   results = sp.next(results)
#   albums.extend(results['items'])

  # results = sp.artist_albums(urn, album_type='album,single')
  # albums = results['items']
  # while results['next']:
  #  results = sp.next(results)
  #  albums.extend(results['items'])