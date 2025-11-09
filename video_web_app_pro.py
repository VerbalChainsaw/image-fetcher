#!/usr/bin/env python3
"""
Professional Video Fetcher Web Application.

Features:
- WebSocket for real-time updates
- Statistics dashboard with analytics
- Video preview and gallery
- Download history
- Advanced search with autocomplete
- Export functionality
- RESTful API
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread
from typing import Dict, Optional

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

from video_config import VideoConfig
from video_fetcher_pro import VideoFetcherPro
from video_database import VideoDatabase
from video_sources import PixabayVideoSource


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('video_web_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'video-fetcher-pro-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False
)

# Initialize database
db = VideoDatabase()

# Global state for job management
jobs: Dict[int, Dict] = {}
job_counter = 0


def create_job(theme: str, count: int, sources: str) -> int:
    """Create a new job."""
    global job_counter
    job_counter += 1
    job_id = job_counter

    jobs[job_id] = {
        "id": job_id,
        "theme": theme,
        "count": count,
        "sources": sources,
        "status": "queued",
        "progress": "Initializing...",
        "current": 0,
        "total": count,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "result_dir": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "speed_mbps": 0.0
    }

    logger.info(f"Created job {job_id}: {theme} ({count} videos)")
    return job_id


def update_job(job_id: int, **kwargs):
    """Update job and broadcast via WebSocket."""
    if job_id in jobs:
        jobs[job_id].update(kwargs)

        # Broadcast update to all connected clients
        socketio.emit('job_update', jobs[job_id], namespace='/', broadcast=True)


def run_fetch_job_async(
    job_id: int,
    theme: str,
    count: int,
    sources: str,
    quality: str,
    filters: Dict
):
    """Background job for fetching videos with async support."""
    try:
        update_job(job_id, status="running", progress="Loading configuration...")

        # Load config and create fetcher
        config = VideoConfig.load_config()
        fetcher = VideoFetcherPro(config)

        update_job(job_id, progress="Searching for videos...", total=count)

        # Progress callback
        def progress_callback(successful, failed, total):
            current = successful + failed
            update_job(
                job_id,
                current=current,
                successful=successful,
                failed=failed,
                progress=f"Downloaded {successful}/{total} videos ({failed} failed)"
            )

        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run async fetch
            result_dir = loop.run_until_complete(
                fetcher.fetch_and_process_async(
                    theme=theme,
                    num_videos=count,
                    sources=sources,
                    quality=quality,
                    progress_callback=progress_callback,
                    **filters
                )
            )

            # Get final stats
            job = jobs.get(job_id, {})
            successful = job.get("successful", 0)
            failed = job.get("failed", 0)
            skipped = job.get("skipped", 0)

            update_job(
                job_id,
                status="completed",
                progress=f"Complete! {successful} videos downloaded, {failed} failed, {skipped} skipped",
                result_dir=result_dir
            )

            logger.info(f"Job {job_id} completed: {successful}/{count} successful")

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
        update_job(
            job_id,
            status="failed",
            progress=f"Error: {str(e)[:200]}",
            error=str(e)
        )


@app.route('/')
def index():
    """Render main page."""
    config = VideoConfig.load_config()

    # Get available sources
    pexels_key = config.get("pexels_api_key")
    pixabay_key = config.get("pixabay_api_key")

    available_sources = []
    if pexels_key:
        available_sources.append("pexels")
    if pixabay_key:
        available_sources.append("pixabay")

    # API key status
    api_keys = {
        "pexels": bool(pexels_key),
        "pixabay": bool(pixabay_key)
    }

    # Categories
    categories = PixabayVideoSource.CATEGORIES

    # Theme
    theme = config.get("theme", "dark")

    return render_template(
        'video_index_pro.html',
        available_sources=available_sources,
        api_keys=api_keys,
        categories=categories,
        theme=theme
    )


@app.route('/api/fetch', methods=['POST'])
def api_fetch():
    """Start a video fetch job."""
    data = request.get_json()

    # Validate input
    theme = data.get('theme', '').strip()
    if not theme:
        return jsonify({"error": "Theme is required"}), 400

    count = data.get('count', 10)
    try:
        count = int(count)
        if not 1 <= count <= 100:
            return jsonify({"error": "Count must be between 1 and 100"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid count"}), 400

    sources = data.get('sources', 'all')
    quality = data.get('quality', 'hd')

    # Build filters
    filters = {}
    for key in ['orientation', 'category', 'min_duration', 'max_duration']:
        if data.get(key):
            filters[key] = data[key]

    # Create job
    job_id = create_job(theme, count, sources)

    # Start background thread
    thread = Thread(
        target=run_fetch_job_async,
        args=(job_id, theme, count, sources, quality, filters),
        daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route('/api/status/<int:job_id>')
def api_status(job_id: int):
    """Get job status."""
    job = jobs.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job)


@app.route('/api/jobs')
def api_jobs():
    """Get all jobs."""
    all_jobs = list(jobs.values())
    all_jobs.sort(key=lambda x: x['id'], reverse=True)
    return jsonify({"jobs": all_jobs[:50]})  # Limit to 50 most recent


@app.route('/api/stats')
def api_stats():
    """Get download statistics."""
    days = request.args.get('days', 30, type=int)
    stats = db.get_download_stats(days)
    return jsonify(stats)


@app.route('/api/history')
def api_history():
    """Get download history."""
    limit = request.args.get('limit', 50, type=int)
    history = db.get_recent_downloads(limit)
    return jsonify({"history": history})


@app.route('/api/search/suggestions')
def api_search_suggestions():
    """Get search suggestions."""
    prefix = request.args.get('q', '')
    if len(prefix) < 2:
        return jsonify({"suggestions": []})

    suggestions = db.get_search_suggestions(prefix, limit=10)
    return jsonify({"suggestions": suggestions})


@app.route('/api/themes/popular')
def api_popular_themes():
    """Get popular themes."""
    limit = request.args.get('limit', 20, type=int)
    themes = db.get_popular_themes(limit)
    return jsonify({"themes": [{"theme": t[0], "count": t[1]} for t in themes]})


@app.route('/api/setup', methods=['POST'])
def api_setup():
    """Update configuration."""
    data = request.get_json()

    config = VideoConfig.load_config()

    # Update API keys
    if data.get('pexels_key'):
        config['pexels_api_key'] = data['pexels_key'].strip()
    if data.get('pixabay_key'):
        config['pixabay_api_key'] = data['pixabay_key'].strip()

    # Update theme
    if data.get('theme') in ['dark', 'light']:
        config['theme'] = data['theme']

    # Update other settings
    if 'parallel_downloads' in data:
        try:
            parallel = int(data['parallel_downloads'])
            if 1 <= parallel <= 10:
                config['parallel_downloads'] = parallel
        except (ValueError, TypeError):
            pass

    VideoConfig.save_config(config)

    return jsonify({"success": True})


@app.route('/api/config')
def api_config():
    """Get current configuration."""
    config = VideoConfig.load_config()

    return jsonify({
        "has_pexels_key": bool(config.get("pexels_api_key")),
        "has_pixabay_key": bool(config.get("pixabay_api_key")),
        "theme": config.get("theme", "dark"),
        "default_quality": config.get("default_quality", "hd"),
        "default_source": config.get("default_source", "all"),
        "parallel_downloads": config.get("parallel_downloads", 3),
        "max_file_size_mb": config.get("max_file_size_mb", 100)
    })


@app.route('/api/export/metadata/<int:job_id>')
def api_export_metadata(job_id: int):
    """Export job metadata as JSON."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job['status'] != 'completed' or not job.get('result_dir'):
        return jsonify({"error": "Job not completed"}), 400

    metadata_path = Path(job['result_dir']) / 'metadata.json'
    if not metadata_path.exists():
        return jsonify({"error": "Metadata not found"}), 404

    return send_from_directory(
        Path(job['result_dir']),
        'metadata.json',
        as_attachment=True,
        download_name=f"{job['theme']}_metadata.json"
    )


