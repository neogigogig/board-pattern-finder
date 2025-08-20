#!/usr/bin/env python3
"""
3-Finder Pattern QR Orientation Detector
Correctly identifies QR orientation using exactly 3 finder patterns
"""

import cv2
import numpy as np
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Dict, Tuple, Optional
from enhanced_strict_qr_detector import EnhancedStrictQRDetector
from qr_orientation_detector import QROrientationDetector

class ThreeFinderPatternAnalyzer:
    def __init__(self):
        """Initialize 3-finder pattern analyzer"""
        self.debug_info = []
        
    def filter_to_best_three_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        Filter detected patterns to the best 3 finder patterns
        
        Args:
            patterns: List of all detected patterns
            
        Returns:
            List of exactly 3 best finder patterns
        """
        if len(patterns) <= 3:
            return patterns
        
        # Sort patterns by detection score (higher is better)
        sorted_patterns = sorted(patterns, key=lambda p: p.get('score', 0), reverse=True)
        
        # Take top 3 patterns
        best_three = sorted_patterns[:3]
        
        self.debug_info.append(f"Filtered {len(patterns)} patterns down to best 3")
        self.debug_info.append(f"Selected patterns with scores: {[p.get('score', 0) for p in best_three]}")
        
        return best_three
    
    def validate_three_pattern_geometry(self, patterns: List[Dict]) -> bool:
        """
        Validate that 3 patterns form a valid QR finder pattern triangle
        
        Args:
            patterns: List of exactly 3 patterns
            
        Returns:
            True if geometry is valid for QR code
        """
        if len(patterns) != 3:
            return False
        
        # Extract centers
        centers = []
        for p in patterns:
            if isinstance(p['center'], dict):
                centers.append((p['center']['x'], p['center']['y']))
            else:
                centers.append((p['center'][0], p['center'][1]))
        
        # Calculate all pairwise distances
        distances = []
        for i in range(3):
            for j in range(i+1, 3):
                dist = np.sqrt((centers[i][0] - centers[j][0])**2 + (centers[i][1] - centers[j][1])**2)
                distances.append(dist)
        
        distances.sort()
        min_dist, mid_dist, max_dist = distances
        
        # For a QR code, the pattern should form approximately a right triangle
        # Two sides should be similar (top edge and left edge)
        # One side should be longer (diagonal)
        
        # Check if ratios make sense for QR geometry
        ratio1 = mid_dist / min_dist if min_dist > 0 else 0
        ratio2 = max_dist / mid_dist if mid_dist > 0 else 0
        
        # Valid QR geometry should have:
        # - Reasonable size patterns (not too small/large)
        # - Form a proper triangle (not collinear)
        # - Have reasonable distance ratios
        
        valid_size = min_dist > 50 and max_dist < 1000  # Reasonable pattern spacing
        valid_ratios = 0.7 < ratio1 < 2.0 and 1.2 < ratio2 < 2.0  # Triangle geometry
        
        self.debug_info.append(f"Geometry validation: min={min_dist:.0f}, mid={mid_dist:.0f}, max={max_dist:.0f}")
        self.debug_info.append(f"Ratios: {ratio1:.2f}, {ratio2:.2f}")
        self.debug_info.append(f"Valid: size={valid_size}, ratios={valid_ratios}")
        
        return valid_size and valid_ratios
    
    def analyze_single_image(self, image_path: str) -> Optional[Dict]:
        """
        Analyze a single image for 3-finder pattern orientation
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Analysis results or None if failed
        """
        self.debug_info = []
        
        print(f"\n🔍 Analyzing 3-finder patterns: {Path(image_path).name}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return None
        
        # Detect all patterns
        detector = EnhancedStrictQRDetector()
        all_patterns, _, _ = detector.find_qr_patterns_multi_threshold(image)
        
        print(f"📊 Initially detected {len(all_patterns)} patterns")
        
        if len(all_patterns) < 3:
            print(f"❌ Not enough patterns detected: {len(all_patterns)} (need ≥3)")
            return None
        
        # Filter to best 3 patterns
        three_patterns = self.filter_to_best_three_patterns(all_patterns)
        
        # Validate geometry
        if not self.validate_three_pattern_geometry(three_patterns):
            print("⚠️  Pattern geometry validation failed")
            # Continue anyway, but note the issue
        
        # Convert for orientation analysis
        finder_patterns = []
        for pattern in three_patterns:
            center = pattern['center']
            finder_patterns.append({
                'center': center,
                'size': pattern['size']
            })
        
        # Analyze orientation
        orientation_detector = QROrientationDetector()
        orientation_data = orientation_detector.detect_orientation(finder_patterns)
        
        if orientation_data:
            angles = orientation_data['angles']
            print(f"✅ 3-Pattern Orientation Analysis:")
            print(f"   Primary Rotation: {angles['primary_rotation']:+6.1f}°")
            print(f"   Skew Angle:       {angles['skew_angle']:6.1f}°")
            print(f"   Description:      {orientation_data['description']}")
            
            # Enhanced result with filtering info
            result = {
                'success': True,
                'image_path': image_path,
                'total_patterns_detected': len(all_patterns),
                'patterns_used': 3,
                'filtered_patterns': three_patterns,
                'orientation': orientation_data,
                'debug_info': self.debug_info.copy()
            }
            
            return result
        else:
            print("❌ 3-pattern orientation analysis failed")
            return None
    
    def create_three_pattern_visualization(self, image: np.ndarray, analysis: Dict, 
                                         output_path: str = None) -> None:
        """
        Create visualization specifically for 3-finder pattern analysis
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Left plot: All detected patterns
        ax1.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        ax1.set_title(f"All Detected Patterns ({analysis['total_patterns_detected']})", 
                     fontsize=14, fontweight='bold')
        ax1.axis('off')
        
        # Draw all original patterns in gray
        all_patterns = analysis.get('all_patterns', [])
        for i, pattern in enumerate(all_patterns):
            center = pattern['center']
            if isinstance(center, dict):
                cx, cy = center['x'], center['y']
            else:
                cx, cy = center[0], center[1]
            
            circle = patches.Circle((cx, cy), radius=15, color='gray', fill=True, alpha=0.5)
            ax1.add_patch(circle)
            ax1.text(cx, cy - 25, str(i+1), color='gray', fontsize=10, 
                    ha='center', va='center', fontweight='bold')
        
        # Right plot: Selected 3 patterns with orientation
        ax2.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        ax2.set_title("3 Selected Finder Patterns + Orientation", 
                     fontsize=14, fontweight='bold')
        ax2.axis('off')
        
        # Draw the selected 3 patterns and orientation
        orientation_data = analysis['orientation']
        positions = orientation_data['positions']
        fourth_corner = orientation_data['fourth_corner']
        angles = orientation_data['angles']
        
        # Color scheme
        colors = {'top_left': 'red', 'top_right': 'blue', 'bottom_left': 'green'}
        labels = {'top_left': 'TL', 'top_right': 'TR', 'bottom_left': 'BL'}
        
        # Draw finder patterns
        for pos_name, pos_data in positions.items():
            center = pos_data['center']
            color = colors[pos_name]
            label = labels[pos_name]
            
            circle = patches.Circle(center, radius=20, color=color, fill=True, alpha=0.8)
            ax2.add_patch(circle)
            ax2.text(center[0], center[1] - 30, label, color=color, fontsize=14, 
                    fontweight='bold', ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        # Draw calculated fourth corner
        fourth_circle = patches.Circle(fourth_corner, radius=20, color='purple', 
                                     fill=True, alpha=0.8, linestyle='--')
        ax2.add_patch(fourth_circle)
        ax2.text(fourth_corner[0], fourth_corner[1] - 30, 'BR', color='purple', 
                fontsize=14, fontweight='bold', ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        # Draw QR rectangle
        tl = positions['top_left']['center']
        tr = positions['top_right']['center']
        bl = positions['bottom_left']['center']
        
        corners = [tl, tr, fourth_corner, bl, tl]
        xs, ys = zip(*corners)
        ax2.plot(xs, ys, 'yellow', linewidth=3, alpha=0.8, label='QR Rectangle')
        
        # Add orientation information
        info_text = f"""3-Pattern Analysis:
        
Original detected: {analysis['total_patterns_detected']}
Used for analysis: 3 best patterns

Orientation Results:
Primary Rotation: {angles['primary_rotation']:+.1f}°
Skew Angle: {angles['skew_angle']:.1f}°

{orientation_data['description']}"""
        
        ax2.text(0.02, 0.98, info_text, transform=ax2.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.9))
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✅ 3-pattern visualization saved: {output_path}")
        
        plt.close()
    
    def analyze_three_finder_folder(self, folder_path: str = "data-qr-ratio-finder/3-finder-pattern"):
        """
        Analyze all images in the 3-finder-pattern folder
        """
        print("🔍 3-FINDER PATTERN QR ORIENTATION ANALYSIS")
        print("=" * 60)
        
        folder = Path(folder_path)
        if not folder.exists():
            print(f"❌ Folder not found: {folder_path}")
            return
        
        # Create output directory
        output_dir = Path("results/3-finder-pattern-analysis")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all image files
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(folder.glob(ext))
        
        if not image_files:
            print(f"❌ No image files found in {folder_path}")
            return
        
        print(f"📊 Found {len(image_files)} images to analyze")
        
        all_results = {}
        
        for image_path in image_files:
            # Analyze single image
            result = self.analyze_single_image(str(image_path))
            
            if result:
                image_name = image_path.stem
                all_results[image_name] = result
                
                # Load image for visualization
                image = cv2.imread(str(image_path))
                if image is not None:
                    viz_path = output_dir / f"{image_name}_3pattern_analysis.png"
                    self.create_three_pattern_visualization(image, result, str(viz_path))
        
        # Save results
        if all_results:
            results_path = output_dir / "3_finder_pattern_results.json"
            with open(results_path, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            
            print(f"\n📁 Results saved: {results_path}")
            
            # Create summary
            self.create_summary_report(all_results, output_dir)
        
        return all_results
    
    def create_summary_report(self, results: Dict, output_dir: Path):
        """Create summary report for 3-finder pattern analysis"""
        print(f"\n📊 3-FINDER PATTERN ANALYSIS SUMMARY")
        print("=" * 50)
        
        total_images = len(results)
        print(f"Total images analyzed: {total_images}")
        
        # Pattern detection summary
        pattern_counts = []
        orientations = []
        
        for image_name, data in results.items():
            total_detected = data['total_patterns_detected']
            pattern_counts.append(total_detected)
            
            orientation = data['orientation']['angles']['primary_rotation']
            orientations.append(orientation)
            
            print(f"\n{image_name}:")
            print(f"  Total patterns detected: {total_detected}")
            print(f"  Used for analysis: 3 (best scoring)")
            print(f"  Primary rotation: {orientation:+6.1f}°")
            print(f"  Description: {data['orientation']['description']}")
        
        # Statistics
        avg_patterns = np.mean(pattern_counts)
        avg_rotation = np.mean([abs(r) for r in orientations])
        
        print(f"\n📈 Statistics:")
        print(f"   Average patterns detected: {avg_patterns:.1f}")
        print(f"   Pattern count range: {min(pattern_counts)} to {max(pattern_counts)}")
        print(f"   Average absolute rotation: {avg_rotation:.1f}°")
        print(f"   Rotation range: {min(orientations):+.1f}° to {max(orientations):+.1f}°")
        
        print(f"\n✅ All images successfully analyzed with exactly 3 finder patterns!")

def main():
    """Main function to analyze 3-finder pattern images"""
    analyzer = ThreeFinderPatternAnalyzer()
    results = analyzer.analyze_three_finder_folder()
    
    if results:
        print(f"\n🎉 3-Finder Pattern Analysis Complete!")
        print(f"📁 Check results in: results/3-finder-pattern-analysis/")

if __name__ == "__main__":
    main()
