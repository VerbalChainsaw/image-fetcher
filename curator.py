#!/usr/bin/env python3
"""
Intelligent Image Curator - Automated library building and organization

This module provides intelligent curation capabilities for building large
image libraries automatically without manual intervention. Features include:
- Theme expansion and generation
- Quality scoring and filtering
- Automatic categorization
- Scheduled/batch processing
- Collection management
"""

import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from PIL import Image, ImageStat
import math

from config import Config
from image_fetcher import ImageFetcher


# Pre-defined theme templates for different categories
THEME_TEMPLATES = {
    'nature': [
        'mountain landscape sunrise',
        'forest path misty morning',
        'ocean waves sunset',
        'desert sand dunes',
        'waterfall rainforest',
        'alpine lake reflection',
        'autumn forest colors',
        'spring flower meadow',
        'winter snow mountain',
        'coastal cliff ocean',
        'river valley vista',
        'prairie golden hour',
        'jungle canopy green',
        'canyon rock formation',
        'volcanic landscape',
    ],
    'urban': [
        'city skyline night lights',
        'modern architecture building',
        'street photography urban life',
        'downtown financial district',
        'historic town square',
        'industrial warehouse district',
        'subway station commuters',
        'rooftop city view',
        'urban park people',
        'bridge architecture',
        'neon signs nightlife',
        'graffiti street art',
        'market street vendors',
        'skyscraper reflection glass',
        'alleyway brick buildings',
    ],
    'people': [
        'business professional office',
        'diverse team meeting',
        'family outdoor activity',
        'athlete training exercise',
        'artist creative workspace',
        'student studying library',
        'chef cooking kitchen',
        'doctor medical care',
        'elderly couple smiling',
        'children playing park',
        'yoga meditation wellness',
        'musician performing stage',
        'traveler exploring adventure',
        'craftsman working tools',
        'portrait natural light',
    ],
    'business': [
        'startup team collaboration',
        'corporate meeting presentation',
        'office workspace modern',
        'handshake business deal',
        'data analytics dashboard',
        'technology innovation',
        'financial charts growth',
        'coworking space professional',
        'video conference remote',
        'entrepreneur laptop coffee',
        'factory production line',
        'warehouse logistics',
        'retail store customer',
        'restaurant service hospitality',
        'construction site progress',
    ],
    'technology': [
        'artificial intelligence ai',
        'data center servers',
        'cybersecurity network',
        'smartphone mobile app',
        'virtual reality headset',
        'robotics automation',
        'circuit board electronics',
        'programming code developer',
        'cloud computing infrastructure',
        'blockchain cryptocurrency',
        'drone aerial technology',
        '3d printing manufacturing',
        'smart home devices',
        'electric vehicle charging',
        'solar panels renewable energy',
    ],
    'lifestyle': [
        'healthy breakfast food',
        'coffee morning routine',
        'home interior design',
        'garden plants flowers',
        'pet dog playing',
        'fashion style outfit',
        'travel vacation destination',
        'fitness gym workout',
        'meditation mindfulness',
        'reading book cozy',
        'cooking fresh ingredients',
        'bicycle riding outdoor',
        'camping tent nature',
        'beach vacation relaxing',
        'wine dinner celebration',
    ],
    'abstract': [
        'geometric pattern colorful',
        'texture background material',
        'watercolor paint splash',
        'light bokeh blur',
        'gradient smooth color',
        'minimal simple clean',
        'line shape composition',
        'shadow contrast monochrome',
        'motion blur dynamic',
        'reflection symmetry',
        'smoke fluid abstract',
        'crystal geometric structure',
        'metallic surface texture',
        'fabric textile closeup',
        'paper torn texture',
    ],
    'seasonal': [
        'spring flowers blooming',
        'summer beach vacation',
        'autumn leaves falling',
        'winter snow holiday',
        'christmas decorations festive',
        'halloween pumpkin spooky',
        'thanksgiving harvest table',
        'new year celebration fireworks',
        'valentine romance love',
        'easter egg spring',
        'fourth july patriotic',
        'back to school supplies',
        'summer festival outdoor',
        'fall harvest festival',
        'winter sports skiing',
    ],
}