@app.route('/videos/<path:filepath>')
def serve_video(filepath):
    """Serve downloaded videos."""
    config = VideoConfig.load_config()
    output_dir = Path(config.get("output_dir", "video_collections"))

    # Security: prevent path traversal
    safe_path = output_dir.resolve()
    requested_path = (safe_path / filepath).resolve()

    if not str(requested_path).startswith(str(safe_path)):
        return "Access denied", 403

    if requested_path.is_file():
        return send_from_directory(safe_path, filepath)
    else:
        return "File not found", 404


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db else "error",
        "jobs_count": len(jobs)
    })


@app.route('/api/cleanup', methods=['POST'])
def api_cleanup():
    """Cleanup old records."""
    data = request.get_json()
    days = data.get('days', 90)

    try:
        db.cleanup_old_records(days)
        db.vacuum()
        return jsonify({"success": True, "message": f"Cleaned up records older than {days} days"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected")
    emit('connection_response', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected")


@socketio.on('subscribe_job')
def handle_subscribe(data):
    """Subscribe to job updates."""
    job_id = data.get('job_id')
    if job_id and job_id in jobs:
        emit('job_update', jobs[job_id])


def main():
    """Run the Flask-SocketIO server."""
    import argparse

    parser = argparse.ArgumentParser(description="Professional Video Fetcher Web Application")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5001, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print("\n" + "="*70)
    print(" Professional Video Fetcher Web Application")
    print("="*70)
    print(f"\n Starting server at http://{args.host}:{args.port}")
    print("\n Features:")
    print("  • Real-time updates via WebSocket")
    print("  • Statistics dashboard")
    print("  • Download history")
    print("  • Video validation")
    print("  • Resume capability")
    print("  • Duplicate detection")
    print("\n Press Ctrl+C to stop the server\n")

    socketio.run(
        app,
        host=args.host,
        port=args.port,
        debug=args.debug,
        use_reloader=False,  # Disable reloader to prevent double execution
        log_output=not args.debug
    )


if __name__ == '__main__':
    main()
