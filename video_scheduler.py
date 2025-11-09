"""
Video download scheduler with cron support.

Features:
- Scheduled downloads
- Recurring jobs (daily, weekly, monthly)
- Cron expression support
- Auto-retry failed jobs
- Job queue management
- Email notifications (optional)
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading


logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Schedule types."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


@dataclass
class ScheduledJob:
    """Scheduled download job."""
    id: str
    theme: str
    count: int
    sources: str
    quality: str
    filters: Dict = field(default_factory=dict)
    schedule_type: ScheduleType = ScheduleType.ONCE
    schedule_time: Optional[datetime] = None
    cron_expression: Optional[str] = None
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    runs: int = 0
    failures: int = 0
    max_retries: int = 3
    notify_on_complete: bool = False
    notify_on_error: bool = True


class CronParser:
    """Simple cron expression parser."""

    @staticmethod
    def parse(expression: str) -> Dict:
        """
        Parse cron expression.

        Format: minute hour day month weekday
        Example: "0 2 * * *" = 2:00 AM every day
        """
        parts = expression.strip().split()

        if len(parts) != 5:
            raise ValueError("Invalid cron expression (must have 5 fields)")

        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "weekday": parts[4]
        }

    @staticmethod
    def matches(cron_dict: Dict, dt: datetime) -> bool:
        """Check if datetime matches cron expression."""

        def matches_field(field_value: str, actual_value: int) -> bool:
            if field_value == '*':
                return True
            if '/' in field_value:
                # Step values like */5
                _, step = field_value.split('/')
                return actual_value % int(step) == 0
            if ',' in field_value:
                # List like 1,15,30
                return str(actual_value) in field_value.split(',')
            if '-' in field_value:
                # Range like 1-5
                start, end = map(int, field_value.split('-'))
                return start <= actual_value <= end
            return int(field_value) == actual_value

        return (
            matches_field(cron_dict["minute"], dt.minute) and
            matches_field(cron_dict["hour"], dt.hour) and
            matches_field(cron_dict["day"], dt.day) and
            matches_field(cron_dict["month"], dt.month) and
            matches_field(cron_dict["weekday"], dt.weekday())
        )

    @staticmethod
    def next_run(expression: str, after: datetime = None) -> datetime:
        """Calculate next run time for cron expression."""
        if after is None:
            after = datetime.now()

        cron_dict = CronParser.parse(expression)

        # Start checking from next minute
        check_time = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Check up to 1 year ahead
        for _ in range(365 * 24 * 60):
            if CronParser.matches(cron_dict, check_time):
                return check_time
            check_time += timedelta(minutes=1)

        raise ValueError("Could not find next run time within 1 year")


class VideoScheduler:
    """Manage scheduled video downloads."""

    def __init__(self, storage_file: str = "scheduled_jobs.json"):
        self.storage_file = Path(storage_file)
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running = False
        self.thread = None
        self.callback: Optional[Callable] = None

        self.load_jobs()

    def load_jobs(self):
        """Load jobs from storage."""
        if not self.storage_file.exists():
            return

        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)

            for job_data in data.get('jobs', []):
                job = ScheduledJob(
                    id=job_data['id'],
                    theme=job_data['theme'],
                    count=job_data['count'],
                    sources=job_data['sources'],
                    quality=job_data['quality'],
                    filters=job_data.get('filters', {}),
                    schedule_type=ScheduleType(job_data['schedule_type']),
                    schedule_time=datetime.fromisoformat(job_data['schedule_time']) if job_data.get('schedule_time') else None,
                    cron_expression=job_data.get('cron_expression'),
                    enabled=job_data.get('enabled', True),
                    last_run=datetime.fromisoformat(job_data['last_run']) if job_data.get('last_run') else None,
                    next_run=datetime.fromisoformat(job_data['next_run']) if job_data.get('next_run') else None,
                    runs=job_data.get('runs', 0),
                    failures=job_data.get('failures', 0),
                    max_retries=job_data.get('max_retries', 3)
                )

                self.jobs[job.id] = job

            logger.info(f"Loaded {len(self.jobs)} scheduled jobs")

        except Exception as e:
            logger.error(f"Failed to load jobs: {str(e)}")

    def save_jobs(self):
        """Save jobs to storage."""
        try:
            data = {
                'jobs': [
                    {
                        'id': job.id,
                        'theme': job.theme,
                        'count': job.count,
                        'sources': job.sources,
                        'quality': job.quality,
                        'filters': job.filters,
                        'schedule_type': job.schedule_type.value,
                        'schedule_time': job.schedule_time.isoformat() if job.schedule_time else None,
                        'cron_expression': job.cron_expression,
                        'enabled': job.enabled,
                        'last_run': job.last_run.isoformat() if job.last_run else None,
                        'next_run': job.next_run.isoformat() if job.next_run else None,
                        'runs': job.runs,
                        'failures': job.failures,
                        'max_retries': job.max_retries
                    }
                    for job in self.jobs.values()
                ]
            }

            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save jobs: {str(e)}")

    def add_job(self, job: ScheduledJob) -> str:
        """Add a scheduled job."""
        # Generate ID if not provided
        if not job.id:
            job.id = f"job_{int(time.time())}_{len(self.jobs)}"

        # Calculate next run time
        job.next_run = self._calculate_next_run(job)

        self.jobs[job.id] = job
        self.save_jobs()

        logger.info(f"Added scheduled job: {job.id} (next run: {job.next_run})")
        return job.id

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job."""
        if job_id in self.jobs:
            del self.jobs[job_id]
            self.save_jobs()
            logger.info(f"Removed job: {job_id}")
            return True
        return False

    def enable_job(self, job_id: str):
        """Enable a job."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = True
            self.save_jobs()

    def disable_job(self, job_id: str):
        """Disable a job."""
        if job_id in self.jobs:
            self.jobs[job_id].enabled = False
            self.save_jobs()

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[ScheduledJob]:
        """Get all jobs."""
        return list(self.jobs.values())

    def _calculate_next_run(self, job: ScheduledJob) -> Optional[datetime]:
        """Calculate next run time for job."""
        now = datetime.now()

        if job.schedule_type == ScheduleType.ONCE:
            return job.schedule_time if job.schedule_time and job.schedule_time > now else None

        elif job.schedule_type == ScheduleType.DAILY:
            next_run = job.schedule_time or now
            if next_run <= now:
                next_run = now + timedelta(days=1)
            return next_run.replace(hour=job.schedule_time.hour, minute=job.schedule_time.minute) if job.schedule_time else next_run

        elif job.schedule_type == ScheduleType.WEEKLY:
            # Run once a week
            next_run = now + timedelta(days=7)
            return next_run

        elif job.schedule_type == ScheduleType.MONTHLY:
            # Run once a month
            next_run = now.replace(day=1) + timedelta(days=32)
            next_run = next_run.replace(day=1)
            return next_run

        elif job.schedule_type == ScheduleType.CRON:
            if job.cron_expression:
                try:
                    return CronParser.next_run(job.cron_expression, now)
                except Exception as e:
                    logger.error(f"Invalid cron expression for {job.id}: {str(e)}")

        return None

    def _should_run(self, job: ScheduledJob) -> bool:
        """Check if job should run now."""
        if not job.enabled:
            return False

        if job.next_run is None:
            return False

        if job.failures >= job.max_retries:
            logger.warning(f"Job {job.id} exceeded max retries, disabling")
            job.enabled = False
            self.save_jobs()
            return False

        return datetime.now() >= job.next_run

    async def _execute_job(self, job: ScheduledJob):
        """Execute a scheduled job."""
        logger.info(f"Executing job: {job.id} ({job.theme})")

        try:
            # Call callback if set
            if self.callback:
                await self.callback(job)

            # Update job stats
            job.runs += 1
            job.last_run = datetime.now()
            job.failures = 0  # Reset failures on success

            # Calculate next run
            if job.schedule_type != ScheduleType.ONCE:
                job.next_run = self._calculate_next_run(job)
            else:
                job.enabled = False  # One-time job, disable after run

            self.save_jobs()

            logger.info(f"Job {job.id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job.id} failed: {str(e)}")
            job.failures += 1
            self.save_jobs()

    async def _run_loop(self):
        """Main scheduler loop."""
        logger.info("Scheduler started")

        while self.running:
            try:
                # Check all jobs
                for job in list(self.jobs.values()):
                    if self._should_run(job):
                        await self._execute_job(job)

                # Sleep for 30 seconds
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(60)

        logger.info("Scheduler stopped")

    def start(self, callback: Optional[Callable] = None):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.callback = callback
        self.running = True

        # Start in thread
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._run_loop())

        self.thread = threading.Thread(target=run_async_loop, daemon=True)
        self.thread.start()

        logger.info("Scheduler started in background")

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def get_status(self) -> Dict:
        """Get scheduler status."""
        return {
            "running": self.running,
            "total_jobs": len(self.jobs),
            "enabled_jobs": sum(1 for j in self.jobs.values() if j.enabled),
            "pending_jobs": sum(1 for j in self.jobs.values() if j.enabled and j.next_run and j.next_run > datetime.now()),
            "jobs": [
                {
                    "id": j.id,
                    "theme": j.theme,
                    "enabled": j.enabled,
                    "next_run": j.next_run.isoformat() if j.next_run else None,
                    "last_run": j.last_run.isoformat() if j.last_run else None,
                    "runs": j.runs,
                    "failures": j.failures
                }
                for j in self.jobs.values()
            ]
        }