class ImageQualityScorer:
    """Scores image quality based on various metrics"""

    def __init__(self, min_resolution=(800, 600)):
        self.min_resolution = min_resolution

    def score_image(self, image_path: Path) -> Dict:
        """
        Score an image on multiple quality metrics

        Returns:
            dict: {
                'overall_score': 0-100,
                'resolution_score': 0-100,
                'sharpness_score': 0-100,
                'brightness_score': 0-100,
                'contrast_score': 0-100,
                'color_variety_score': 0-100,
                'notes': []
            }
        """
        try:
            img = Image.open(image_path)

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            scores = {
                'resolution_score': self._score_resolution(img),
                'sharpness_score': self._score_sharpness(img),
                'brightness_score': self._score_brightness(img),
                'contrast_score': self._score_contrast(img),
                'color_variety_score': self._score_color_variety(img),
                'notes': []
            }

            # Calculate weighted overall score
            weights = {
                'resolution_score': 0.25,
                'sharpness_score': 0.25,
                'brightness_score': 0.15,
                'contrast_score': 0.20,
                'color_variety_score': 0.15,
            }

            overall = sum(scores[k] * weights[k] for k in weights.keys())
            scores['overall_score'] = round(overall, 2)

            # Add quality notes
            if scores['overall_score'] >= 85:
                scores['notes'].append('excellent_quality')
            elif scores['overall_score'] >= 70:
                scores['notes'].append('good_quality')
            elif scores['overall_score'] >= 50:
                scores['notes'].append('acceptable_quality')
            else:
                scores['notes'].append('low_quality')

            if scores['sharpness_score'] < 40:
                scores['notes'].append('blurry')
            if scores['brightness_score'] < 30 or scores['brightness_score'] > 85:
                scores['notes'].append('poor_exposure')
            if scores['contrast_score'] < 30:
                scores['notes'].append('low_contrast')

            return scores

        except Exception as e:
            logging.error(f"Error scoring image {image_path}: {e}")
            return {
                'overall_score': 0,
                'resolution_score': 0,
                'sharpness_score': 0,
                'brightness_score': 0,
                'contrast_score': 0,
                'color_variety_score': 0,
                'notes': ['error']
            }

    def _score_resolution(self, img: Image.Image) -> float:
        """Score based on resolution"""
        width, height = img.size
        pixels = width * height

        # Score based on megapixels
        # 1MP = 50, 2MP = 65, 4MP = 80, 8MP+ = 100
        mp = pixels / 1_000_000

        if mp >= 8:
            return 100
        elif mp >= 4:
            return 80 + (mp - 4) * 5
        elif mp >= 2:
            return 65 + (mp - 2) * 7.5
        elif mp >= 1:
            return 50 + (mp - 1) * 15
        else:
            return mp * 50

    def _score_sharpness(self, img: Image.Image) -> float:
        """Estimate sharpness using edge detection"""
        # Convert to grayscale
        gray = img.convert('L')

        # Resize for faster processing
        gray = gray.resize((400, 300))

        # Calculate variance of Laplacian (edge detection)
        # Higher variance = sharper image
        pixels = list(gray.getdata())
        width, height = gray.size

        # Simple Laplacian approximation
        edges = []
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                idx = y * width + x
                center = pixels[idx]
                neighbors = [
                    pixels[idx - 1],      # left
                    pixels[idx + 1],      # right
                    pixels[idx - width],  # top
                    pixels[idx + width],  # bottom
                ]
                laplacian = abs(4 * center - sum(neighbors))
                edges.append(laplacian)

        # Calculate variance
        mean_edge = sum(edges) / len(edges)
        variance = sum((e - mean_edge) ** 2 for e in edges) / len(edges)

        # Normalize to 0-100
        # Typical variance ranges from 0-5000
        score = min(100, (variance / 50))
        return score

    def _score_brightness(self, img: Image.Image) -> float:
        """Score based on brightness (prefer well-exposed images)"""
        stat = ImageStat.Stat(img)

        # Average brightness across RGB channels
        avg_brightness = sum(stat.mean[:3]) / 3

        # Ideal brightness is around 128 (middle gray)
        # Score drops as we move toward extremes (0 or 255)
        ideal = 128
        distance = abs(avg_brightness - ideal)

        # Convert distance to score (0 distance = 100, 128 distance = 0)
        score = max(0, 100 - (distance / 128) * 100)
        return score

    def _score_contrast(self, img: Image.Image) -> float:
        """Score based on contrast (tonal range)"""
        stat = ImageStat.Stat(img)

        # Standard deviation indicates spread of values
        avg_stddev = sum(stat.stddev[:3]) / 3

        # Good contrast typically has stddev around 50-80
        # Low contrast < 30, High contrast > 80
        if 50 <= avg_stddev <= 80:
            score = 100
        elif 30 <= avg_stddev < 50:
            score = 50 + ((avg_stddev - 30) / 20) * 50
        elif 80 < avg_stddev <= 100:
            score = 100 - ((avg_stddev - 80) / 20) * 20
        elif avg_stddev < 30:
            score = (avg_stddev / 30) * 50
        else:  # > 100
            score = max(0, 80 - (avg_stddev - 100))

        return max(0, min(100, score))

    def _score_color_variety(self, img: Image.Image) -> float:
        """Score based on color variety and vibrancy"""
        # Resize for faster processing
        small = img.resize((100, 100))
        pixels = list(small.getdata())

        # Calculate color variance
        r_values = [p[0] for p in pixels]
        g_values = [p[1] for p in pixels]
        b_values = [p[2] for p in pixels]

        r_var = self._variance(r_values)
        g_var = self._variance(g_values)
        b_var = self._variance(b_values)

        avg_var = (r_var + g_var + b_var) / 3

        # Normalize (typical variance 0-5000)
        score = min(100, (avg_var / 50))
        return score

    def _variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)


