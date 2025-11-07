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
import logging
from spotipy.oauth2 import SpotifyClientCredentials

# Import our Spotify utilities
from spotify_utils import (
    safe_spotify_artist,
    safe_spotify_artist_top_tracks,
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

TOPPEN_ID = '7zXnbJOPoNFnQmp8JfiwZ4'

track_add_lst = []

if len(sys.argv) > 1:
  username = sys.argv[1]
else:
  print("Usage: %s username" % (sys.argv[0],))
  sys.exit()

token = util.prompt_for_user_token(
    username=username,
    scope='playlist-modify-private',     
    redirect_uri="http://localhost:8888/callback"
)
sp = spotipy.Spotify(auth=token)

# Remove all tracks from playlist
try:
  sp.playlist_replace_items(TOPPEN_ID, track_add_lst)
except:
  print("Failed to remove old list items!")
  exit()

scope = 'playlist-modify-public'
try:
  list_name = 'Hälsingetoppen-' + datetime.datetime.now().strftime("%b %d %Y")
  # pp = sp.user_playlist_create(username, list_name, public=True, collaborative=False, description='En publik spellista baserad på Hälsingetoppen - http://www.hälsingetoppen.online')
  # print("New list: ", pp)
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

# Remove all entries from table tracks
try:
  cur_write.execute("delete from tracks;")  
  con.commit()
except:
  print("* * * * * * * Failed to remove all tracks ")

for row in cur.execute('SELECT * FROM artists ORDER BY name,id'):
  
  # Get artist id
  urn = row[TBL_ID]

  # Use safe Spotify calls with retry handling
  artist = safe_spotify_artist(sp, urn)
  if not artist:
    logger.error(f"Failed to get artist data for URN: {urn}")
    continue
  
  # Get top tracks for artist
  tracks = safe_spotify_artist_top_tracks(sp, urn)
  if not tracks:
    logger.error(f"Failed to get top tracks for {artist['name']} (URN: {urn})")
    continue

  if (len(tracks['tracks']) == 0):
    continue

  track_add_lst = []
  for item in tracks['tracks']:
    #print(item['popularity'], item['name'], item['album']['album_type'], item['album']['release_date'],  item['external_urls']['spotify'] ) 
    if not(item is None):
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
    except sqlite3.Error as er:
      print("* * * * * * * Failed to add track to db", sqlstr)
      print('SQLite error: %s' % (' '.join(er.args)))
      print("Exception class is: ", er.__class__)
      continue

  # Add tracks to playlist -  pp['id']
  if (len(track_add_lst) > 0):
    try:
      sp.user_playlist_add_tracks(username, TOPPEN_ID, track_add_lst, position=None)
    except:
      print("* * * * * * * ------> Failed to add tracks to playlist " + list_name + " for " + artist['name'] + " - '" + item['name'] + "'")
      #print(pp['id'])
      print(track_add_lst, len(track_add_lst))
      continue

  # Add rate limiting delay between artists
  rate_limit_delay()

# try:
#   print(track_add_lst)
#   sp.playlist_replace_items(TOPPEN_ID, track_add_lst)
# except:
#   print("* * * * * * * ------> Failed to add tracks to playlist ")
      
