#!/usr/bin/env python3
"""
Generate All Lists - CLI Version
Generates both toplist and songs list in one run with optional Spotify updates.
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our utilities and web_admin functions
from spotify_utils import rate_limit_delay
from web_admin import (
    get_db_connection, generate_html_toplist, generate_html_songs,
    safe_spotify_artist, sp, logger
)

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('generate_all.log')
        ]
    )

def update_artists_from_spotify():
    """Update all artist data from Spotify"""
    if not sp:
        logger.error("Spotify client not configured. Skipping artist updates.")
        return 0, 0
    
    logger.info("Updating artist data from Spotify...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    update_count = 0
    error_count = 0
    
    total_artists = conn.execute('SELECT COUNT(*) FROM artists').fetchone()[0]
    logger.info(f"Processing {total_artists} artists...")
    
    for i, row in enumerate(cur.execute('SELECT * FROM artists ORDER BY id'), 1):
        urn = row['id']
        
        logger.debug(f"Processing artist {i}/{total_artists}: {urn}")
        
        # Use safe Spotify artist call with retry handling
        artist = safe_spotify_artist(sp, urn)
        if not artist:
            logger.error(f"Failed to get artist data for {urn}")
            error_count += 1
            continue
        
        print(f"[{i:3d}/{total_artists}] Updating: {artist['name']}")
        
        if row['bInactivate'] != 0:
            logger.debug(f"Skipping inactive artist: {artist['name']}")
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
        
        # Add small delay between requests to be respectful
        rate_limit_delay()
        
        # Show progress every 10 artists
        if i % 10 == 0:
            logger.info(f"Progress: {i}/{total_artists} artists processed")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Artist update completed: {update_count} updated, {error_count} errors")
    return update_count, error_count

def generate_all_lists(update_spotify=False, verbose=False):
    """
    Generate all lists (toplist and songs) in one run
    
    Args:
        update_spotify (bool): Whether to update artist data from Spotify first
        verbose (bool): Enable verbose logging
        
    Returns:
        dict: Results summary with generated files and statistics
    """
    setup_logging(verbose)
    
    start_time = datetime.now()
    logger.info("="*60)
    logger.info("Starting batch generation of all lists")
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Update from Spotify: {'Yes' if update_spotify else 'No'}")
    logger.info("="*60)
    
    results = {
        'toplist_file': None,
        'songs_file': None,
        'update_count': 0,
        'error_count': 0,
        'errors': [],
        'start_time': start_time,
        'end_time': None,
        'duration': None
    }
    
    try:
        # Step 1: Update artist data from Spotify if requested
        if update_spotify:
            logger.info("Step 1/3: Updating artist data from Spotify...")
            update_count, error_count = update_artists_from_spotify()
            results['update_count'] = update_count
            results['error_count'] += error_count
            
            if error_count > 0:
                results['errors'].append(f"Failed to update {error_count} artists from Spotify")
        else:
            logger.info("Step 1/3: Skipping Spotify update (not requested)")
        
        # Step 2: Generate HTML toplist
        logger.info("Step 2/3: Generating HTML toplist...")
        try:
            results['toplist_file'] = generate_html_toplist()
            logger.info(f"✅ Toplist generated: {results['toplist_file']}")
        except Exception as e:
            error_msg = f"Error generating toplist: {str(e)}"
            logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
            results['error_count'] += 1
        
        # Step 3: Generate HTML songs list
        logger.info("Step 3/3: Generating HTML songs list...")
        try:
            results['songs_file'] = generate_html_songs()
            logger.info(f"✅ Songs list generated: {results['songs_file']}")
        except Exception as e:
            error_msg = f"Error generating songs list: {str(e)}"
            logger.error(f"❌ {error_msg}")
            results['errors'].append(error_msg)
            results['error_count'] += 1
        
        # Calculate completion stats
        results['end_time'] = datetime.now()
        results['duration'] = results['end_time'] - results['start_time']
        
        # Summary
        logger.info("="*60)
        logger.info("BATCH GENERATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Duration: {results['duration']}")
        logger.info(f"Files generated:")
        if results['toplist_file']:
            logger.info(f"  ✅ Toplist: {results['toplist_file']}")
        else:
            logger.info(f"  ❌ Toplist: Failed to generate")
        
        if results['songs_file']:
            logger.info(f"  ✅ Songs: {results['songs_file']}")
        else:
            logger.info(f"  ❌ Songs: Failed to generate")
        
        if update_spotify:
            logger.info(f"Artists updated from Spotify: {results['update_count']}")
        
        if results['error_count'] > 0:
            logger.info(f"Total errors: {results['error_count']}")
            for error in results['errors']:
                logger.info(f"  - {error}")
        else:
            logger.info("✅ No errors encountered")
        
        logger.info("="*60)
        
        return results
        
    except Exception as e:
        error_msg = f'Critical error during batch generation: {str(e)}'
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        results['errors'].append(error_msg)
        results['error_count'] += 1
        results['end_time'] = datetime.now()
        results['duration'] = results['end_time'] - results['start_time']
        return results

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Generate all Hälsingetoppen lists (toplist and songs) in one run',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_all_cli.py                    # Generate lists without Spotify update
  python generate_all_cli.py --update-spotify  # Update from Spotify first, then generate
  python generate_all_cli.py -v                # Verbose output
  python generate_all_cli.py --update-spotify -v  # Full update with verbose output

This script will:
1. Optionally update all artist data from Spotify (popularity, followers, images)
2. Generate HTML toplist ranking artists by popularity
3. Generate HTML songs list with all top tracks

Generated files will be saved in the current directory.
Progress and results are logged to both console and generate_all.log.
        """
    )
    
    parser.add_argument(
        '--update-spotify', '-u',
        action='store_true',
        help='Update artist data from Spotify before generating lists (slower but more current data)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output with detailed logging'
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not os.path.exists('toppen.sqlite3'):
        print("Error: toppen.sqlite3 database not found.")
        print("Please run this script from the Hälsingetoppen directory.")
        sys.exit(1)
    
    # Run the generation
    try:
        results = generate_all_lists(
            update_spotify=args.update_spotify,
            verbose=args.verbose
        )
        
        # Exit with appropriate code
        if results['error_count'] > 0:
            if results['toplist_file'] or results['songs_file']:
                # Partial success
                print(f"\\nCompleted with {results['error_count']} errors. Some files were generated.")
                sys.exit(1)
            else:
                # Complete failure
                print(f"\\nFailed with {results['error_count']} errors. No files were generated.")
                sys.exit(2)
        else:
            # Complete success
            print(f"\\n✅ All lists generated successfully in {results['duration']}!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\\n❌ Generation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")
        sys.exit(3)

if __name__ == '__main__':
    main()