class IntelligentCurator:
    """Main curator class for intelligent library building"""

    def __init__(self, config: Config, curation_config: Dict = None):
        """
        Initialize curator

        Args:
            config: Main Config object
            curation_config: Curation preferences and rules
        """
        self.config = config
        self.fetcher = ImageFetcher(config, skip_duplicates=True)
        self.scorer = ImageQualityScorer()

        # Default curation configuration
        self.curation_config = curation_config or {
            'min_quality_score': 60,  # Minimum overall quality score
            'images_per_theme': 20,
            'target_size': (1920, 1080),
            'preferred_sources': ['pexels', 'pixabay', 'duckduckgo'],
            'categories': ['nature', 'urban', 'abstract'],  # Which categories to curate
            'organize_by_quality': True,  # Organize into quality tiers
            'organize_by_category': True,  # Organize by detected category
            'auto_cleanup_low_quality': False,  # Automatically remove low quality images
        }

        if curation_config:
            self.curation_config.update(curation_config)

        self.stats = {
            'themes_processed': 0,
            'images_downloaded': 0,
            'images_rejected': 0,
            'categories': {},
            'start_time': None,
            'end_time': None,
        }

    def generate_themes(self, category: str, count: int = 15) -> List[str]:
        """
        Generate themes for a category

        Args:
            category: Category name (nature, urban, people, etc.)
            count: Number of themes to generate

        Returns:
            List of theme strings
        """
        if category.lower() in THEME_TEMPLATES:
            themes = THEME_TEMPLATES[category.lower()][:count]
            logging.info(f"Generated {len(themes)} themes for category '{category}'")
            return themes
        else:
            logging.warning(f"Unknown category '{category}', using generic themes")
            return [f"{category} {suffix}" for suffix in [
                'high quality', 'professional', 'beautiful', 'stunning',
                'creative', 'artistic', 'modern', 'classic',
                'vibrant', 'natural', 'authentic', 'inspiring',
                'dramatic', 'elegant', 'dynamic'
            ]][:count]

    def curate_category(self, category: str, output_dir: Path = None) -> Path:
        """
        Curate an entire category automatically

        Args:
            category: Category to curate
            output_dir: Base output directory

        Returns:
            Path to curated collection
        """
        self.stats['start_time'] = datetime.now()

        output_dir = output_dir or Path('curated_collections')
        category_dir = output_dir / category / datetime.now().strftime("%Y%m%d_%H%M%S")
        category_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*70}")
        print(f"🎨 Intelligent Curation: {category.upper()}")
        print(f"{'='*70}")
        print(f"📁 Output: {category_dir}")
        print(f"🎯 Target: {self.curation_config['images_per_theme']} images per theme")
        print(f"✨ Min Quality: {self.curation_config['min_quality_score']}/100")
        print(f"{'='*70}\n")

        # Generate themes
        themes = self.generate_themes(category)
        print(f"📝 Generated {len(themes)} themes for '{category}':\n")
        for i, theme in enumerate(themes, 1):
            print(f"  {i}. {theme}")
        print()

        # Process each theme
        for i, theme in enumerate(themes, 1):
            print(f"\n[{i}/{len(themes)}] Processing: {theme}")
            print("-" * 70)

            try:
                # Download images
                result_dir = self.fetcher.fetch_and_process(
                    theme=theme,
                    num_images=self.curation_config['images_per_theme'],
                    sources=self.curation_config['preferred_sources']
                )

                if result_dir:
                    # Score and filter images
                    self._score_and_organize(result_dir, category_dir, theme)
                    self.stats['themes_processed'] += 1

                # Small delay to be respectful to APIs
                time.sleep(2)

            except Exception as e:
                logging.error(f"Error processing theme '{theme}': {e}")
                print(f"  ✗ Error: {e}")
                continue

        self.stats['end_time'] = datetime.now()

        # Save curation report
        self._save_curation_report(category_dir, category)

        print(f"\n{'='*70}")
        print(f"✅ Curation Complete!")
        print(f"{'='*70}")
        print(f"📊 Themes Processed: {self.stats['themes_processed']}/{len(themes)}")
        print(f"📥 Images Downloaded: {self.stats['images_downloaded']}")
        print(f"⭐ Images Accepted: {self.stats['images_downloaded'] - self.stats['images_rejected']}")
        print(f"❌ Images Rejected: {self.stats['images_rejected']}")
        print(f"⏱️  Duration: {(self.stats['end_time'] - self.stats['start_time']).total_seconds():.1f}s")
        print(f"📁 Location: {category_dir}")
        print(f"{'='*70}\n")

        return category_dir

    def _score_and_organize(self, source_dir: Path, dest_dir: Path, theme: str):
        """Score images and organize by quality"""
        # Create quality tiers
        excellent_dir = dest_dir / 'excellent' if self.curation_config['organize_by_quality'] else dest_dir
        good_dir = dest_dir / 'good' if self.curation_config['organize_by_quality'] else dest_dir
        acceptable_dir = dest_dir / 'acceptable' if self.curation_config['organize_by_quality'] else dest_dir

        for dir_path in [excellent_dir, good_dir, acceptable_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Score all images
        image_files = list(source_dir.glob('*.jpg'))
        scored_images = []

        for img_path in image_files:
            scores = self.scorer.score_image(img_path)
            scored_images.append((img_path, scores))
            self.stats['images_downloaded'] += 1

        # Filter and organize
        for img_path, scores in scored_images:
            overall = scores['overall_score']

            # Filter by minimum quality
            if overall < self.curation_config['min_quality_score']:
                self.stats['images_rejected'] += 1
                if self.curation_config['auto_cleanup_low_quality']:
                    img_path.unlink()  # Delete low quality
                continue

            # Organize by quality tier
            if overall >= 85:
                target_dir = excellent_dir
                tier = 'excellent'
            elif overall >= 70:
                target_dir = good_dir
                tier = 'good'
            else:
                target_dir = acceptable_dir
                tier = 'acceptable'

            # Copy to organized location with quality prefix
            safe_theme = "".join(c for c in theme if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_theme = safe_theme.replace(' ', '_')

            new_name = f"{safe_theme}_{overall:.0f}_{img_path.name}"
            target_path = target_dir / new_name

            # Copy file
            import shutil
            shutil.copy2(img_path, target_path)

            # Save score metadata
            score_file = target_path.with_suffix('.json')
            with open(score_file, 'w') as f:
                json.dump(scores, f, indent=2)

        print(f"  ✓ Scored and organized {len(image_files)} images")
        print(f"    Accepted: {len(image_files) - self.stats['images_rejected']}, "
              f"Rejected: {len([s for _, s in scored_images if s['overall_score'] < self.curation_config['min_quality_score']])}")

    def _save_curation_report(self, output_dir: Path, category: str):
        """Save detailed curation report"""
        report = {
            'category': category,
            'curation_config': self.curation_config,
            'statistics': self.stats,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        }

        report_file = output_dir / 'curation_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logging.info(f"Saved curation report to {report_file}")


def main():
    """CLI interface for curator"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Intelligent Image Curator - Build curated libraries automatically',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Curate a single category
  python curator.py nature

  # Curate multiple categories
  python curator.py nature urban abstract

  # Custom settings
  python curator.py nature --images-per-theme 30 --min-quality 70

  # Show available categories
  python curator.py --list-categories

Available categories:
  nature, urban, people, business, technology, lifestyle, abstract, seasonal
        """
    )

    parser.add_argument('categories', nargs='*', help='Categories to curate')
    parser.add_argument('--list-categories', action='store_true',
                       help='List available categories and exit')
    parser.add_argument('--images-per-theme', type=int, default=20,
                       help='Images to download per theme (default: 20)')
    parser.add_argument('--min-quality', type=int, default=60,
                       help='Minimum quality score 0-100 (default: 60)')
    parser.add_argument('--output', type=str, default='curated_collections',
                       help='Output directory (default: curated_collections)')
    parser.add_argument('--sources', nargs='+',
                       default=['pexels', 'pixabay', 'duckduckgo'],
                       help='Image sources to use')

    args = parser.parse_args()

    # List categories
    if args.list_categories:
        print("\nAvailable categories:")
        print("=" * 60)
        for category, themes in THEME_TEMPLATES.items():
            print(f"\n{category.upper()}")
            print(f"  {len(themes)} themes available")
            print(f"  Examples: {', '.join(themes[:3])}")
        print("\n" + "=" * 60)
        return

    # Validate categories
    if not args.categories:
        parser.print_help()
        return

    # Setup
    config = Config()
    curation_config = {
        'min_quality_score': args.min_quality,
        'images_per_theme': args.images_per_theme,
        'preferred_sources': args.sources,
        'organize_by_quality': True,
        'auto_cleanup_low_quality': False,
    }

    curator = IntelligentCurator(config, curation_config)

    # Process each category
    for category in args.categories:
        if category.lower() not in THEME_TEMPLATES:
            print(f"⚠️  Unknown category '{category}'. Use --list-categories to see available options.")
            continue

        output_dir = Path(args.output)
        curator.curate_category(category, output_dir)

        # Pause between categories
        if len(args.categories) > 1:
            time.sleep(5)


if __name__ == '__main__':
    main()
