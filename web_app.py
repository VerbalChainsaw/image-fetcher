#!/usr/bin/env python3
"""
Web interface for Image Fetcher using Flask
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
import threading
from config import Config
from image_fetcher import ImageFetcher

app = Flask(__name__)
config = Config()
fetcher = ImageFetcher(config)

# Store job status
jobs = {}
job_counter = 0
job_lock = threading.Lock()


def run_fetch_job(job_id, theme, count, sources, category):
    """Background job to fetch images"""
    global jobs

    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['progress'] = 'Searching for images...'

        result_dir = fetcher.fetch_and_process(theme, count, sources, category)

        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = f'Completed! Images saved to: {result_dir}'
        jobs[job_id]['result_dir'] = str(result_dir)

    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['progress'] = f'Error: {str(e)}'


@app.route('/')
def index():
    """Main page"""
    available_sources = fetcher.source_manager.get_available_sources()

    return render_template('index.html',
                         sources=available_sources,
                         has_pexels=config.get_api_key('pexels') != '',
                         has_pixabay=config.get_api_key('pixabay') != '')


@app.route('/api/fetch', methods=['POST'])
def fetch_images():
    """API endpoint to start fetching images"""
    global job_counter

    data = request.json
    theme = data.get('theme', '').strip()
    count = int(data.get('count', 10))
    sources = data.get('sources', 'all')
    category = data.get('category', '').strip() or None

    if not theme:
        return jsonify({'error': 'Theme is required'}), 400

    if count <= 0 or count > 100:
        return jsonify({'error': 'Count must be between 1 and 100'}), 400

    # Create job
    with job_lock:
        job_counter += 1
        job_id = job_counter
        jobs[job_id] = {
            'id': job_id,
            'theme': theme,
            'count': count,
            'status': 'queued',
            'progress': 'Queued...'
        }

    # Start background thread
    thread = threading.Thread(target=run_fetch_job,
                             args=(job_id, theme, count, sources, category))
    thread.daemon = True
    thread.start()

    return jsonify({'job_id': job_id})


@app.route('/api/status/<int:job_id>')
def job_status(job_id):
    """Get job status"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(job)


@app.route('/api/setup', methods=['POST'])
def setup_api_keys():
    """Setup API keys"""
    data = request.json
    pexels_key = data.get('pexels_key', '').strip()
    pixabay_key = data.get('pixabay_key', '').strip()

    if pexels_key:
        config.set_api_key('pexels', pexels_key)
    if pixabay_key:
        config.set_api_key('pixabay', pixabay_key)

    return jsonify({'success': True})


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve downloaded images"""
    output_dir = Path('image_collections')
    return send_from_directory(output_dir, filename)


def run_web_app(host='127.0.0.1', port=5000, debug=False):
    """Run the web application"""
    print("\n" + "="*60)
    print("Image Fetcher - Web Interface")
    print("="*60)
    print(f"\nOpen your browser and navigate to:")
    print(f"  http://{host}:{port}")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_web_app(debug=True)
