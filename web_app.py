#!/usr/bin/env python3
"""
Web interface for Image Fetcher using Flask
Enhanced v2.0 with better UI and features
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
import threading
import json
import glob
import os
from datetime import datetime
from config import Config
from image_fetcher import ImageFetcher

app = Flask(__name__)
config = Config()
fetcher = ImageFetcher(config)

# Store job status and results
jobs = {}
job_counter = 0
job_lock = threading.Lock()


def run_fetch_job(job_id, theme, count, sources, category, width, height, skip_duplicates):
    """Background job to fetch images"""
    global jobs

    try:
        with job_lock:
            jobs[job_id]['status'] = 'running'
            jobs[job_id]['progress'] = 'Searching for images...'
            jobs[job_id]['percent'] = 10

        # Create fetcher with custom size
        job_fetcher = ImageFetcher(config, target_size=(width, height), skip_duplicates=skip_duplicates)
        result_dir = job_fetcher.fetch_and_process(theme, count, sources, category)

        # Read metadata to get stats
        metadata_file = Path(result_dir) / 'metadata.json'
        stats = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                stats = {
                    'saved': metadata.get('actual_count', 0),
                    'duplicates': metadata.get('duplicate_count', 0),
                    'failed': metadata.get('failed_count', 0),
                    'duration': metadata.get('duration_seconds', 0)
                }

        with job_lock:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['progress'] = f'Completed! Images saved to: {result_dir}'
            jobs[job_id]['result_dir'] = str(result_dir)
            jobs[job_id]['percent'] = 100
            jobs[job_id]['stats'] = stats

    except Exception as e:
        with job_lock:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['progress'] = f'Error: {str(e)}'
            jobs[job_id]['percent'] = 0


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
    width = int(data.get('width', 1920))
    height = int(data.get('height', 1080))
    skip_duplicates = data.get('skip_duplicates', True)  # Default to True

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
            'progress': 'Queued...',
            'percent': 0,
            'skip_duplicates': skip_duplicates
        }

    # Start background thread
    thread = threading.Thread(target=run_fetch_job,
                             args=(job_id, theme, count, sources, category, width, height, skip_duplicates))
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


@app.route('/api/results/<int:job_id>')
def get_results(job_id):
    """Get results of a completed job"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400

    result_dir = Path(job.get('result_dir', ''))
    if not result_dir.exists():
        return jsonify({'error': 'Results not found'}), 404

    # Load metadata
    metadata_file = result_dir / 'metadata.json'
    metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except:
            pass

    # Get images
    images = []
    for img_file in sorted(result_dir.glob('*.jpg')):
        # Find metadata for this image
        img_meta = next((m for m in metadata.get('images', [])
                        if m['filename'] == img_file.name), {})

        images.append({
            'path': f'/images/{result_dir.name}/{img_file.name}',
            'title': img_meta.get('title', img_file.stem),
            'photographer': img_meta.get('photographer', 'Unknown'),
            'source': img_meta.get('source', 'Unknown')
        })

    return jsonify({
        'images': images,
        'metadata': metadata
    })


@app.route('/api/history')
def get_history():
    """Get download history from metadata files"""
    output_dir = Path('image_collections')
    if not output_dir.exists():
        return jsonify({'history': []})

    history = []
    for meta_file in sorted(output_dir.glob('*/metadata.json'), reverse=True):
        try:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)

            history.append({
                'theme': metadata.get('theme', 'Unknown'),
                'timestamp': metadata.get('timestamp', ''),
                'count': metadata.get('actual_count', 0),
                'sources': metadata.get('sources', 'all'),
                'size': f"{metadata.get('target_size', [0, 0])[0]}x{metadata.get('target_size', [0, 0])[1]}",
                'success_rate': f"{metadata.get('actual_count', 0)}/{metadata.get('actual_count', 0) + metadata.get('failed_count', 0)}",
                'duration': metadata.get('duration_seconds', 0)
            })
        except:
            continue

    return jsonify({'history': history[:20]})  # Return last 20


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve downloaded images"""
    output_dir = Path('image_collections')
    return send_from_directory(output_dir, filename)


@app.route('/api/db-stats')
def get_db_stats():
    """Get database statistics"""
    try:
        from image_db import ImageDatabase
        db = ImageDatabase()

        total_images = db.get_total_images()
        stats_by_source = {}

        for source in ['pexels', 'pixabay', 'duckduckgo']:
            source_stats = db.get_stats_by_source(source)
            stats_by_source[source] = [
                {
                    'theme': row['theme'],
                    'downloaded': row['total_downloaded'],
                    'duplicates': row['total_duplicates'],
                    'failed': row['total_failed']
                }
                for row in source_stats[:5]  # Top 5 themes per source
            ]

        db.close()

        return jsonify({
            'total_images': total_images,
            'by_source': stats_by_source
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
