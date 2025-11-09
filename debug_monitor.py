#!/usr/bin/env python3
"""
Enhanced debugging, monitoring, and profiling system for Video Fetcher Pro.

Features:
- Performance profiling
- Request/response logging
- Memory tracking
- Error tracking with stack traces
- Health monitoring
- Real-time metrics
- Debug mode with verbose output
"""

import time
import logging
import traceback
import sys
import psutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import json


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Error tracking record."""
    error_type: str
    message: str
    stack_trace: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: deque = deque(maxlen=max_history)
        self.timers: Dict[str, float] = {}
        self.counters: Dict[str, int] = {}
        self._lock = threading.Lock()

    def start_timer(self, name: str):
        """Start a performance timer."""
        self.timers[name] = time.time()

    def stop_timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Stop timer and record metric."""
        if name not in self.timers:
            return

        elapsed = time.time() - self.timers[name]
        self.record_metric(name, elapsed, tags or {})
        del self.timers[name]
        return elapsed

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a performance metric."""
        with self._lock:
            metric = PerformanceMetric(name, value, tags=tags or {})
            self.metrics.append(metric)

    def increment_counter(self, name: str, amount: int = 1):
        """Increment a counter."""
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + amount

    def get_metrics(self, name: Optional[str] = None, since: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get metrics, optionally filtered."""
        with self._lock:
            result = list(self.metrics)

        if name:
            result = [m for m in result if m.name == name]
        if since:
            result = [m for m in result if m.timestamp >= since]

        return result

    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        metrics = self.get_metrics(name)
        if not metrics:
            return {}

        values = [m.value for m in metrics]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "total": sum(values)
        }

    def get_counters(self) -> Dict[str, int]:
        """Get all counters."""
        with self._lock:
            return self.counters.copy()


class ErrorTracker:
    """Track and analyze errors."""

    def __init__(self, max_errors: int = 500):
        self.max_errors = max_errors
        self.errors: deque = deque(maxlen=max_errors)
        self._lock = threading.Lock()

    def track_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Track an error with context."""
        with self._lock:
            record = ErrorRecord(
                error_type=type(error).__name__,
                message=str(error),
                stack_trace=traceback.format_exc(),
                context=context or {}
            )
            self.errors.append(record)

    def get_errors(
        self,
        error_type: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[ErrorRecord]:
        """Get errors, optionally filtered."""
        with self._lock:
            result = list(self.errors)

        if error_type:
            result = [e for e in result if e.error_type == error_type]
        if since:
            result = [e for e in result if e.timestamp >= since]

        return result

    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by type."""
        with self._lock:
            errors = list(self.errors)

        summary = {}
        for error in errors:
            summary[error.error_type] = summary.get(error.error_type, 0) + 1

        return summary


class HealthMonitor:
    """System health monitoring."""

    def __init__(self):
        self.process = psutil.Process()
        self.start_time = datetime.now()

    def get_health(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            cpu_percent = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            # Get system-wide stats
            system_cpu = psutil.cpu_percent(interval=0.1)
            system_memory = psutil.virtual_memory()
            disk_usage = psutil.disk_usage('/')

            uptime = datetime.now() - self.start_time

            return {
                "status": "healthy",
                "uptime_seconds": uptime.total_seconds(),
                "process": {
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_info.rss / 1024 / 1024,
                    "memory_percent": memory_percent,
                    "threads": self.process.num_threads()
                },
                "system": {
                    "cpu_percent": system_cpu,
                    "memory_available_mb": system_memory.available / 1024 / 1024,
                    "memory_percent": system_memory.percent,
                    "disk_free_gb": disk_usage.free / 1024 / 1024 / 1024,
                    "disk_percent": disk_usage.percent
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class DebugLogger:
    """Enhanced debug logging with multiple outputs."""

    def __init__(self, log_dir: str = "logs", debug_mode: bool = False):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.debug_mode = debug_mode

        # Setup logging
        self.logger = logging.getLogger("video_fetcher_debug")
        self.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)

        # File handler with rotation
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            self.log_dir / "debug.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message: str, **kwargs):
        """Debug level log."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Info level log."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Warning level log."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Error level log."""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)

    def log_request(self, method: str, url: str, headers: Dict, **kwargs):
        """Log HTTP request."""
        if self.debug_mode:
            self.debug(f"REQUEST {method} {url}", extra={
                "headers": headers,
                **kwargs
            })

    def log_response(self, status: int, url: str, duration: float, **kwargs):
        """Log HTTP response."""
        if self.debug_mode:
            self.debug(f"RESPONSE {status} {url} ({duration:.2f}s)", extra=kwargs)


class DebugMonitor:
    """Comprehensive debugging and monitoring system."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize monitoring systems."""
        if hasattr(self, '_initialized'):
            return

        self.performance = PerformanceMonitor()
        self.errors = ErrorTracker()
        self.health = HealthMonitor()
        self.logger = DebugLogger(debug_mode=False)
        self._initialized = True

    def enable_debug_mode(self):
        """Enable debug mode."""
        self.logger.debug_mode = True
        self.logger.logger.setLevel(logging.DEBUG)
        for handler in self.logger.logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.DEBUG)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all monitoring data for dashboard."""
        # Get metrics from last hour
        since = datetime.now() - timedelta(hours=1)

        # Performance metrics
        download_metrics = self.performance.get_metrics("download_speed", since)
        search_metrics = self.performance.get_metrics("search_duration", since)

        # Error summary
        error_summary = self.errors.get_error_summary()
        recent_errors = self.errors.get_errors(since=datetime.now() - timedelta(minutes=15))

        # Health
        health = self.health.get_health()

        # Counters
        counters = self.performance.get_counters()

        return {
            "health": health,
            "metrics": {
                "downloads": {
                    "count": len(download_metrics),
                    "stats": self.performance.get_stats("download_speed")
                },
                "searches": {
                    "count": len(search_metrics),
                    "stats": self.performance.get_stats("search_duration")
                }
            },
            "errors": {
                "summary": error_summary,
                "recent": len(recent_errors),
                "details": [
                    {
                        "type": e.error_type,
                        "message": e.message,
                        "timestamp": e.timestamp.isoformat()
                    }
                    for e in recent_errors[:10]
                ]
            },
            "counters": counters,
            "timestamp": datetime.now().isoformat()
        }

    def export_report(self, filepath: str):
        """Export comprehensive debug report."""
        data = self.get_dashboard_data()

        # Add detailed error traces
        data["detailed_errors"] = [
            {
                "type": e.error_type,
                "message": e.message,
                "timestamp": e.timestamp.isoformat(),
                "stack_trace": e.stack_trace,
                "context": e.context
            }
            for e in self.errors.get_errors()
        ]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        self.logger.info(f"Debug report exported to {filepath}")


# Global instance
monitor = DebugMonitor()
