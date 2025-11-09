#!/usr/bin/env python3
"""
Flask web application for the video fetcher.
Provides a web interface with dark mode, real-time progress, and API endpoints.
"""

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, render_template, request, jsonify, send_from_directory

from video_config import VideoConfig
from video_fetcher import VideoFetcher
from video_sources import PixabayVideoSource


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Global state for job management
jobs: Dict[int, Dict] = {}
job_counter = 0
job_lock = threading.Lock()


def create_job() -> int:
    """Create a new job and return its ID."""
    global job_counter
    with job_lock:
        job_counter += 1
        job_id = job_counter
        jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "progress": "Initializing...",
            "current": 0,
            "total": 0,
            "successful": 0,
            "failed": 0,
            "result_dir": None,
            "error": None,
            "created_at": datetime.now().isoformat()
        }
        return job_id


def update_job(job_id: int, **kwargs):
    """Update job status thread-safely."""
    with job_lock:
        if job_id in jobs:
            jobs[job_id].update(kwargs)


def get_job(job_id: int) -> Optional[Dict]:
    """Get job status thread-safely."""
    with job_lock:
        return jobs.get(job_id, {}).copy() if job_id in jobs else None


def run_fetch_job(
    job_id: int,
    theme: str,
    count: int,
    sources: str,
    quality: str,
    filters: Dict
):
    """Background job for fetching videos."""
    try:
        update_job(job_id, status="running", progress="Loading configuration...")

        # Load config and create fetcher
        config = VideoConfig.load_config()
        fetcher = VideoFetcher(config)

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

        # Fetch videos
        result_dir = fetcher.fetch_and_process(
            theme=theme,
            num_videos=count,
            sources=sources,
            quality=quality,
            progress_callback=progress_callback,
            **filters
        )

        # Get final stats
        job = get_job(job_id)
        successful = job.get("successful", 0)
        failed = job.get("failed", 0)

        update_job(
            job_id,
            status="completed",
            progress=f"Complete! {successful} videos downloaded, {failed} failed",
            result_dir=result_dir
        )

    except Exception as e:
        update_job(
            job_id,
            status="failed",
            progress=f"Error: {str(e)}",
            error=str(e)
        )


@app.route('/')
def index():
    """Render the main page."""
    config = VideoConfig.load_config()
    fetcher = VideoFetcher(config)

    # Get available sources
    available_sources = fetcher.source_manager.get_available_sources()

    # Get API key status
    api_keys = {
        "pexels": bool(config.get("pexels_api_key")),
        "pixabay": bool(config.get("pixabay_api_key"))
    }

    # Get categories (from Pixabay)
    categories = PixabayVideoSource.CATEGORIES

    # Get theme setting
    theme = config.get("theme", "dark")

    return render_template(
        'video_index.html',
        available_sources=available_sources,
        api_keys=api_keys,
        categories=categories,
        theme=theme
    )


@app.route('/api/fetch', methods=['POST'])
def api_fetch():
    """
    API endpoint to start a video fetch job.

    POST JSON:
    {
        "theme": "string",
        "count": integer (1-100),
        "sources": "all|pexels|pixabay",
        "quality": "hd|medium|high",
        "orientation": "landscape|portrait|square" (optional),
        "category": "string" (optional),
        "min_duration": integer (optional),
        "max_duration": integer (optional)
    }

    Returns:
    {
        "job_id": integer
    }
    """
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
    if data.get('orientation'):
        filters['orientation'] = data['orientation']
    if data.get('category'):
        filters['category'] = data['category']
    if data.get('min_duration'):
        try:
            filters['min_duration'] = int(data['min_duration'])
        except (ValueError, TypeError):
            pass
    if data.get('max_duration'):
        try:
            filters['max_duration'] = int(data['max_duration'])
        except (ValueError, TypeError):
            pass

    # Create job
    job_id = create_job()

    # Start background thread
    thread = threading.Thread(
        target=run_fetch_job,
        args=(job_id, theme, count, sources, quality, filters),
        daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route('/api/status/<int:job_id>')
def api_status(job_id: int):
    """
    Get the status of a job.

    Returns:
    {
        "id": integer,
        "status": "queued|running|completed|failed",
        "progress": "string",
        "current": integer,
        "total": integer,
        "successful": integer,
        "failed": integer,
        "result_dir": "string" or null,
        "error": "string" or null
    }
    """
    job = get_job(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job)


@app.route('/api/jobs')
def api_jobs():
    """
    Get all jobs.

    Returns:
    {
        "jobs": [...]
    }
    """
    with job_lock:
        all_jobs = list(jobs.values())

    # Sort by ID descending (newest first)
    all_jobs.sort(key=lambda x: x['id'], reverse=True)

    return jsonify({"jobs": all_jobs})


@app.route('/api/setup', methods=['POST'])
def api_setup():
    """
    Update API keys configuration.

    POST JSON:
    {
        "pexels_key": "string" (optional),
        "pixabay_key": "string" (optional),
        "theme": "dark|light" (optional)
    }

    Returns:
    {
        "success": true
    }
    """
    data = request.get_json()

    config = VideoConfig.load_config()

    # Update API keys if provided
    if data.get('pexels_key'):
        config['pexels_api_key'] = data['pexels_key'].strip()

    if data.get('pixabay_key'):
        config['pixabay_api_key'] = data['pixabay_key'].strip()

    # Update theme if provided
    if data.get('theme') in ['dark', 'light']:
        config['theme'] = data['theme']

    # Save configuration
    VideoConfig.save_config(config)

    return jsonify({"success": True})


@app.route('/api/config')
def api_config():
    """
    Get current configuration (without sensitive data).

    Returns:
    {
        "has_pexels_key": boolean,
        "has_pixabay_key": boolean,
        "theme": "dark|light",
        "default_quality": string,
        "default_source": string
    }
    """
    config = VideoConfig.load_config()

    return jsonify({
        "has_pexels_key": bool(config.get("pexels_api_key")),
        "has_pixabay_key": bool(config.get("pixabay_api_key")),
        "theme": config.get("theme", "dark"),
        "default_quality": config.get("default_quality", "hd"),
        "default_source": config.get("default_source", "all")
    })


@app.route('/videos/<path:filepath>')
def serve_video(filepath):
    """Serve downloaded videos."""
    config = VideoConfig.load_config()
    output_dir = config.get("output_dir", "video_collections")

    # Security: prevent path traversal
    safe_path = Path(output_dir).resolve()
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
        "timestamp": datetime.now().isoformat()
    })


def main():
    """Run the Flask development server."""
    import argparse

    parser = argparse.ArgumentParser(description="Video Fetcher Web Application")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5001, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Video Fetcher Web Application")
    print("="*60)
    print(f"\nStarting server at http://{args.host}:{args.port}")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug,
        threaded=True
    )


if __name__ == '__main__':
    main()
