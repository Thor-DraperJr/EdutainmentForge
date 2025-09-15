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
from flask_session import Session
import threading
import uuid
from datetime import datetime, timedelta
import logging
from functools import wraps

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content.fetcher import MSLearnFetcher
from content.processor import ScriptProcessor
from content.clean_catalog import CleanCatalogService  # Modern clean service
from audio.tts import create_tts_service
from audio import create_best_multivoice_tts_service
from utils.config import load_config
from utils.premium_integration import print_feature_status
from utils.task_store import get_task_store
from utils.task_queue import get_task_queue
from utils.rate_limit import rate_limit

# Authentication imports
from auth import AuthService, require_auth, AuthConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global storage for processing status (with thread-safe access)
processing_status = {}  # retained as small hot cache fallback
status_lock = threading.Lock()
task_store = get_task_store()
task_queue = get_task_queue()

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

    # Configure Flask session with server-side storage
    app.secret_key = auth_config.flask_secret_key
    app.permanent_session_lifetime = timedelta(hours=24)

    # Configure Flask-Session for server-side storage to avoid cookie size limits
    session_dir = '/tmp/flask_session'
    os.makedirs(session_dir, exist_ok=True)

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = session_dir
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'edutainment:'

    # Initialize Flask-Session
    Session(app)

    logger.info("Authentication configured successfully with server-side sessions")
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

