"""
Spotify API utilities with proper rate limiting and retry handling.
Implements Spotify's recommended retry-after behavior for 429 responses.
"""

import time
import logging
from typing import Any, Callable, Dict, Optional
from spotipy.exceptions import SpotifyException

# Set up logging
logger = logging.getLogger(__name__)

def spotify_request_with_retry(
    spotify_func: Callable, 
    *args, 
    max_retries: int = 3,
    base_delay: float = 1.0,
    **kwargs
) -> Any:
    """
    Execute a Spotify API request with automatic retry handling for rate limits.
    
    Implements Spotify's recommended behavior:
    - When a 429 error is received, wait for the time specified in Retry-After header
    - Use exponential backoff for other transient errors
    - Respect Spotify's rate limiting guidelines
    
    Args:
        spotify_func: The spotipy function to call (e.g., sp.artist, sp.search)
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay for exponential backoff (default: 1.0 seconds)
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the Spotify API call
        
    Raises:
        SpotifyException: If all retries are exhausted or for non-retryable errors
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            # Execute the Spotify API call
            result = spotify_func(*args, **kwargs)
            
            # Success - reset any rate limiting state
            if attempt > 0:
                logger.info(f"Spotify API call succeeded after {attempt} retries")
            
            return result
            
        except SpotifyException as e:
            last_exception = e
            
            # Check if this is a rate limit error (429)
            if e.http_status == 429:
                # Extract Retry-After header value
                retry_after = None
                if hasattr(e, 'headers') and e.headers:
                    retry_after = e.headers.get('Retry-After') or e.headers.get('retry-after')
                
                if retry_after:
                    try:
                        retry_seconds = int(retry_after)
                        logger.warning(f"Rate limited by Spotify. Waiting {retry_seconds} seconds as specified in Retry-After header")
                        time.sleep(retry_seconds)
                        continue
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid Retry-After header value: {retry_after}")
                
                # If no valid Retry-After header, use exponential backoff
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Rate limited by Spotify. No valid Retry-After header. Using exponential backoff: {delay} seconds")
                time.sleep(delay)
                continue
                
            # Check for other potentially retryable errors
            elif e.http_status in [500, 502, 503, 504]:
                # Server errors - use exponential backoff
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Server error {e.http_status}. Retrying in {delay} seconds. Attempt {attempt + 1}/{max_retries}")
                    time.sleep(delay)
                    continue
                    
            # Non-retryable error or max retries reached
            logger.error(f"Non-retryable Spotify error or max retries reached: {e.http_status} - {e.msg}")
            raise e
            
        except Exception as e:
            # Non-Spotify exceptions are generally not retryable
            logger.error(f"Non-Spotify exception in API call: {type(e).__name__}: {e}")
            raise e
    
    # This should not be reached, but just in case
    if last_exception:
        raise last_exception
    else:
        raise Exception("Unexpected error in spotify_request_with_retry")


def safe_spotify_artist(sp, artist_id: str, **kwargs) -> Optional[Dict]:
    """
    Safely get artist information with retry handling.
    
    Args:
        sp: Spotify client instance
        artist_id: Artist Spotify ID
        **kwargs: Additional arguments for sp.artist()
        
    Returns:
        Artist information dict or None if error
    """
    try:
        return spotify_request_with_retry(sp.artist, artist_id, **kwargs)
    except SpotifyException as e:
        logger.error(f"Failed to get artist {artist_id}: {e.http_status} - {e.msg}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting artist {artist_id}: {e}")
        return None


def safe_spotify_artist_top_tracks(sp, artist_id: str, country: str = 'SE', **kwargs) -> Optional[Dict]:
    """
    Safely get artist's top tracks with retry handling.
    
    Args:
        sp: Spotify client instance
        artist_id: Artist Spotify ID
        country: Country code for top tracks (default: 'SE' for Sweden)
        **kwargs: Additional arguments for sp.artist_top_tracks()
        
    Returns:
        Top tracks dict or None if error
    """
    try:
        return spotify_request_with_retry(sp.artist_top_tracks, artist_id, country=country, **kwargs)
    except SpotifyException as e:
        logger.error(f"Failed to get top tracks for artist {artist_id}: {e.http_status} - {e.msg}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting top tracks for artist {artist_id}: {e}")
        return None


def safe_spotify_search(sp, query: str, search_type: str = 'artist', limit: int = 10, **kwargs) -> Optional[Dict]:
    """
    Safely search Spotify with retry handling.
    
    Args:
        sp: Spotify client instance
        query: Search query
        search_type: Type of search ('artist', 'track', 'album', etc.)
        limit: Number of results to return
        **kwargs: Additional arguments for sp.search()
        
    Returns:
        Search results dict or None if error
    """
    try:
        return spotify_request_with_retry(sp.search, q=query, type=search_type, limit=limit, **kwargs)
    except SpotifyException as e:
        logger.error(f"Failed to search Spotify for '{query}': {e.http_status} - {e.msg}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error searching Spotify for '{query}': {e}")
        return None


def get_retry_delay_from_headers(headers: Dict) -> Optional[int]:
    """
    Extract retry delay from Spotify response headers.
    
    Args:
        headers: HTTP response headers
        
    Returns:
        Number of seconds to wait, or None if not found
    """
    if not headers:
        return None
        
    # Try different case variations of Retry-After header
    retry_after = headers.get('Retry-After') or headers.get('retry-after') or headers.get('RETRY-AFTER')
    
    if retry_after:
        try:
            return int(retry_after)
        except (ValueError, TypeError):
            logger.warning(f"Invalid Retry-After header value: {retry_after}")
    
    return None


# Rate limiting configuration
DEFAULT_RATE_LIMIT_DELAY = 0.1  # Default delay between requests (100ms)
RATE_LIMIT_BURST_DELAY = 1.0    # Delay after hitting rate limits

def rate_limit_delay(delay: float = DEFAULT_RATE_LIMIT_DELAY):
    """
    Add a small delay to respect Spotify's rate limits proactively.
    
    Args:
        delay: Number of seconds to delay (default: 0.1)
    """
    time.sleep(delay)