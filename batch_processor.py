#!/usr/bin/env python3
"""
Batch video download processor.

Features:
- Process downloads from CSV/JSON files
- Bulk operations
- Progress tracking
- Error handling and retry
- Export results
"""

import csv
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from video_fetcher_pro import VideoFetcherPro
from video_config import VideoConfig


logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    """Single batch job entry."""
    theme: str
    count: int
    sources: str = "all"
    quality: str = "hd"
    orientation: Optional[str] = None
    category: Optional[str] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None


class BatchProcessor:
    """Process multiple video downloads in batch."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or VideoConfig.load_config()
        self.fetcher = VideoFetcherPro(self.config)
        self.results = []

    def load_from_csv(self, csv_file: Path) -> List[BatchJob]:
        """
        Load batch jobs from CSV file.

        CSV format:
        theme,count,sources,quality,orientation,category
        ocean waves,10,pexels,hd,landscape,nature
        """
        jobs = []

        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Skip comment lines
                    if row.get('theme', '').startswith('#'):
                        continue

                    job = BatchJob(
                        theme=row['theme'],
                        count=int(row.get('count', 10)),
                        sources=row.get('sources', 'all'),
                        quality=row.get('quality', 'hd'),
                        orientation=row.get('orientation') or None,
                        category=row.get('category') or None,
                        min_duration=int(row['min_duration']) if row.get('min_duration') else None,
                        max_duration=int(row['max_duration']) if row.get('max_duration') else None
                    )

                    jobs.append(job)

            logger.info(f"Loaded {len(jobs)} jobs from CSV")
            return jobs

        except Exception as e:
            logger.error(f"Failed to load CSV: {str(e)}")
            return []

    def load_from_json(self, json_file: Path) -> List[BatchJob]:
        """
        Load batch jobs from JSON file.

        JSON format:
        {
          "jobs": [
            {
              "theme": "ocean waves",
              "count": 10,
              "sources": "pexels",
              "quality": "hd"
            }
          ]
        }
        """
        jobs = []

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            for job_data in data.get('jobs', []):
                job = BatchJob(
                    theme=job_data['theme'],
                    count=job_data.get('count', 10),
                    sources=job_data.get('sources', 'all'),
                    quality=job_data.get('quality', 'hd'),
                    orientation=job_data.get('orientation'),
                    category=job_data.get('category'),
                    min_duration=job_data.get('min_duration'),
                    max_duration=job_data.get('max_duration')
                )

                jobs.append(job)

            logger.info(f"Loaded {len(jobs)} jobs from JSON")
            return jobs

        except Exception as e:
            logger.error(f"Failed to load JSON: {str(e)}")
            return []

    async def process_job(self, job: BatchJob, index: int, total: int) -> Dict:
        """Process a single batch job."""
        print(f"\n[{index + 1}/{total}] Processing: {job.theme} ({job.count} videos)")

        start_time = datetime.now()

        try:
            # Build filters
            filters = {}
            if job.orientation:
                filters['orientation'] = job.orientation
            if job.category:
                filters['category'] = job.category
            if job.min_duration:
                filters['min_duration'] = job.min_duration
            if job.max_duration:
                filters['max_duration'] = job.max_duration

            # Execute download
            result_dir = await self.fetcher.fetch_and_process_async(
                theme=job.theme,
                num_videos=job.count,
                sources=job.sources,
                quality=job.quality,
                **filters
            )

            elapsed = (datetime.now() - start_time).total_seconds()

            result = {
                "theme": job.theme,
                "count": job.count,
                "status": "success",
                "result_dir": result_dir,
                "elapsed_seconds": elapsed,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"✓ Completed {job.theme} in {elapsed:.1f}s")
            return result

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()

            result = {
                "theme": job.theme,
                "count": job.count,
                "status": "failed",
                "error": str(e),
                "elapsed_seconds": elapsed,
                "timestamp": datetime.now().isoformat()
            }

            logger.error(f"✗ Failed {job.theme}: {str(e)[:100]}")
            return result

    async def process_batch(
        self,
        jobs: List[BatchJob],
        sequential: bool = True
    ) -> List[Dict]:
        """
        Process batch of jobs.

        Args:
            jobs: List of batch jobs
            sequential: If True, process one at a time; if False, process concurrently

        Returns:
            List of results
        """
        results = []
        total = len(jobs)

        print(f"\n{'='*70}")
        print(f"  Batch Processing: {total} jobs")
        print(f"  Mode: {'Sequential' if sequential else 'Concurrent'}")
        print(f"{'='*70}\n")

        if sequential:
            # Process one at a time
            for i, job in enumerate(jobs):
                result = await self.process_job(job, i, total)
                results.append(result)

        else:
            # Process concurrently (with semaphore for control)
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent

            async def process_with_semaphore(job, index):
                async with semaphore:
                    return await self.process_job(job, index, total)

            tasks = [
                process_with_semaphore(job, i)
                for i, job in enumerate(jobs)
            ]

            results = await asyncio.gather(*tasks)

        # Summary
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'failed')

        print(f"\n{'='*70}")
        print(f"  Batch Complete!")
        print(f"  Successful: {successful}/{total}")
        print(f"  Failed: {failed}/{total}")
        print(f"{'='*70}\n")

        self.results = results
        return results

    def export_results(self, output_file: Path, format: str = "json"):
        """
        Export batch results.

        Args:
            output_file: Output file path
            format: 'json' or 'csv'
        """
        if not self.results:
            logger.warning("No results to export")
            return

        try:
            if format == "json":
                with open(output_file, 'w') as f:
                    json.dump({
                        "total": len(self.results),
                        "successful": sum(1 for r in self.results if r['status'] == 'success'),
                        "failed": sum(1 for r in self.results if r['status'] == 'failed'),
                        "results": self.results
                    }, f, indent=2)

            elif format == "csv":
                with open(output_file, 'w', newline='') as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=['theme', 'count', 'status', 'result_dir', 'error', 'elapsed_seconds', 'timestamp']
                    )
                    writer.writeheader()
                    writer.writerows(self.results)

            logger.info(f"Results exported to {output_file}")

        except Exception as e:
            logger.error(f"Failed to export results: {str(e)}")


async def main():
    """CLI for batch processing."""
    import argparse

    parser = argparse.ArgumentParser(description="Batch Video Processor")
    parser.add_argument("input", help="Input CSV or JSON file")
    parser.add_argument("--output", help="Output results file")
    parser.add_argument("--concurrent", action="store_true", help="Process concurrently")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")

    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        return

    # Load jobs
    processor = BatchProcessor()

    if input_file.suffix == '.csv':
        jobs = processor.load_from_csv(input_file)
    elif input_file.suffix == '.json':
        jobs = processor.load_from_json(input_file)
    else:
        print(f"Error: Unsupported file type: {input_file.suffix}")
        return

    if not jobs:
        print("Error: No jobs loaded")
        return

    # Process batch
    await processor.process_batch(jobs, sequential=not args.concurrent)

    # Export results
    if args.output:
        processor.export_results(Path(args.output), format=args.format)


if __name__ == "__main__":
    asyncio.run(main())
