#!/usr/bin/env python3
"""
Hälsingetoppen Web Admin Interface
A Flask-based web interface for managing the artists and tracks database.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime, date
import os
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a random secret key

# Database path
DB_PATH = 'toppen.sqlite3'

# Initialize Spotify client
sp = None
try:
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
except:
    print("Warning: Spotify credentials not configured. Some features may not work.")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_db_connection()
    
    # Create artists table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS "artists" (
            "id"    TEXT UNIQUE,
            "link_to_area"  INTEGER,
            "name"  TEXT,
            "popularity"    INTEGER,
            "followers"     INTEGER,
            "link"  TEXT,
            "picture_small" TEXT,
            "picture_large" INTEGER,
            "bInactivate"   INTEGER,
            "notes" INTEGER
        )
    ''')
    
    # Create tracks table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS "tracks" (
            "id"    TEXT,
            "artist_id"     TEXT,
            "name"  TEXT,
            "popularity"    INTEGER,
            "album_type"    TEXT,
            "url"   TEXT,
            "release_date"  TEXT,
            PRIMARY KEY("id")
        )
    ''')
    
    # Create area table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS "area" (
            "id"    INTEGER UNIQUE,
            "Name"  TEXT,
            PRIMARY KEY("id" AUTOINCREMENT)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Main dashboard"""
    conn = get_db_connection()
    
    # Get statistics
    artist_count = conn.execute('SELECT COUNT(*) FROM artists').fetchone()[0]
    track_count = conn.execute('SELECT COUNT(*) FROM tracks').fetchone()[0]
    active_artists = conn.execute('SELECT COUNT(*) FROM artists WHERE bInactivate = 0 OR bInactivate IS NULL').fetchone()[0]
    
    # Get recent additions
    recent_artists = conn.execute('''
        SELECT id, name, popularity, followers 
        FROM artists 
        ORDER BY ROWID DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         artist_count=artist_count,
                         track_count=track_count,
                         active_artists=active_artists,
                         recent_artists=recent_artists)

@app.route('/artists')
def artists():
    """List all artists"""
    conn = get_db_connection()
    
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    show_inactive = request.args.get('show_inactive', 'false') == 'true'
    sort_by = request.args.get('sort', 'popularity')
    order = request.args.get('order', 'desc')
    
    # Build query
    query = 'SELECT * FROM artists WHERE 1=1'
    params = []
    
    if search:
        query += ' AND name LIKE ? COLLATE NOCASE'
        params.append(f'%{search}%')
    
    if not show_inactive:
        query += ' AND (bInactivate = 0 OR bInactivate IS NULL)'
    
    # Add sorting
    if sort_by in ['name', 'popularity', 'followers']:
        query += f' ORDER BY {sort_by} {order.upper()}'
    
    artists_list = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('artists.html', 
                         artists=artists_list,
                         search=search,
                         show_inactive=show_inactive,
                         sort_by=sort_by,
                         order=order)

@app.route('/artist/<artist_id>')
def artist_detail(artist_id):
    """Show artist details"""
    conn = get_db_connection()
    
    artist = conn.execute('SELECT * FROM artists WHERE id = ?', [artist_id]).fetchone()
    if not artist:
        flash('Artist not found', 'error')
        return redirect(url_for('artists'))
    
    # Get artist's tracks
    tracks = conn.execute('''
        SELECT * FROM tracks 
        WHERE artist_id = ? 
        ORDER BY popularity DESC
    ''', [artist_id]).fetchall()
    
    conn.close()
    
    return render_template('artist_detail.html', artist=artist, tracks=tracks)

@app.route('/artist/add', methods=['GET', 'POST'])
def add_artist():
    """Add new artist"""
    if request.method == 'POST':
        spotify_url = request.form.get('spotify_url', '').strip()
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('Artist name is required', 'error')
            return render_template('add_artist.html')
        
        # Extract Spotify ID from URL if provided
        artist_id = None
        if spotify_url:
            if 'spotify:artist:' in spotify_url:
                artist_id = spotify_url.split('spotify:artist:')[1]
            elif 'open.spotify.com/artist/' in spotify_url:
                artist_id = spotify_url.split('open.spotify.com/artist/')[1].split('?')[0]
        
        # If we have Spotify integration and an ID, fetch data from Spotify
        spotify_data = {}
        if sp and artist_id:
            try:
                artist_info = sp.artist(artist_id)
                spotify_data = {
                    'name': artist_info['name'],
                    'popularity': artist_info['popularity'],
                    'followers': artist_info['followers']['total'],
                    'link': artist_info['external_urls']['spotify'],
                    'picture_small': artist_info['images'][0]['url'] if artist_info['images'] else '',
                }
                # Use Spotify data if we have it
                name = spotify_data['name']
            except Exception as e:
                flash(f'Could not fetch Spotify data: {e}', 'warning')
        
        # Generate a simple ID if no Spotify ID
        if not artist_id:
            import uuid
            artist_id = f'local:{uuid.uuid4().hex[:16]}'
        
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO artists (id, name, popularity, followers, link, picture_small, bInactivate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', [
                artist_id,
                name,
                spotify_data.get('popularity', 0),
                spotify_data.get('followers', 0),
                spotify_data.get('link', spotify_url),
                spotify_data.get('picture_small', ''),
                0
            ])
            conn.commit()
            conn.close()
            
            flash(f'Artist "{name}" added successfully!', 'success')
            return redirect(url_for('artist_detail', artist_id=artist_id))
            
        except sqlite3.IntegrityError:
            flash('An artist with this ID already exists', 'error')
        except Exception as e:
            flash(f'Error adding artist: {e}', 'error')
    
    return render_template('add_artist.html')

@app.route('/artist/<artist_id>/edit', methods=['GET', 'POST'])
def edit_artist(artist_id):
    """Edit artist"""
    conn = get_db_connection()
    artist = conn.execute('SELECT * FROM artists WHERE id = ?', [artist_id]).fetchone()
    
    if not artist:
        flash('Artist not found', 'error')
        return redirect(url_for('artists'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        popularity = int(request.form.get('popularity', 0) or 0)
        followers = int(request.form.get('followers', 0) or 0)
        link = request.form.get('link', '').strip()
        picture_small = request.form.get('picture_small', '').strip()
        inactive = 1 if request.form.get('inactive') else 0
        
        if not name:
            flash('Artist name is required', 'error')
            return render_template('edit_artist.html', artist=artist)
        
        try:
            conn.execute('''
                UPDATE artists 
                SET name = ?, popularity = ?, followers = ?, link = ?, 
                    picture_small = ?, bInactivate = ?
                WHERE id = ?
            ''', [name, popularity, followers, link, picture_small, inactive, artist_id])
            conn.commit()
            
            flash(f'Artist "{name}" updated successfully!', 'success')
            return redirect(url_for('artist_detail', artist_id=artist_id))
            
        except Exception as e:
            flash(f'Error updating artist: {e}', 'error')
    
    conn.close()
    return render_template('edit_artist.html', artist=artist)

@app.route('/artist/<artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):
    """Delete artist"""
    conn = get_db_connection()
    
    # Check if artist exists
    artist = conn.execute('SELECT name FROM artists WHERE id = ?', [artist_id]).fetchone()
    if not artist:
        flash('Artist not found', 'error')
        return redirect(url_for('artists'))
    
    try:
        # Delete associated tracks first
        conn.execute('DELETE FROM tracks WHERE artist_id = ?', [artist_id])
        # Delete artist
        conn.execute('DELETE FROM artists WHERE id = ?', [artist_id])
        conn.commit()
        
        flash(f'Artist "{artist[0]}" and associated tracks deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting artist: {e}', 'error')
    
    conn.close()
    return redirect(url_for('artists'))

@app.route('/tracks')
def tracks():
    """List all tracks"""
    conn = get_db_connection()
    
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    artist_filter = request.args.get('artist', '').strip()
    sort_by = request.args.get('sort', 'popularity')
    order = request.args.get('order', 'desc')
    
    # Build query with JOIN to get artist name
    query = '''
        SELECT t.*, a.name as artist_name 
        FROM tracks t 
        LEFT JOIN artists a ON t.artist_id = a.id 
        WHERE 1=1
    '''
    params = []
    
    if search:
        query += ' AND (t.name LIKE ? COLLATE NOCASE OR a.name LIKE ? COLLATE NOCASE)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    if artist_filter:
        query += ' AND a.name LIKE ? COLLATE NOCASE'
        params.append(f'%{artist_filter}%')
    
    # Add sorting
    if sort_by in ['name', 'popularity', 'release_date', 'artist_name']:
        if sort_by == 'artist_name':
            query += f' ORDER BY a.name {order.upper()}'
        else:
            query += f' ORDER BY t.{sort_by} {order.upper()}'
    
    tracks_list = conn.execute(query, params).fetchall()
    
    # Get all artists for filter dropdown
    artists_list = conn.execute('SELECT DISTINCT name FROM artists ORDER BY name').fetchall()
    
    conn.close()
    
    return render_template('tracks.html', 
                         tracks=tracks_list,
                         artists=artists_list,
                         search=search,
                         artist_filter=artist_filter,
                         sort_by=sort_by,
                         order=order)

@app.route('/track/<track_id>/edit', methods=['GET', 'POST'])
def edit_track(track_id):
    """Edit track"""
    conn = get_db_connection()
    
    # Get track with artist info
    track = conn.execute('''
        SELECT t.*, a.name as artist_name 
        FROM tracks t 
        LEFT JOIN artists a ON t.artist_id = a.id 
        WHERE t.id = ?
    ''', [track_id]).fetchone()
    
    if not track:
        flash('Track not found', 'error')
        return redirect(url_for('tracks'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        popularity = int(request.form.get('popularity', 0) or 0)
        album_type = request.form.get('album_type', '').strip()
        url = request.form.get('url', '').strip()
        release_date = request.form.get('release_date', '').strip()
        
        if not name:
            flash('Track name is required', 'error')
            return render_template('edit_track.html', track=track)
        
        try:
            conn.execute('''
                UPDATE tracks 
                SET name = ?, popularity = ?, album_type = ?, url = ?, release_date = ?
                WHERE id = ?
            ''', [name, popularity, album_type, url, release_date, track_id])
            conn.commit()
            
            flash(f'Track "{name}" updated successfully!', 'success')
            return redirect(url_for('tracks'))
            
        except Exception as e:
            flash(f'Error updating track: {e}', 'error')
    
    conn.close()
    return render_template('edit_track.html', track=track)

@app.route('/track/<track_id>/delete', methods=['POST'])
def delete_track(track_id):
    """Delete track"""
    conn = get_db_connection()
    
    # Check if track exists
    track = conn.execute('SELECT name FROM tracks WHERE id = ?', [track_id]).fetchone()
    if not track:
        flash('Track not found', 'error')
        return redirect(url_for('tracks'))
    
    try:
        conn.execute('DELETE FROM tracks WHERE id = ?', [track_id])
        conn.commit()
        
        flash(f'Track "{track[0]}" deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting track: {e}', 'error')
    
    conn.close()
    return redirect(url_for('tracks'))

@app.route('/api/search_spotify')
def search_spotify():
    """Search Spotify for artists"""
    if not sp:
        return jsonify({'error': 'Spotify not configured'}), 500
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})
    
    try:
        # Spotify search is already case insensitive
        results = sp.search(q=query, type='artist', limit=10)
        artists = []
        
        for artist in results['artists']['items']:
            artists.append({
                'id': artist['id'],
                'name': artist['name'],
                'popularity': artist['popularity'],
                'followers': artist['followers']['total'],
                'url': artist['external_urls']['spotify'],
                'image': artist['images'][0]['url'] if artist['images'] else None
            })
        
        return jsonify({'results': artists})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate')
def generate_menu():
    """Show generation menu"""
    return render_template('generate_menu.html')

@app.route('/generate/toplist', methods=['GET', 'POST'])
def generate_toplist():
    """Generate HTML toplist (same as ht.py)"""
    if request.method == 'POST':
        update_spotify = request.form.get('update_spotify') == 'on'
        
        try:
            # Update artist data from Spotify if requested
            if update_spotify and sp:
                conn = get_db_connection()
                cur = conn.cursor()
                
                update_count = 0
                for row in cur.execute('SELECT * FROM artists ORDER BY id'):
                    urn = row['id']
                    try:
                        artist = sp.artist(urn)
                        print(f"Updating: {artist['name']}")
                        
                        if row['bInactivate'] != 0:
                            continue
                            
                        name = artist['name'].replace('"', "''")
                        popularity = artist['popularity']
                        followers = artist['followers']['total']
                        link = artist['external_urls']['spotify']
                        picture_small = ""
                        picture_large = ""
                        
                        if len(artist['images']) > 0:
                            picture_large = artist['images'][0]['url']
                        if len(artist['images']) > 1:
                            picture_small = artist['images'][1]['url']
                        
                        conn.execute('''
                            UPDATE artists 
                            SET name = ?, popularity = ?, followers = ?, link = ?, 
                                picture_small = ?, picture_large = ?
                            WHERE id = ?
                        ''', [name, popularity, followers, link, picture_small, picture_large, urn])
                        
                        update_count += 1
                        time.sleep(0.1)  # Rate limiting
                        
                    except Exception as e:
                        print(f"Error updating {urn}: {e}")
                        continue
                
                conn.commit()
                conn.close()
                flash(f'Updated {update_count} artists from Spotify', 'success')
            
            # Generate HTML file
            filename = generate_html_toplist()
            flash(f'HTML toplist generated: {filename}', 'success')
            
            return redirect(url_for('generate_toplist'))
            
        except Exception as e:
            flash(f'Error generating toplist: {e}', 'error')
    
    # Show form - get stats
    conn = get_db_connection()
    artist_count = conn.execute('SELECT COUNT(*) FROM artists').fetchone()[0]
    active_artists = conn.execute('SELECT COUNT(*) FROM artists WHERE bInactivate = 0 OR bInactivate IS NULL').fetchone()[0]
    conn.close()
    
    return render_template('generate_toplist.html', 
                         artist_count=artist_count,
                         active_artists=active_artists,
                         spotify_configured=sp is not None)

@app.route('/generate/songs', methods=['POST'])
def generate_songs():
    """Generate HTML songs list (same as topp_songs.py)"""
    try:
        filename = generate_html_songs()
        flash(f'HTML songs list generated: {filename}', 'success')
    except Exception as e:
        flash(f'Error generating songs list: {e}', 'error')
    
    return redirect(url_for('generate_menu'))

@app.route('/sync/tracks', methods=['GET', 'POST'])
def sync_tracks():
    """Sync tracks from Spotify (same as tracks.py)"""
    if request.method == 'POST':
        update_playlist = request.form.get('update_playlist') == 'on'
        
        try:
            if not sp:
                flash('Spotify not configured', 'error')
                return redirect(url_for('sync_tracks'))
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Clear existing tracks
            conn.execute('DELETE FROM tracks')
            conn.commit()
            
            track_count = 0
            error_count = 0
            
            for row in cur.execute('SELECT * FROM artists ORDER BY name, id'):
                urn = row['id']
                
                try:
                    artist = sp.artist(urn)
                    tracks = sp.artist_top_tracks(urn)
                    
                    if len(tracks['tracks']) == 0:
                        continue
                    
                    for item in tracks['tracks']:
                        song = item['name'].replace('"', "''")
                        
                        conn.execute('''
                            INSERT INTO tracks (id, artist_id, name, popularity, album_type, url, release_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', [
                            item['id'],
                            artist['id'], 
                            song,
                            item['popularity'],
                            item['album']['album_type'],
                            item['external_urls']['spotify'],
                            item['album']['release_date']
                        ])
                        track_count += 1
                    
                    conn.commit()
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error syncing tracks for {urn}: {e}")
                    error_count += 1
                    continue
            
            conn.close()
            
            flash(f'Synced {track_count} tracks from Spotify. {error_count} errors.', 'success')
            
        except Exception as e:
            flash(f'Error syncing tracks: {e}', 'error')
        
        return redirect(url_for('sync_tracks'))
    
    # Show form - get stats
    conn = get_db_connection()
    artist_count = conn.execute('SELECT COUNT(*) FROM artists').fetchone()[0]
    track_count = conn.execute('SELECT COUNT(*) FROM tracks').fetchone()[0]
    estimated_time = max(1, artist_count // 10)  # Rough estimate
    conn.close()
    
    return render_template('sync_tracks.html',
                         artist_count=artist_count,
                         track_count=track_count,
                         estimated_time=estimated_time,
                         spotify_configured=sp is not None)

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated files"""
    if filename in ['topplista.html', 'songs.html'] and os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    flash('File not found', 'error')
    return redirect(url_for('generate_menu'))

def generate_html_toplist():
    """Generate modern, interactive HTML toplist file"""
    filename = f'topplista-{date.today()}.html'
    
    conn = get_db_connection()
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f'''<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hälsingetoppen - Topplista {date.today()}</title>
    
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=UA-69888-1"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag("js", new Date());
        gtag("config", "UA-69888-1");
    </script>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <!-- DataTables CSS -->
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .main-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin: 2rem auto;
            padding: 2rem;
        }}
        
        .header-section {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
            background: linear-gradient(135deg, #ff6b6b, #feca57);
            border-radius: 15px;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .artist-card {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
            overflow: hidden;
            margin-bottom: 1rem;
        }}
        
        .artist-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .position-badge {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-weight: bold;
            font-size: 1.2rem;
            padding: 0.8rem;
            text-align: center;
            min-width: 60px;
        }}
        
        .artist-image {{
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #fff;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        
        .artist-info {{
            flex-grow: 1;
            padding: 1rem;
        }}
        
        .artist-name {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            text-decoration: none;
        }}
        
        .artist-name:hover {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .stats-container {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            background: linear-gradient(135deg, #74b9ff, #0984e3);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-size: 0.9rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .popularity-stat {{ background: linear-gradient(135deg, #fd79a8, #e84393); }}
        .followers-stat {{ background: linear-gradient(135deg, #fdcb6e, #e17055); }}
        
        .controls-section {{
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .search-box {{
            border: 2px solid #e9ecef;
            border-radius: 25px;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .search-box:focus {{
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }}
        
        .btn-custom {{
            border-radius: 25px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
        }}
        
        .btn-sort {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        .btn-sort:hover {{
            background: linear-gradient(135deg, #764ba2, #667eea);
            transform: translateY(-2px);
            color: white;
        }}
        
        .btn-sort:active,
        .btn-sort.touching {{
            transform: translateY(0) scale(0.95);
        }}
        
        /* Touch-friendly improvements */
        @media (hover: none) and (pointer: coarse) {{
            .btn {{
                min-height: 44px;
                padding: 0.75rem 1rem;
            }}
            
            .artist-card {{
                cursor: default;
            }}
            
            .search-box {{
                min-height: 44px;
                font-size: 16px; /* Prevents zoom on iOS */
            }}
        }}
        
        /* Prevent text selection on touch devices */
        .btn, .artist-card {{
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }}
        
        /* Better touch feedback */
        .artist-card:active {{
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }}

        .btn-sort.active {{
            background: linear-gradient(135deg, #fd79a8, #e84393);
        }}

        .footer-section {{
            text-align: center;
            margin-top: 3rem;
            padding: 2rem;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
        }}
        
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }}
        
        .loading-spinner {{
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        @media (max-width: 768px) {{
            .main-container {{ 
                margin: 0.5rem; 
                padding: 0.5rem; 
            }}
            .artist-card {{ 
                margin-bottom: 0.5rem; 
                padding: 0.75rem;
            }}
            .stats-container {{ 
                flex-direction: column; 
                gap: 0.5rem;
            }}
            .stat-item {{
                font-size: 0.9rem;
                padding: 0.4rem 0.8rem;
            }}
            .artist-name {{
                font-size: 1.1rem;
                line-height: 1.3;
            }}
            .artist-image {{
                width: 50px;
                height: 50px;
            }}
            .position-badge {{
                width: 35px;
                height: 35px;
                font-size: 0.9rem;
            }}
            .btn {{
                font-size: 0.9rem;
                padding: 0.5rem 1rem;
            }}
            .search-container {{
                margin-bottom: 1rem;
            }}
            .search-container input {{
                font-size: 1rem;
                padding: 0.75rem;
            }}
            .alert {{
                font-size: 0.9rem;
                padding: 1rem;
            }}
            .header-section h1 {{
                font-size: 1.8rem;
            }}
            .header-section h2 {{
                font-size: 1.3rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .main-container {{ 
                margin: 0.25rem; 
                padding: 0.25rem; 
            }}
            .artist-card {{
                padding: 0.5rem;
            }}
            .artist-name {{
                font-size: 1rem;
            }}
            .artist-image {{
                width: 40px;
                height: 40px;
            }}
            .position-badge {{
                width: 30px;
                height: 30px;
                font-size: 0.8rem;
            }}
            .stats-container {{
                gap: 0.25rem;
            }}
            .stat-item {{
                font-size: 0.8rem;
                padding: 0.3rem 0.6rem;
            }}
            .btn {{
                font-size: 0.8rem;
                padding: 0.4rem 0.8rem;
            }}
            .header-section h1 {{
                font-size: 1.5rem;
            }}
            .header-section h2 {{
                font-size: 1.1rem;
            }}
            .col-12 .btn {{
                margin-bottom: 0.5rem;
                display: block;
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-spinner"></div>
    </div>

    <div class="container-fluid">
        <div class="main-container">
            <!-- Header -->
            <div class="header-section">
                <h1><i class="fas fa-trophy me-3"></i>Hälsingetoppen</h1>
                <h2>Topplista {date.today()}</h2>
                <p class="mb-0">De populäraste artisterna från Hälsingland</p>
            </div>

            <!-- Description -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="alert alert-info">
                        <h5><i class="fas fa-info-circle me-2"></i>Om topplistan</h5>
                        <p class="mb-2">Topplista med artister från Hälsingland baserad på Spotifys 
                        <a href="https://community.spotify.com/t5/Content-Questions/Artist-popularity/td-p/4415259" target="_blank">popularitets index (0-100)</a> 
                        som är konstruerat utifrån hur mycket en artists alla låtar är spelade över tid.</p>
                        
                        <p class="mb-2">Artister som har samma popularitet är i sin tur ordnade i antal följare. 
                        Vill du att din favoritartist skall komma högre upp på den här listan så följ artisten och 
                        spela artistens musik. Svårare än så är det inte.</p>
                        
                        <p class="mb-0">Artisterna som är med har någon form av koppling till Hälsingland. 
                        Saknar du en artist? Skicka artistens Spotifylänk till 
                        <a href="mailto:akhe@grodansparadis.com">akhe@grodansparadis.com</a> 
                        och tala om vilken koppling artisten har till Hälsingland.</p>
                    </div>
                </div>
            </div>

            <!-- Navigation Links -->
            <div class="row mb-4">
                <div class="col-12 text-center">
                    <a href="songs.html" class="btn btn-custom btn-sort me-2">
                        <i class="fas fa-music me-2"></i>Visa alla låtar
                    </a>
                    <a href="https://open.spotify.com/playlist/7zXnbJOPoNFnQmp8JfiwZ4" target="_blank" class="btn btn-custom btn-sort">
                        <i class="fab fa-spotify me-2"></i>Spotify Spellista
                    </a>
                </div>
            </div>

            <!-- Controls -->
            <div class="controls-section">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <div class="input-group">
                            <span class="input-group-text"><i class="fas fa-search"></i></span>
                            <input type="text" class="form-control search-box" id="searchInput" placeholder="Sök artist...">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="btn-group w-100" role="group">
                            <button type="button" class="btn btn-custom btn-sort active" data-sort="position">
                                <i class="fas fa-trophy me-1"></i>Position
                            </button>
                            <button type="button" class="btn btn-custom btn-sort" data-sort="name">
                                <i class="fas fa-sort-alpha-up me-1"></i>Namn
                            </button>
                            <button type="button" class="btn btn-custom btn-sort" data-sort="popularity">
                                <i class="fas fa-fire me-1"></i>Popularitet
                            </button>
                            <button type="button" class="btn btn-custom btn-sort" data-sort="followers">
                                <i class="fas fa-users me-1"></i>Följare
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Artists List -->
            <div id="artistsList">
''')
        
        cnt = 1
        for row in conn.execute('SELECT * FROM artists WHERE bInactivate = 0 OR bInactivate IS NULL ORDER BY popularity DESC, followers DESC'):
            if sp:
                try:
                    artist = sp.artist(row['id'])
                    name = artist['name']
                    popularity = artist['popularity']
                    followers = artist['followers']['total']
                    spotify_url = artist['external_urls']['spotify']
                    image_url = artist['images'][0]['url'] if len(artist['images']) > 0 else ''
                except:
                    # Fallback to database data
                    name = row['name']
                    popularity = row['popularity'] or 0
                    followers = row['followers'] or 0
                    spotify_url = row['link'] or '#'
                    image_url = row['picture_small'] or ''
            else:
                # Use database data
                name = row['name']
                popularity = row['popularity'] or 0
                followers = row['followers'] or 0
                spotify_url = row['link'] or '#'
                image_url = row['picture_small'] or ''
            
            f.write(f'''                <div class="artist-card" data-position="{cnt}" data-name="{name.lower()}" data-popularity="{popularity}" data-followers="{followers}">
                    <div class="d-flex align-items-center">
                        <div class="position-badge">
                            <span class="position-number">#{cnt}</span>
                        </div>
                        <div class="p-3">
                            {f'<img src="{image_url}" alt="{name}" class="artist-image">' if image_url else f'<div class="artist-image bg-light d-flex align-items-center justify-content-center"><i class="fas fa-user fa-2x text-muted"></i></div>'}
                        </div>
                        <div class="artist-info">
                            <a href="{spotify_url}" target="_blank" class="artist-name">
                                <i class="fab fa-spotify me-2"></i>{name}
                            </a>
                            <div class="stats-container">
                                <div class="stat-item popularity-stat">
                                    <i class="fas fa-fire"></i>
                                    <span>{popularity}% popularitet</span>
                                </div>
                                <div class="stat-item followers-stat">
                                    <i class="fas fa-users"></i>
                                    <span>{followers:,} följare</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
''')
            cnt += 1
        
        f.write(f'''            </div>

            <!-- Footer -->
            <div class="footer-section">
                <p class="mb-2"><strong>Listan uppdateras varje fredag</strong></p>
                <p class="mb-0">Listan sammanställd av <a href="https://www.akehedman.se/" target="_blank">Åke Hedman</a></p>
                <p class="small text-muted mt-2">Genererad {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Application state
        let currentSort = 'position';
        let sortDirection = 'asc';
        let artists = [];

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            initializeArtists();
            setupEventListeners();
            hideLoading();
        }});

        function showLoading() {{
            document.getElementById('loadingOverlay').style.display = 'flex';
        }}

        function hideLoading() {{
            document.getElementById('loadingOverlay').style.display = 'none';
        }}

        function initializeArtists() {{
            const artistCards = document.querySelectorAll('.artist-card');
            artists = Array.from(artistCards).map(card => ({{
                element: card,
                position: parseInt(card.dataset.position),
                name: card.dataset.name,
                popularity: parseInt(card.dataset.popularity),
                followers: parseInt(card.dataset.followers)
            }}));
        }}

        function setupEventListeners() {{
            // Search functionality
            const searchInput = document.getElementById('searchInput');
            searchInput.addEventListener('input', handleSearch);

            // Sort buttons
            const sortButtons = document.querySelectorAll('[data-sort]');
            sortButtons.forEach(button => {{
                button.addEventListener('click', handleSort);
            }});
        }}

        function handleSearch(e) {{
            const searchTerm = e.target.value.toLowerCase();
            
            artists.forEach(artist => {{
                const shouldShow = artist.name.includes(searchTerm);
                artist.element.style.display = shouldShow ? 'block' : 'none';
            }});

            updatePositionNumbers();
        }}

        function handleSort(e) {{
            showLoading();
            
            const sortType = e.target.closest('[data-sort]').dataset.sort;
            
            // Update active button
            document.querySelectorAll('[data-sort]').forEach(btn => btn.classList.remove('active'));
            e.target.closest('[data-sort]').classList.add('active');
            
            // Toggle direction if same sort
            if (currentSort === sortType) {{
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            }} else {{
                sortDirection = sortType === 'name' ? 'asc' : 'desc';
            }}
            
            currentSort = sortType;
            
            setTimeout(() => {{
                sortArtists(sortType, sortDirection);
                hideLoading();
            }}, 100);
        }}

        function sortArtists(sortBy, direction) {{
            const visibleArtists = artists.filter(artist => 
                artist.element.style.display !== 'none'
            );

            visibleArtists.sort((a, b) => {{
                let aVal, bVal;
                
                switch(sortBy) {{
                    case 'name':
                        aVal = a.name;
                        bVal = b.name;
                        break;
                    case 'popularity':
                        aVal = a.popularity;
                        bVal = b.popularity;
                        break;
                    case 'followers':
                        aVal = a.followers;
                        bVal = b.followers;
                        break;
                    default: // position
                        aVal = a.position;
                        bVal = b.position;
                }}

                if (typeof aVal === 'string') {{
                    return direction === 'asc' ? 
                        aVal.localeCompare(bVal, 'sv') : 
                        bVal.localeCompare(aVal, 'sv');
                }} else {{
                    return direction === 'asc' ? aVal - bVal : bVal - aVal;
                }}
            }});

            // Re-arrange DOM elements
            const container = document.getElementById('artistsList');
            visibleArtists.forEach(artist => {{
                container.appendChild(artist.element);
            }});

            updatePositionNumbers();
        }}

        function updatePositionNumbers() {{
            const visibleCards = Array.from(document.querySelectorAll('.artist-card'))
                .filter(card => card.style.display !== 'none');
            
            visibleCards.forEach((card, index) => {{
                const positionElement = card.querySelector('.position-number');
                positionElement.textContent = `#${{index + 1}}`;
            }});
        }}

        // Smooth scrolling for internal links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});

        // Add loading animation to external links
        document.querySelectorAll('a[target="_blank"]').forEach(link => {{
            link.addEventListener('click', function() {{
                showLoading();
                setTimeout(hideLoading, 2000);
            }});
        }});
    </script>
</body>
</html>''')
    
    conn.close()
    return filename

def generate_html_songs():
    """Generate modern, interactive HTML songs list file"""
    filename = 'songs.html'
    
    conn = get_db_connection()
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f'''<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Hälsingetoppen - Alla låtar</title>
    
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-SNRXECZNJX"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-SNRXECZNJX');
    </script>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        
        .main-container {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin: 2rem auto;
            padding: 2rem;
        }}
        
        .header-section {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
            background: linear-gradient(135deg, #55a3ff, #003d82);
            border-radius: 15px;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .song-card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: none;
            overflow: hidden;
            margin-bottom: 0.75rem;
        }}
        
        .song-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .song-info {{
            padding: 1rem;
        }}
        
        .song-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #2c3e50;
            text-decoration: none;
            display: block;
            margin-bottom: 0.5rem;
        }}
        
        .song-title:hover {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .artist-link {{
            color: #74b9ff;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .artist-link:hover {{
            color: #0984e3;
            text-decoration: underline;
        }}
        
        .song-meta {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 0.5rem;
        }}
        
        .meta-tag {{
            background: linear-gradient(135deg, #fd79a8, #e84393);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .meta-tag.album {{ background: linear-gradient(135deg, #fdcb6e, #e17055); }}
        .meta-tag.date {{ background: linear-gradient(135deg, #74b9ff, #0984e3); }}
        
        .controls-section {{
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .search-box {{
            border: 2px solid #e9ecef;
            border-radius: 25px;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .search-box:focus {{
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }}
        
        .btn-custom {{
            border-radius: 25px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
        }}
        
        .btn-sort {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        
        .btn-sort:hover {{
            background: linear-gradient(135deg, #764ba2, #667eea);
            transform: translateY(-2px);
            color: white;
        }}
        
        .btn-sort:active,
        .btn-sort.touching {{
            transform: translateY(0) scale(0.95);
        }}
        
        /* Touch-friendly improvements */
        @media (hover: none) and (pointer: coarse) {{
            .btn {{
                min-height: 44px;
                padding: 0.75rem 1rem;
            }}
            
            .song-card {{
                cursor: default;
            }}
            
            .search-box {{
                min-height: 44px;
                font-size: 16px; /* Prevents zoom on iOS */
            }}
        }}
        
        /* Prevent text selection on touch devices */
        .btn, .song-card {{
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
        }}
        
        /* Better touch feedback */
        .song-card:active {{
            transform: scale(0.98);
            transition: transform 0.1s ease;
        }}

        .btn-sort.active {{
            background: linear-gradient(135deg, #fd79a8, #e84393);
        }}

        .stats-section {{
            background: rgba(255,255,255,0.1);
            padding: 1rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
        }}
        
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }}
        
        .loading-spinner {{
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        @media (max-width: 768px) {{
            .main-container {{ 
                margin: 0.5rem; 
                padding: 0.5rem; 
            }}
            .song-card {{ 
                margin-bottom: 0.5rem; 
                padding: 0.75rem;
            }}
            .song-stats {{ 
                flex-direction: column; 
                gap: 0.5rem;
            }}
            .stat-item {{
                font-size: 0.9rem;
                padding: 0.4rem 0.8rem;
            }}
            .song-title {{
                font-size: 1.1rem;
                line-height: 1.3;
            }}
            .artist-name {{
                font-size: 0.95rem;
            }}
            .position-badge {{
                width: 35px;
                height: 35px;
                font-size: 0.9rem;
            }}
            .btn {{
                font-size: 0.9rem;
                padding: 0.5rem 1rem;
            }}
            .search-container {{
                margin-bottom: 1rem;
            }}
            .search-container input {{
                font-size: 1rem;
                padding: 0.75rem;
            }}
            .alert {{
                font-size: 0.9rem;
                padding: 1rem;
            }}
            .header-section h1 {{
                font-size: 1.8rem;
            }}
            .header-section h2 {{
                font-size: 1.3rem;
            }}
            .song-meta {{ 
                flex-direction: column; 
                gap: 0.5rem; 
            }}
        }}
        
        @media (max-width: 480px) {{
            .main-container {{ 
                margin: 0.25rem; 
                padding: 0.25rem; 
            }}
            .song-card {{
                padding: 0.5rem;
            }}
            .song-title {{
                font-size: 1rem;
            }}
            .artist-name {{
                font-size: 0.9rem;
            }}
            .position-badge {{
                width: 30px;
                height: 30px;
                font-size: 0.8rem;
            }}
            .song-stats {{
                gap: 0.25rem;
            }}
            .stat-item {{
                font-size: 0.8rem;
                padding: 0.3rem 0.6rem;
            }}
            .btn {{
                font-size: 0.8rem;
                padding: 0.4rem 0.8rem;
            }}
            .header-section h1 {{
                font-size: 1.5rem;
            }}
            .header-section h2 {{
                font-size: 1.1rem;
            }}
            .col-12 .btn {{
                margin-bottom: 0.5rem;
                display: block;
                width: 100%;
            }}
            .song-meta {{
                gap: 0.25rem;
            }}
            .meta-tag {{
                font-size: 0.7rem;
                padding: 0.2rem 0.6rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-spinner"></div>
    </div>

    <div class="container-fluid">
        <div class="main-container">
            <!-- Header -->
            <div class="header-section">
                <h1><i class="fas fa-music me-3"></i>Hälsingetoppen</h1>
                <h2>Mest lyssnade spår</h2>
                <p class="mb-0">Alla artisters populäraste låtar i alfabetisk ordning</p>
            </div>

            <!-- Description -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="alert alert-info">
                        <h5><i class="fas fa-info-circle me-2"></i>Om låtlistan</h5>
                        <p class="mb-2">Här listas topplistans alla artisters mest lyssnade spår (max tio spår per artist). 
                        Eftersom Spotify inte delar antal lysningar per låt listas låtarna i alfabetisk ordning.</p>
                        
                        <p class="mb-0">Spår som finns både som singel och i ett album listas separat om båda är bland de mest avlyssnade.</p>
                    </div>
                </div>
            </div>

            <!-- Navigation Links -->
            <div class="row mb-4">
                <div class="col-12 text-center">
                    <a href="topplista-{date.today()}.html" class="btn btn-custom btn-sort me-2">
                        <i class="fas fa-home me-2"></i>Tillbaka till topplistan
                    </a>
                    <a href="https://open.spotify.com/playlist/7zXnbJOPoNFnQmp8JfiwZ4" target="_blank" class="btn btn-custom btn-sort">
                        <i class="fab fa-spotify me-2"></i>Spotify Spellista
                    </a>
                </div>
            </div>

            <!-- Stats -->
            <div class="stats-section">
                <h5 id="songCount">Laddar låtar...</h5>
            </div>

            <!-- Controls -->
            <div class="controls-section">
                <div class="row align-items-center">
                    <div class="col-md-6">
                        <div class="input-group">
                            <span class="input-group-text"><i class="fas fa-search"></i></span>
                            <input type="text" class="form-control search-box" id="searchInput" placeholder="Sök låt eller artist...">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="btn-group w-100" role="group">
                            <button type="button" class="btn btn-custom btn-sort active" data-sort="song">
                                <i class="fas fa-music me-1"></i>Låt
                            </button>
                            <button type="button" class="btn btn-custom btn-sort" data-sort="artist">
                                <i class="fas fa-user me-1"></i>Artist
                            </button>
                            <button type="button" class="btn btn-custom btn-sort" data-sort="date">
                                <i class="fas fa-calendar me-1"></i>Datum
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Songs List -->
            <div id="songsList">
''')
        
        song_count = 0
        for row in conn.execute('''
            SELECT t.*, a.name as artist_name, a.link as artist_link
            FROM tracks t 
            LEFT JOIN artists a ON t.artist_id = a.id 
            ORDER BY t.name
        '''):
            album_type = row['album_type'] or 'Unknown'
            release_date = row['release_date'] or 'Unknown'
            artist_name = row['artist_name'] or 'Unknown Artist'
            
            f.write(f'''                <div class="song-card" data-song="{row['name'].lower()}" data-artist="{artist_name.lower()}" data-date="{release_date}">
                    <div class="song-info">
                        <a href="{row['url']}" target="_blank" class="song-title">
                            <i class="fab fa-spotify me-2"></i>{row['name']}
                        </a>
                        <div>
                            <span>av </span>
                            <a href="{row['artist_link'] or '#'}" target="_blank" class="artist-link">
                                {artist_name}
                            </a>
                        </div>
                        <div class="song-meta">
                            <span class="meta-tag album">{album_type}</span>
                            <span class="meta-tag date">{release_date}</span>
                        </div>
                    </div>
                </div>
''')
            song_count += 1
        
        f.write(f'''            </div>

            <!-- Footer -->
            <div class="text-center mt-4">
                <p class="mb-0">Listan sammanställd av <a href="https://www.akehedman.se/" target="_blank">Åke Hedman</a></p>
                <p class="small text-muted mt-2">Genererad {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Application state
        let currentSort = 'song';
        let sortDirection = 'asc';
        let songs = [];
        const totalSongs = {song_count};

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            initializeSongs();
            setupEventListeners();
            updateSongCount();
            hideLoading();
        }});

        function showLoading() {{
            document.getElementById('loadingOverlay').style.display = 'flex';
        }}

        function hideLoading() {{
            document.getElementById('loadingOverlay').style.display = 'none';
        }}

        function initializeSongs() {{
            const songCards = document.querySelectorAll('.song-card');
            songs = Array.from(songCards).map(card => ({{
                element: card,
                song: card.dataset.song,
                artist: card.dataset.artist,
                date: card.dataset.date
            }}));
        }}

        function setupEventListeners() {{
            // Search functionality
            const searchInput = document.getElementById('searchInput');
            searchInput.addEventListener('input', handleSearch);

            // Sort buttons
            const sortButtons = document.querySelectorAll('[data-sort]');
            sortButtons.forEach(button => {{
                button.addEventListener('click', handleSort);
            }});
        }}

        function handleSearch(e) {{
            const searchTerm = e.target.value.toLowerCase();
            let visibleCount = 0;
            
            songs.forEach(song => {{
                const shouldShow = song.song.includes(searchTerm) || song.artist.includes(searchTerm);
                song.element.style.display = shouldShow ? 'block' : 'none';
                if (shouldShow) visibleCount++;
            }});

            updateSongCount(visibleCount);
        }}

        function handleSort(e) {{
            showLoading();
            
            const sortType = e.target.closest('[data-sort]').dataset.sort;
            
            // Update active button
            document.querySelectorAll('[data-sort]').forEach(btn => btn.classList.remove('active'));
            e.target.closest('[data-sort]').classList.add('active');
            
            // Toggle direction if same sort
            if (currentSort === sortType) {{
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            }} else {{
                sortDirection = 'asc';
            }}
            
            currentSort = sortType;
            
            setTimeout(() => {{
                sortSongs(sortType, sortDirection);
                hideLoading();
            }}, 100);
        }}

        function sortSongs(sortBy, direction) {{
            const visibleSongs = songs.filter(song => 
                song.element.style.display !== 'none'
            );

            visibleSongs.sort((a, b) => {{
                let aVal, bVal;
                
                switch(sortBy) {{
                    case 'artist':
                        aVal = a.artist;
                        bVal = b.artist;
                        break;
                    case 'date':
                        aVal = a.date;
                        bVal = b.date;
                        break;
                    default: // song
                        aVal = a.song;
                        bVal = b.song;
                }}

                return direction === 'asc' ? 
                    aVal.localeCompare(bVal, 'sv') : 
                    bVal.localeCompare(aVal, 'sv');
            }});

            // Re-arrange DOM elements
            const container = document.getElementById('songsList');
            visibleSongs.forEach(song => {{
                container.appendChild(song.element);
            }});
        }}

        function updateSongCount(visible = null) {{
            const count = visible !== null ? visible : totalSongs;
            const text = visible !== null ? 
                `Visar ${{count}} av ${{totalSongs}} låtar` : 
                `${{totalSongs}} låtar totalt`;
            
            document.getElementById('songCount').textContent = text;
        }}

        // Add loading animation to external links
        document.querySelectorAll('a[target="_blank"]').forEach(link => {{
            link.addEventListener('click', function() {{
                showLoading();
                setTimeout(hideLoading, 2000);
            }});
        }});
    </script>
</body>
</html>''')
    
    conn.close()
    return filename

if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)