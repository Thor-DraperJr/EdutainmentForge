"""
EdutainmentForge Web Application

Local web interface for processing Microsoft Learn URLs into podcasts.
Supports single URL processing and batch processing with multi-voice TTS.
"""

import os
import sys
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import threading
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content.fetcher import MSLearnFetcher
from content.processor import ScriptProcessor
from audio.tts import create_tts_service
from audio.multivoice_tts import create_multivoice_tts_service
from utils.config import load_config

app = Flask(__name__)

# Global storage for processing status and batch jobs
processing_status = {}
batch_jobs = {}

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

@app.route('/')
def index():
    """Main page with URL input form and podcast library."""
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

@app.route('/batch')
def batch_page():
    """Batch processing page for multiple URLs."""
    return render_template('batch.html')

@app.route('/library')
def library_page():
    """Podcast library page."""
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
        except Exception as e:
            print(f"Could not load local podcasts: {e}")
    
    return render_template('library.html', podcasts=podcasts)

@app.route('/api/process', methods=['POST'])
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
        
        # Initialize status
        processing_status[task_id] = {
            'status': 'started',
            'progress': 0,
            'message': 'Starting processing...',
            'url': url,
            'voice': voice,
            'created_at': datetime.now().isoformat()
        }
        
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
        processing_status[task_id].update({
            'status': 'fetching',
            'progress': 20,
            'message': 'Fetching content from Microsoft Learn...'
        })
        
        # Load config
        config = load_config()
        if voice:
            config['tts_voice'] = voice
        
        # Fetch content
        fetcher = MSLearnFetcher()
        content = fetcher.fetch_module_content(url)
        
        if not content or not content.get('title') or not content.get('content'):
            processing_status[task_id].update({
                'status': 'error',
                'message': 'Failed to fetch content or content is empty'
            })
            return
        
        # Update status
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
        processing_status[task_id].update({
            'status': 'generating_audio',
            'progress': 70,
            'message': 'Generating audio with Azure Speech Service...'
        })
        
        # Generate audio with multi-voice support
        multivoice_tts = create_multivoice_tts_service(config)
        
        # Create output filename
        clean_title = "".join(c for c in content['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_title = clean_title.replace(' ', '_')[:50]
        output_name = f"{clean_title}_{task_id[:8]}"
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Save script
        script_path = output_dir / f"{output_name}_script.txt"
        script_path.write_text(script)
        
        # Generate audio with multiple voices
        audio_path = output_dir / f"{output_name}.wav"
        success = multivoice_tts.synthesize_dialogue_script(script, audio_path)
        
        if success and audio_path.exists():
            file_size = audio_path.stat().st_size
            
            # Update status - completed
            processing_status[task_id].update({
                'status': 'completed',
                'progress': 100,
                'message': 'Podcast generated successfully!',
                'audio_file': str(audio_path),
                'script_file': str(script_path),
                'title': content['title'],
                'file_size': file_size,
                'duration_estimate': len(script) / 12  # ~12 chars per second
            })
        else:
            processing_status[task_id].update({
                'status': 'error',
                'message': 'Failed to generate audio file'
            })
            
    except Exception as e:
        processing_status[task_id].update({
            'status': 'error',
            'message': f'Processing error: {str(e)}'
        })

@app.route('/api/status/<task_id>')
def get_status(task_id):
    """Get processing status for a task."""
    if task_id not in processing_status:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(processing_status[task_id])

@app.route('/api/audio/<task_id>')
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

@app.route('/api/voices')
def get_voices():
    """Get available Azure voices."""
    voices = {
        "en-US-AriaNeural": "Aria - US English Female, Expressive (recommended for podcasts)",
        "en-US-GuyNeural": "Guy - US English Male, Friendly",
        "en-US-JennyNeural": "Jenny - US English Female, Assistant-like",
        "en-US-DavisNeural": "Davis - US English Male, Conversational",
        "en-GB-LibbyNeural": "Libby - UK English Female",
        "en-GB-RyanNeural": "Ryan - UK English Male",
    }
    return jsonify(voices)

@app.route('/api/process-batch', methods=['POST'])
def process_batch():
    """Process multiple Microsoft Learn URLs as a batch."""
    return jsonify({'error': 'Batch processing temporarily disabled for demo'}), 501

@app.route('/api/batch-status/<batch_id>')
def get_batch_status(batch_id):
    """Get batch processing status."""
    if batch_id not in batch_jobs:
        return jsonify({'error': 'Batch not found'}), 404
    
    return jsonify(batch_jobs[batch_id])

@app.route('/api/batches')
def list_batches():
    """List all batch jobs."""
    # Return recent batches (last 10)
    recent_batches = list(batch_jobs.values())[-10:]
    recent_batches.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({
        'batches': recent_batches,
        'total': len(batch_jobs)
    })

@app.route('/api/podcasts')
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
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