# Helper function to check authentication - with local testing bypass
def _require_auth(f):
    """Apply authentication requirement - with local development bypass."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Local development bypass - ONLY for testing
        if os.getenv('DISABLE_AUTH_FOR_TESTING', '').lower() == 'true':
            logger.warning("⚠️  Authentication bypassed for local testing - NEVER use in production!")
            # Create a mock user session for testing
            session['user'] = {
                'name': 'Test User',
                'email': 'test@example.com',
                'id': 'test-user-id'
            }
            return f(*args, **kwargs)

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

# ============================================================================
# DEPRECATED LEGACY API ENDPOINTS (v1) - July 30, 2025
# ============================================================================
# These endpoints are no longer used by the frontend (which uses /api/v2/catalog/*)
# They remain here temporarily for backward compatibility but should be removed
# after confirming no external systems depend on them.
#
# Frontend confirmed to use only:
# - /api/v2/catalog/roles
# - /api/v2/catalog/roles/<role_id>/certifications
# - /api/v2/catalog/certifications/<cert_id>/modules
# - /api/v2/catalog/modules/<module_uid>/details
#
# TODO: Remove these deprecated endpoints in next cleanup phase
# ============================================================================

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
        # Using global catalog_service
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
        # Using global catalog_service
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
        # Using global catalog_service
        roles_data = catalog_service.get_roles()

        # Format roles for the frontend
        roles = []
        for role in roles_data:
            roles.append({
                'id': role.get('uid', role.get('id', 'unknown')),
                'name': role.get('name', 'Unknown Role'),
                'description': role.get('description', 'No description available'),
                'certification_count': 8  # Default estimate, could be made dynamic
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
        # Using global catalog_service
        result = catalog_service.get_role_certifications(role_id)

        # Add module count for each certification (estimate)
        for cert in result.get('certifications', []):
            cert['module_count'] = 5  # Default estimate, could be made more accurate

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to get certifications for role {role_id}: {e}")
        return jsonify({'error': 'Failed to load certifications'}), 500
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/certifications/<cert_id>/modules', methods=['GET'])
@_require_auth
def get_certification_modules(cert_id):
    """Get modules for a specific certification."""
    try:
        # Using global catalog_service
        result = catalog_service.get_certification_modules(cert_id)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to get modules for certification {cert_id}: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# NEW CLEAN CATALOG API ENDPOINTS (v2)
# ============================================================================

# Initialize clean catalog service
# Initialize clean catalog service globally
catalog_service = CleanCatalogService()
clean_catalog_service = catalog_service  # Alias for backward compatibility

@app.route('/api/v2/catalog/roles', methods=['GET'])
@_require_auth
def get_roles_v2():
    """Get available roles using the new clean catalog service."""
    try:
        roles = clean_catalog_service.get_available_roles()

        # Format roles for the frontend
        formatted_roles = []
        for role in roles:
            formatted_roles.append({
                'id': role.uid,
                'name': role.name,
                'description': role.description,
                'certification_count': role.certification_count
            })

        return jsonify({'roles': formatted_roles})

    except Exception as e:
        logger.error(f"Failed to get roles (v2): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/catalog/roles/<role_id>/certifications', methods=['GET'])
@_require_auth
def get_role_certifications_v2(role_id):
    """Get certifications for a specific role using clean service."""
    try:
        certifications = clean_catalog_service.get_certifications_for_role(role_id)

        # Format certifications for the frontend
        formatted_certs = []
        for cert in certifications:
            formatted_certs.append({
                'id': cert.uid,
                'name': cert.name,
                'description': cert.description,
                'level': cert.level,
                'module_count': cert.module_count,
                'exam_codes': cert.exam_codes,  # Include exam codes
                'questionable_role_association': cert.questionable_role_association,  # Include warning indicator
                'role_association_explanation': cert.role_association_explanation    # Include warning explanation
            })

        return jsonify({
            'role_id': role_id,
            'certifications': formatted_certs
        })

    except Exception as e:
        logger.error(f"Failed to get certifications for role {role_id} (v2): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/catalog/certifications/<cert_id>/details', methods=['GET'])
@_require_auth
def get_certification_details_v2(cert_id):
    """Get full details for a specific certification including untruncated description."""
    try:
        # Get the full certification data from the Microsoft Learn API
        certification_details = clean_catalog_service.get_certification_full_details(cert_id)

        if not certification_details:
            return jsonify({'error': 'Certification not found'}), 404

        return jsonify(certification_details)

    except Exception as e:
        logger.error(f"Failed to get certification details for {cert_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/catalog/certifications/<cert_id>/modules', methods=['GET'])
@_require_auth
def get_certification_modules_v2(cert_id):
    """Get modules for a specific certification using clean service."""
    try:
        modules = clean_catalog_service.get_modules_for_certification(cert_id)

        # Format modules for the frontend
        formatted_modules = []
        for module in modules:
            formatted_modules.append({
                'uid': module.uid,
                'title': module.title,
                'summary': module.summary,
                'url': module.url,
                'duration_minutes': module.duration_minutes,
                'duration': f"{module.duration_minutes} min" if module.duration_minutes else "45 min",
                'level': module.level,
                'units': module.unit_count  # Frontend expects 'units'
            })

        return jsonify({
            'certification_id': cert_id,
            'modules': formatted_modules
        })

    except Exception as e:
        logger.error(f"Failed to get modules for certification {cert_id} (v2): {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/catalog/modules/<module_uid>/details', methods=['GET'])
@_require_auth
def get_module_details_v2(module_uid):
    """Get detailed module information including units using clean service."""
    try:
        module_details = clean_catalog_service.get_module_with_units(module_uid)

        if not module_details:
            return jsonify({'error': 'Module not found'}), 404

        # Format units for the frontend
        formatted_units = []
        for unit in module_details.units:
            formatted_units.append({
                'title': unit.title,
                'url': unit.url,
                'type': unit.type,
                'duration_minutes': unit.duration_minutes,
                'is_knowledge_check': unit.type == 'knowledge-check'
            })

        return jsonify({
            'uid': module_details.uid,
            'title': module_details.title,
            'summary': module_details.summary,
            'url': module_details.url,
            'duration_minutes': module_details.duration_minutes,
            'level': module_details.level,
            'rating': module_details.rating,
            'units': formatted_units
        })

    except Exception as e:
        logger.error(f"Failed to get module details for {module_uid} (v2): {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# END CLEAN CATALOG API ENDPOINTS
# ============================================================================

@app.route('/api/catalog/facets', methods=['GET'])
@_require_auth
def catalog_facets():
    """Get available catalog facets for filtering."""
    try:
        # Using global catalog_service
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
        # Using global catalog_service
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
        # Using global catalog_service
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
@rate_limit(endpoint_max=3, global_category="processing")
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
@rate_limit(endpoint_max=2, global_category="processing")
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
@rate_limit(endpoint_max=5, global_category="processing")
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
        task_store.create(task_id, { 'status': 'started', 'progress': 0, 'message': 'Starting processing...', 'type': 'url', 'url': url, 'voice': voice })
        task_queue.enqueue({'task_id': task_id, 'type': 'url'})
        logger.debug(f"Created task {task_id}, total tasks (cache): {len(processing_status)}")

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
        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({'status': 'fetching','progress': 20,'message': 'Fetching content from Microsoft Learn...'})
        task_store.update(task_id, status='fetching', progress=20, message='Fetching content from Microsoft Learn...')
        logger.debug(f"Updated task {task_id} to fetching stage")

        # Load config
        config = load_config()
        if voice:
            config['tts_voice'] = voice

        # Fetch content
        fetcher = MSLearnFetcher()
        content = fetcher.fetch_module_content(url)

        if not content or not content.get('title') or not content.get('content'):
            task_store.update(task_id, status='error', message='Failed to fetch content or content is empty')
            return

        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'processing_script',
                    'progress': 50,
                    'message': 'Converting to podcast script...'
                })
        task_store.update(task_id, status='processing_script', progress=50, message='Converting to podcast script...')

        # Process into script
        processor = ScriptProcessor()
        script_result = processor.process_content_to_script(content)
        script = script_result.get('script', '')

        with status_lock:
            if task_id in processing_status:
                processing_status[task_id].update({
                    'status': 'generating_audio',
                    'progress': 70,
                    'message': 'Generating audio with Azure Speech Service...'
                })
        task_store.update(task_id, status='generating_audio', progress=70, message='Generating audio with Azure Speech Service...')

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
            task_store.update(task_id, progress=progress, message=message)
            logger.debug(f"TTS Progress {task_id} - {progress}% - {message}")

        # Generate audio with multiple voices and progress tracking
        audio_path = output_dir / f"{output_name}.wav"
        success = multivoice_tts.synthesize_dialogue_script(script, audio_path, progress_callback=tts_progress_callback)

        if success and audio_path.exists():
            file_size = audio_path.stat().st_size

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
            task_store.update(task_id, status='completed', progress=100, message='Podcast generated successfully!', audio_file=str(audio_path), audio_filename=audio_path.name, script_file=str(script_path), title=content['title'], file_size=file_size)
            logger.debug(f"Task {task_id} completed successfully")
        else:
            error_details = f"success={success}, file_exists={audio_path.exists() if audio_path else False}"
            task_store.update(task_id, status='error', message=f'Failed to generate audio file. Details: {error_details}')
            logger.debug(f"Task {task_id} failed audio generation - {error_details}")
    except Exception as e:
        task_store.update(task_id, status='error', message=f'Processing error: {str(e)}')
        logger.debug(f"Task {task_id} failed with exception: {e}")

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
            task_store.update(task_id, status='error', message='Failed to fetch content or content is empty')
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
            task_store.update(task_id, status='error', message=f'Failed to generate audio file. Details: {error_details}')

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
    # Try cache first
    with status_lock:
        if task_id in processing_status:
            return jsonify(processing_status[task_id])
    # Fallback to task store
    record = task_store.get(task_id)
    if not record:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(record)

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
    recent = task_store.list_recent()
    return jsonify({'cached_total': len(processing_status), 'recent': recent})

@app.route('/api/voices')
def get_voices():
    """Get available Azure voices."""
    voices = {
        "en-US-EmmaNeural": "Emma - Premium Female, Natural & Conversational (recommended for Sarah)",
        "en-US-DavisNeural": "Davis - US English Male, Conversational (recommended for Mike)",
    }
    return jsonify(voices)

@app.route('/prompt', methods=['POST'])
@_require_auth
def prompt_command():
    """Lightweight internal command endpoint.

    Body JSON: {"command": "version"}
    Supported commands:
      - version: returns build metadata (APP_VERSION, GIT_COMMIT) and server time
      - help or empty: list available commands
    This enables post-deployment validation without adding heavy CI logic.
    """
    data = {}
    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        pass
    command = (data.get('command') or '').strip().lower()
    if command in ('', 'help'):
        return jsonify({
            'commands': ['version'],
            'usage': 'POST /prompt {"command": "version"}',
            'status': 'ok'
        })
    if command == 'version':
        return jsonify({
            'app_version': os.getenv('APP_VERSION', 'dev'),
            'git_commit': os.getenv('GIT_COMMIT', 'unknown'),
            'time': datetime.utcnow().isoformat() + 'Z',
            'status': 'ok'
        })
    return jsonify({'error': 'unknown_command', 'status': 'error'}), 400

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

# ---------------------------------------------------------------------------
# Enhanced Health Endpoints (new)
# ---------------------------------------------------------------------------
@app.route('/healthz')
def healthz():
    """Lightweight liveness probe. Returns quickly without remote calls."""
    return jsonify({
        'status': 'ok',
        'time': datetime.utcnow().isoformat() + 'Z',
        'version': os.getenv('APP_VERSION', 'dev'),
    })

@app.route('/healthz/deep')
def healthz_deep():
    """Deep health probe performing dependency & config checks.

    Checks:
      - Essential environment/config values presence
      - Task store operational (remote if configured)
      - Recent task stats from in-memory cache
    """
    checks = {}
    overall_status = 'ok'

    # Config presence checks (non-secret flags only)
    required_env = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_VERSION']
    missing = [k for k in required_env if not os.getenv(k)]
    checks['config'] = {
        'required': required_env,
        'missing': missing,
        'status': 'ok' if not missing else 'degraded'
    }
    if missing:
        overall_status = 'degraded'

    # Task store check
    try:
        # Attempt a lightweight list_recent (in-memory fast, remote resilient)
        recent = task_store.list_recent(limit=5)
        checks['task_store'] = {
            'reachable': True,
            'recent_count': len(recent),
            'status': 'ok'
        }
    except Exception as e:
        checks['task_store'] = {
            'reachable': False,
            'error': str(e),
            'status': 'error'
        }
        overall_status = 'error'

    # In-memory task cache stats
    with status_lock:
        active = [t for t in processing_status.values() if t.get('status') not in ('completed', 'error')]
        checks['runtime'] = {
            'cached_total': len(processing_status),
            'active_tasks': len(active),
            'status': 'ok'
        }

    response = {
        'status': overall_status,
        'time': datetime.utcnow().isoformat() + 'Z',
        'checks': checks
    }
    http_code = 200 if overall_status == 'ok' else 503 if overall_status == 'error' else 206
    return jsonify(response), http_code

if __name__ == '__main__':
    load_env()

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Run the app
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))  # Use PORT env var if set, default to 5000
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
