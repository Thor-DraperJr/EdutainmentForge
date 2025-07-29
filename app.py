"""
EdutainmentForge Web Application

Local web interface for processing Microsoft Learn URLs into podcasts.
Supports single URL processing with multi-voice TTS and Azure AD B2C authentication.
Requires user authentication via Microsoft Entra ID (Azure AD B2C).
"""

import os
import sys
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
import threading
import uuid
from datetime import datetime, timedelta
import logging
from functools import wraps

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content.fetcher import MSLearnFetcher
from content.processor import ScriptProcessor
from content.catalog import create_catalog_service
from audio.tts import create_tts_service
from audio import create_best_multivoice_tts_service
from utils.config import load_config
from utils.premium_integration import print_feature_status

# Authentication imports
from auth import AuthService, require_auth, AuthConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global storage for processing status (with thread-safe access)
import threading
processing_status = {}
status_lock = threading.Lock()

def debug_log_status():
    """Debug function to log current status keys."""
    with status_lock:
        keys = list(processing_status.keys())
        print(f"DEBUG: Current status keys: {keys}")
        return keys

def load_env():
    """Load environment variables from .env file."""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value

# Load environment on startup
load_env()

# Initialize authentication
try:
    auth_config = AuthConfig()
    auth_config.validate()
    auth_service = AuthService(auth_config)
    
    # Configure Flask session
    app.secret_key = auth_config.flask_secret_key
    app.permanent_session_lifetime = timedelta(hours=24)
    
    logger.info("Authentication configured successfully")
    AUTHENTICATION_REQUIRED = True
except Exception as e:
    logger.error(f"Authentication configuration failed: {e}")
    logger.warning("Authentication is REQUIRED but not configured properly")
    logger.info("Please configure Azure AD B2C environment variables to use the application")
    auth_service = None
    AUTHENTICATION_REQUIRED = True  # Always require auth
    # Set a temporary secret key for development
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-me')

# Authentication routes
@app.route('/auth/login')
def auth_login():
    """Show login page or initiate Azure AD B2C login flow."""
    if not auth_service:
        # Authentication is not configured
        flash("Authentication is required but not configured. Please set up Azure AD B2C configuration.", "error")
        return render_template('login.html', auth_service=None)
    
    # Check if this is a direct access to login page or a redirect from auth flow
    if request.args.get('action') == 'signin':
        try:
            # Get the base URL for redirect URI (auth service will use public URL if needed)
            base_url = request.url_root
            auth_url = auth_service.get_auth_url(base_url)
            return redirect(auth_url)
        except Exception as e:
            logger.error(f"Error initiating login: {e}")
            flash("Login failed. Please try again.", "error")
            return render_template('login.html', auth_service=auth_service)
    
    # Show the login page
    return render_template('login.html', auth_service=auth_service)

@app.route('/auth/callback')
def auth_callback():
    """Handle Azure AD B2C authentication callback."""
    if not auth_service:
        flash("Authentication is not configured.", "error")
        return redirect(url_for('index'))
    
    try:
        base_url = request.url_root
        user_info = auth_service.handle_callback(base_url)
        
        if user_info:
            flash(f"Welcome, {user_info.get('name', user_info.get('email', 'User'))}!", "success")
            
            # Redirect to originally requested page or main app
            next_url = session.pop('next_url', url_for('main_app'))
            return redirect(next_url)
        else:
            flash("Authentication failed. Please try again.", "error")
            return redirect(url_for('auth_login'))
            
    except Exception as e:
        logger.error(f"Error handling authentication callback: {e}")
        flash("Authentication error. Please try again.", "error")
        return redirect(url_for('auth_login'))

@app.route('/auth/logout')
def auth_logout():
    """Log out the current user."""
    if not auth_service:
        session.clear()
        return redirect(url_for('index'))
    
    try:
        logout_url = auth_service.logout()
        flash("You have been logged out successfully.", "info")
        
        # Redirect to Azure AD B2C logout, which will then redirect back to our app
        return redirect(logout_url)
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        session.clear()
        flash("Logout completed.", "info")
        return redirect(url_for('index'))

