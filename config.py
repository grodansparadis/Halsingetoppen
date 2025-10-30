# Hälsingetoppen Web Admin Configuration

# Database configuration
DATABASE_PATH = 'toppen.sqlite3'

# Flask configuration
SECRET_KEY = 'change-this-to-a-random-secret-key-in-production'
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000

# Spotify API credentials (set these as environment variables)
# SPOTIPY_CLIENT_ID = 'your_spotify_client_id'
# SPOTIPY_CLIENT_SECRET = 'your_spotify_client_secret'

# Application settings
ITEMS_PER_PAGE = 50
MAX_SEARCH_RESULTS = 100