@app.route('/auth/profile')
@require_auth
def auth_profile():
    """Display user profile information."""
    if not auth_service:
        return redirect(url_for('index'))
    
    user = auth_service.get_current_user()
    return render_template('profile.html', user=user)

# Helper function to check authentication - ALWAYS required
def _require_auth(f):
    """Apply authentication requirement - ALWAYS required."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if authentication service is available
        if not auth_service:
            flash("Authentication is required but not configured. Please contact the administrator.", "error")
            return render_template('login.html', auth_service=None)
        
        # Check if user is authenticated
        if not auth_service.is_authenticated():
            logger.info(f"Unauthenticated access attempt to {request.endpoint}")
            session['next_url'] = request.url
            return redirect(url_for('auth_login'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Landing page - always requires authentication."""
    # Check if authentication service is available
    if not auth_service:
        # Show login page with error message about missing configuration
        flash("Authentication is required but not properly configured. Please contact the administrator.", "error")
        return render_template('login.html', auth_service=None)
    
    # Check if user is authenticated
    if not auth_service.is_authenticated():
        # Redirect to login page
        return redirect(url_for('auth_login'))
    
    # User is authenticated, redirect to main app
    return redirect(url_for('main_app'))

@app.route('/app')
@_require_auth
def main_app():
    """Main application page with URL input form and podcast library."""
    # Get list of available podcasts from local output directory
    podcasts = []
    output_dir = Path("output")
    if output_dir.exists():
        try:
            # Find all .wav files in output directory
            for wav_file in output_dir.glob("*.wav"):
                # Skip demo files
                if "demo_" not in wav_file.name:
                    podcasts.append({
                        'name': wav_file.stem,
                        'filename': wav_file.name,
                        'size': f"{wav_file.stat().st_size / (1024*1024):.1f}MB",
                        'created': datetime.fromtimestamp(wav_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                    })
            # Sort by creation time (newest first)
            podcasts.sort(key=lambda x: x['created'], reverse=True)
            podcasts = podcasts[:20]  # Limit to 20 most recent
        except Exception as e:
            print(f"Could not load local podcasts: {e}")
    
    return render_template('index.html', podcasts=podcasts)

@app.route('/discover')
@_require_auth
def discover_page():
    """Discovery page for browsing Microsoft Learn catalog."""
    return render_template('discover.html')

@app.route('/library')
@_require_auth
def library_page():
    """Podcast library page for managing generated podcasts."""
    return render_template('library.html')

@app.route('/api/catalog/search', methods=['GET'])
@_require_auth
def catalog_search():
    """Search the Microsoft Learn catalog."""
    try:
        # Get query parameters
        query = request.args.get('q', '').strip()
        content_type = request.args.get('type', 'modules')
        product = request.args.get('product', '')
        role = request.args.get('role', '')
        topic = request.args.get('topic', '')
        limit = min(int(request.args.get('limit', 20)), 50)  # Cap at 50
        
        # Create catalog service and search
        catalog_service = create_catalog_service()
        results = catalog_service.search_content(
            query=query,
            content_type=content_type,
            product=product if product else None,
            role=role if role else None,
            topic=topic if topic else None,
            limit=limit
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Catalog search failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/certification-tracks', methods=['GET'])
@_require_auth
def get_certification_tracks():
    """Get organized certification tracks grouped by role."""
    try:
        catalog_service = create_catalog_service()
        tracks = catalog_service.get_certification_tracks()
        return jsonify(tracks)
        
    except Exception as e:
        logger.error(f"Failed to get certification tracks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/roles', methods=['GET'])
@_require_auth  
def get_roles():
    """Get available roles for certification browsing."""
    try:
        catalog_service = create_catalog_service()
        tracks = catalog_service.get_certification_tracks()
        
        roles = []
        for role_id, role_data in tracks.items():
            roles.append({
                'id': role_id,
                'name': role_data['name'],
                'description': role_data['description'],
                'certification_count': len(role_data['certifications'])
            })
        
        return jsonify({'roles': roles})
        
    except Exception as e:
        logger.error(f"Failed to get roles: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/roles/<role_id>/certifications', methods=['GET'])
@_require_auth
def get_role_certifications(role_id):
    """Get certifications for a specific role."""
    try:
        catalog_service = create_catalog_service()
        tracks = catalog_service.get_certification_tracks()
        
        if role_id not in tracks:
            return jsonify({'error': 'Role not found'}), 404
        
        role_data = tracks[role_id]
        certifications = []
        
        for cert_id, cert_data in role_data['certifications'].items():
            certifications.append({
                'id': cert_id,
                'name': cert_data['name'],
                'description': cert_data['description'],
                'module_count': len(cert_data['modules'])
            })
        
        return jsonify({
            'role': {
                'id': role_id,
                'name': role_data['name'],
                'description': role_data['description']
            },
            'certifications': certifications
        })
        
    except Exception as e:
        logger.error(f"Failed to get certifications for role {role_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/certifications/<cert_id>/modules', methods=['GET'])  
@_require_auth
def get_certification_modules(cert_id):
    """Get modules for a specific certification."""
    try:
        catalog_service = create_catalog_service()
        tracks = catalog_service.get_certification_tracks()
        
        # Find the certification across all roles
        cert_data = None
        role_info = None
        
        for role_id, role_data in tracks.items():
            if cert_id in role_data['certifications']:
                cert_data = role_data['certifications'][cert_id] 
                role_info = {
                    'id': role_id,
                    'name': role_data['name'],
                    'description': role_data['description']
                }
                break
        
        if not cert_data:
            return jsonify({'error': 'Certification not found'}), 404
        
        return jsonify({
            'certification': {
                'id': cert_id,
                'name': cert_data['name'],
                'description': cert_data['description']
            },
            'role': role_info,
            'modules': cert_data['modules']
        })
        
    except Exception as e:
        logger.error(f"Failed to get modules for certification {cert_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/facets', methods=['GET'])
@_require_auth
def catalog_facets():
    """Get available catalog facets for filtering."""
    try:
        catalog_service = create_catalog_service()
        facets = catalog_service.get_catalog_facets()
        return jsonify(facets)
        
    except Exception as e:
        logger.error(f"Failed to get catalog facets: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/learning-path/<path_id>/modules', methods=['GET'])
@_require_auth
def get_learning_path_modules(path_id):
    """Get modules in a learning path."""
    try:
        catalog_service = create_catalog_service()
        modules = catalog_service.get_learning_path_modules(path_id)
        return jsonify({'modules': modules, 'total': len(modules)})
        
    except Exception as e:
        logger.error(f"Failed to get learning path modules: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/modules/<path:module_id>', methods=['GET'])
@_require_auth
def get_module_details(module_id):
    """Get detailed information about a specific module including unit URLs."""
    try:
        catalog_service = create_catalog_service()
        module_details = catalog_service.get_module_details(module_id)
        
        if module_details:
            return jsonify(module_details)
        else:
            return jsonify({'error': 'Module not found'}), 404
        
    except Exception as e:
        logger.error(f"Failed to get module details for {module_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-catalog-item', methods=['POST'])
@_require_auth
def process_catalog_item():
    """Process a catalog item (module or learning path) into a podcast."""
    try:
        data = request.get_json()
        catalog_item = data.get('catalog_item', {})
        
        if not catalog_item:
            return jsonify({'error': 'Catalog item is required'}), 400
        
        if not catalog_item.get('url'):
            return jsonify({'error': 'Catalog item must have a URL'}), 400
        
        # Generate unique ID for this processing task
        task_id = str(uuid.uuid4())
        
        # Initialize status
        with status_lock:
            processing_status[task_id] = {
                'status': 'started',
                'progress': 0,
                'message': f'Starting processing of "{catalog_item.get("title", "Unknown")}"...',
                'catalog_item': catalog_item,
                'created_at': datetime.now().isoformat()
            }
        
        # Start processing in background thread
        thread = threading.Thread(target=process_catalog_item_background, args=(task_id, catalog_item))
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id, 'status': 'processing'}), 202
        
    except Exception as e:
        logger.error(f"Catalog item processing failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-learning-path', methods=['POST'])
@_require_auth
def process_learning_path():
    """Process an entire learning path into multiple podcasts."""
    try:
        data = request.get_json()
        learning_path_id = data.get('learning_path_id', '').strip()
        learning_path_title = data.get('title', 'Learning Path')
        
        if not learning_path_id:
            return jsonify({'error': 'Learning path ID is required'}), 400
        
        # Generate unique ID for this batch processing task
        task_id = str(uuid.uuid4())
        
        # Initialize status
        with status_lock:
            processing_status[task_id] = {
                'status': 'started',
                'progress': 0,
                'message': f'Starting batch processing of "{learning_path_title}"...',
                'learning_path_id': learning_path_id,
                'learning_path_title': learning_path_title,
                'batch_processing': True,
                'completed_modules': [],
                'failed_modules': [],
                'created_at': datetime.now().isoformat()
            }
        
        # Start processing in background thread
        thread = threading.Thread(target=process_learning_path_background, args=(task_id, learning_path_id, learning_path_title))
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id, 'status': 'processing', 'batch': True}), 202
        
    except Exception as e:
        logger.error(f"Learning path processing failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
@_require_auth
def process_url():
    """Process a Microsoft Learn URL into a podcast."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        voice = data.get('voice', 'en-US-AriaNeural')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if 'learn.microsoft.com' not in url:
            return jsonify({'error': 'URL must be from learn.microsoft.com'}), 400
        
        # Generate unique ID for this processing task
        task_id = str(uuid.uuid4())
        
        # Initialize status with thread-safe access
        with status_lock:
            processing_status[task_id] = {
                'status': 'started',
                'progress': 0,
                'message': 'Starting processing...',
                'url': url,
                'voice': voice,
                'created_at': datetime.now().isoformat()
            }
            # Debug log
            print(f"DEBUG: Created task {task_id}, total tasks: {len(processing_status)}")
        
        # Start processing in background thread
        thread = threading.Thread(target=process_url_background, args=(task_id, url, voice))
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id, 'status': 'processing'}), 202
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def process_url_background(task_id, url, voice):
    """Background processing of URL to podcast."""
    try:
        # Update status
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'fetching',
                    'progress': 20,
                    'message': 'Fetching content from Microsoft Learn...'
                })
                print(f"DEBUG: Updated task {task_id} to fetching stage")
        
        # Load config
        config = load_config()
        if voice:
            config['tts_voice'] = voice
        
        # Fetch content
        fetcher = MSLearnFetcher()
        content = fetcher.fetch_module_content(url)
        
        if not content or not content.get('title') or not content.get('content'):
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'status': 'error',
                        'message': 'Failed to fetch content or content is empty'
                    })
            return
        
        # Update status
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'processing_script',
                    'progress': 50,
                    'message': 'Converting to podcast script...'
                })
        
        # Process into script
        processor = ScriptProcessor()
        script_result = processor.process_content_to_script(content)
        script = script_result.get('script', '')
        
        # Update status
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'generating_audio',
                    'progress': 70,
                    'message': 'Generating audio with Azure Speech Service...'
                })
        
        # Generate audio with multi-voice support (premium or standard)
        multivoice_tts = create_best_multivoice_tts_service(config)
        
        # Create output filename
        clean_title = "".join(c for c in content['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_title = clean_title.replace(' ', '_')[:50]
        output_name = f"{clean_title}_{task_id[:8]}"
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save script
        script_path = output_dir / f"{output_name}_script.txt"
        script_path.write_text(script)
        
        # Define progress callback to update status during TTS
        def tts_progress_callback(progress, message):
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'progress': progress,
                        'message': message
                    })
                    print(f"DEBUG: TTS Progress {task_id} - {progress}% - {message}")
        
        # Generate audio with multiple voices and progress tracking
        audio_path = output_dir / f"{output_name}.wav"
        success = multivoice_tts.synthesize_dialogue_script(script, audio_path, progress_callback=tts_progress_callback)
        
        if success and audio_path.exists():
            file_size = audio_path.stat().st_size
            
            # Update status - completed
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'message': 'Podcast generated successfully!',
                        'audio_file': str(audio_path),
                        'audio_filename': audio_path.name,  # Add filename for direct access
                        'script_file': str(script_path),
                        'title': content['title'],
                        'file_size': file_size,
                        'duration_estimate': len(script) / 12  # ~12 chars per second
                    })
                    print(f"DEBUG: Task {task_id} completed successfully")
        else:
            # Audio generation failed
            error_details = f"success={success}, file_exists={audio_path.exists() if audio_path else False}"
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'status': 'error',
                        'message': f'Failed to generate audio file. Details: {error_details}'
                    })
                    print(f"DEBUG: Task {task_id} failed audio generation - {error_details}")
                    
                    # Log more details for debugging
                    if audio_path:
                        print(f"DEBUG: Audio path: {audio_path}")
                        print(f"DEBUG: Audio path exists: {audio_path.exists()}")
                        print(f"DEBUG: Output directory: {output_dir}")
                        print(f"DEBUG: Output directory exists: {output_dir.exists()}")
            
    except Exception as e:
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'error',
                    'message': f'Processing error: {str(e)}'
                })
                print(f"DEBUG: Task {task_id} failed with exception: {e}")

def process_catalog_item_background(task_id, catalog_item):
    """Background processing of catalog item to podcast."""
    try:
        # Update status
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'fetching',
                    'progress': 20,
                    'message': f'Fetching content for "{catalog_item.get("title", "Unknown")}"...'
                })
        
        # Load config
        config = load_config()
        
        # Fetch content using enhanced fetcher
        fetcher = MSLearnFetcher()
        content = fetcher.fetch_content_from_catalog_item(catalog_item)
        
        if not content or not content.get('title') or not content.get('content'):
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'status': 'error',
                        'message': 'Failed to fetch content or content is empty'
                    })
            return
        
        # Update status
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'processing_script',
                    'progress': 50,
                    'message': 'Converting to podcast script...'
                })
        
        # Process into script
        processor = ScriptProcessor()
        script_result = processor.process_content_to_script(content)
        script = script_result.get('script', '')
        
        # Update status
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'generating_audio',
                    'progress': 70,
                    'message': 'Generating audio with Azure Speech Service...'
                })
        
        # Generate audio with multi-voice support
        multivoice_tts = create_best_multivoice_tts_service(config)
        
        # Create output filename
        clean_title = "".join(c for c in content['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_title = clean_title.replace(' ', '_')[:50]
        output_name = f"{clean_title}_{task_id[:8]}"
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save script
        script_path = output_dir / f"{output_name}_script.txt"
        script_path.write_text(script)
        
        # Define progress callback
        def tts_progress_callback(progress, message):
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'progress': progress,
                        'message': message
                    })
        
        # Generate audio
        audio_path = output_dir / f"{output_name}.wav"
        success = multivoice_tts.synthesize_dialogue_script(script, audio_path, progress_callback=tts_progress_callback)
        
        if success and audio_path.exists():
            file_size = audio_path.stat().st_size
            
            # Update status - completed
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'message': f'Podcast for "{content["title"]}" generated successfully!',
                        'audio_file': str(audio_path),
                        'audio_filename': audio_path.name,
                        'script_file': str(script_path),
                        'title': content['title'],
                        'file_size': file_size,
                        'duration_estimate': len(script) / 12,
                        'catalog_item': catalog_item
                    })
        else:
            error_details = f"success={success}, file_exists={audio_path.exists() if audio_path else False}"
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'status': 'error',
                        'message': f'Failed to generate audio file. Details: {error_details}'
                    })
                    
    except Exception as e:
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'error',
                    'message': f'Processing error: {str(e)}'
                })

def process_learning_path_background(task_id, learning_path_id, learning_path_title):
    """Background processing of entire learning path to multiple podcasts."""
    try:
        # Update status
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'fetching',
                    'progress': 10,
                    'message': f'Fetching modules for "{learning_path_title}"...'
                })
        
        # Load config
        config = load_config()
        
        # Fetch learning path modules
        fetcher = MSLearnFetcher()
        module_contents = fetcher.fetch_learning_path_content(learning_path_id)
        
        if not module_contents:
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'status': 'error',
                        'message': 'No modules found in learning path'
                    })
            return
        
        total_modules = len(module_contents)
        completed_modules = []
        failed_modules = []
        
        # Process each module
        for i, content in enumerate(module_contents, 1):
            try:
                # Update progress
                base_progress = 20 + (i - 1) * 70 // total_modules
                with status_lock:
                    if task_id in processing_status:
                        processing_status[task_id].update({
                            'progress': base_progress,
                            'message': f'Processing module {i}/{total_modules}: "{content.get("title", "Unknown")}"...'
                        })
                
                # Process into script
                processor = ScriptProcessor()
                script_result = processor.process_content_to_script(content)
                script = script_result.get('script', '')
                
                # Generate audio
                multivoice_tts = create_best_multivoice_tts_service(config)
                
                # Create output filename
                clean_title = "".join(c for c in content['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                clean_title = clean_title.replace(' ', '_')[:50]
                output_name = f"{learning_path_title.replace(' ', '_')}_Module_{i:02d}_{clean_title}_{task_id[:8]}"
                
                output_dir = Path("output")
                output_dir.mkdir(exist_ok=True)
                
                # Save script
                script_path = output_dir / f"{output_name}_script.txt"
                script_path.write_text(script)
                
                # Generate audio
                audio_path = output_dir / f"{output_name}.wav"
                success = multivoice_tts.synthesize_dialogue_script(script, audio_path)
                
                if success and audio_path.exists():
                    completed_modules.append({
                        'title': content['title'],
                        'filename': audio_path.name,
                        'file_size': audio_path.stat().st_size
                    })
                else:
                    failed_modules.append({
                        'title': content['title'],
                        'error': 'Audio generation failed'
                    })
                
            except Exception as e:
                logger.error(f"Failed to process module {i}: {e}")
                failed_modules.append({
                    'title': content.get('title', f'Module {i}'),
                    'error': str(e)
                })
            
            # Update status with current progress
            with status_lock:
                if task_id in processing_status:
                    processing_status[task_id].update({
                        'completed_modules': completed_modules,
                        'failed_modules': failed_modules
                    })
        
        # Final status update
        final_progress = 100
        success_count = len(completed_modules)
        fail_count = len(failed_modules)
        
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'completed' if success_count > 0 else 'error',
                    'progress': final_progress,
                    'message': f'Learning path processing completed: {success_count} succeeded, {fail_count} failed',
                    'completed_modules': completed_modules,
                    'failed_modules': failed_modules,
                    'total_modules': total_modules
                })
                
    except Exception as e:
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'error',
                    'message': f'Learning path processing error: {str(e)}'
                })

@app.route('/api/status/<task_id>')
@_require_auth
def get_status(task_id):
    """Get processing status for a task."""
    with status_lock:
        current_keys = list(processing_status.keys())
        print(f"DEBUG: Status check for {task_id}, available: {current_keys}")
        
        if task_id not in processing_status:
            return jsonify({'error': 'Task not found', 'available_tasks': current_keys}), 404
        
        return jsonify(processing_status[task_id])

@app.route('/api/audio/<task_id>')
@_require_auth
def get_audio(task_id):
    """Download or stream the generated audio file."""
    if task_id not in processing_status:
        return jsonify({'error': 'Task not found'}), 404
    
    status = processing_status[task_id]
    if status['status'] != 'completed':
        return jsonify({'error': 'Audio not ready'}), 400
    
    audio_file = status.get('audio_file')
    if not audio_file or not Path(audio_file).exists():
        return jsonify({'error': 'Audio file not found'}), 404
    
    return send_file(audio_file, as_attachment=False, mimetype='audio/wav')

@app.route('/api/debug/status')
def debug_status():
    """Debug endpoint to show all current task statuses."""
    with status_lock:
        debug_info = {
            'total_tasks': len(processing_status),
            'task_keys': list(processing_status.keys()),
            'task_details': {k: v.get('status', 'unknown') for k, v in processing_status.items()}
        }
        return jsonify(debug_info)

@app.route('/api/voices')
def get_voices():
    """Get available Azure voices."""
    voices = {
        "en-US-EmmaNeural": "Emma - Premium Female, Natural & Conversational (recommended for Sarah)",
        "en-US-DavisNeural": "Davis - US English Male, Conversational (recommended for Mike)",
    }
    return jsonify(voices)

@app.route('/api/podcasts')
@_require_auth
def list_podcasts():
    """List all available podcasts from local storage."""
    try:
        from datetime import datetime
        import wave
        
        output_dir = Path("output")
        podcasts = []
        
        if output_dir.exists():
            for wav_file in output_dir.glob("*.wav"):
                # Try to find corresponding script file
                script_file = wav_file.with_name(wav_file.stem + '_script.txt')
                
                # Get audio duration
                duration_seconds = 0
                try:
                    with wave.open(str(wav_file), 'rb') as audio_file:
                        frames = audio_file.getnframes()
                        rate = audio_file.getframerate()
                        duration_seconds = frames / float(rate)
                except Exception as e:
                    print(f"Could not get duration for {wav_file.name}: {e}")
                
                # Format duration as minutes and seconds
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                duration_str = f"{minutes}m {seconds}s" if duration_seconds > 0 else "Unknown"
                
                # Format the date properly
                modified_time = wav_file.stat().st_mtime
                formatted_date = datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M')
                
                podcast_info = {
                    'name': wav_file.name,
                    'title': wav_file.stem.replace('_', ' '),
                    'url': f'/output/{wav_file.name}',
                    'size': wav_file.stat().st_size,
                    'last_modified': formatted_date,
                    'last_modified_timestamp': modified_time,  # Keep timestamp for sorting
                    'source_url': '',
                    'duration': duration_str,
                    'duration_seconds': duration_seconds,  # For statistics
                    'word_count': ''
                }
                
                podcasts.append(podcast_info)
        
        # Sort by last modified timestamp (newest first)
        podcasts.sort(key=lambda x: x['last_modified_timestamp'], reverse=True)
        
        return jsonify({
            'podcasts': podcasts,
            'total': len(podcasts)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/podcast/<path:filename>')
def stream_podcast(filename):
    """Stream a podcast from local storage."""
    try:
        output_dir = Path("output")
        file_path = output_dir / filename
        
        if file_path.exists() and file_path.suffix == '.wav':
            return send_file(str(file_path), as_attachment=False, mimetype='audio/wav')
        else:
            return jsonify({'error': 'Podcast file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/delete-podcast/<path:filename>', methods=['DELETE'])
@_require_auth
def delete_podcast(filename):
    """Delete a podcast from local storage."""
    try:
        output_dir = Path("output")
        file_path = output_dir / filename
        
        if file_path.exists() and file_path.suffix == '.wav':
            file_path.unlink()  # Delete the file
            # Also delete the script file if it exists
            script_path = output_dir / f"{file_path.stem}_script.txt"
            if script_path.exists():
                script_path.unlink()
            return jsonify({'message': 'Podcast deleted successfully'})
        else:
            return jsonify({'error': 'Podcast file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for Azure App Service."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    load_env()
    
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Run the app
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))  # Use PORT env var if set, default to 5000
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
