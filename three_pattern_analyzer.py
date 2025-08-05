#!/usr/bin/env python3
"""
QR Three-Pattern Fourth Corner Calculator
Specialized analyzer for QR codes with exactly 3 finder patterns to calculate the fourth corner
"""

import cv2
import numpy as np
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Dict, Tuple, Optional

class QRThreePatternAnalyzer:
    def __init__(self, results_dir="results/enhanced-strict-qr-results", data_dir="data-qr-ratio-finder"):
        self.results_dir = Path(results_dir)
        self.data_dir = Path(data_dir)
        self.output_dir = Path("results/three-pattern-analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_detection_results(self) -> Dict:
        """Load detection results for analysis"""
        results = {}
        
        for json_file in self.results_dir.glob("*_results.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    image_name = json_file.stem.replace('_results', '')
                    results[image_name] = data
            except Exception as e:
                print(f"❌ Error loading {json_file}: {e}")
                
        return results
    
    def identify_pattern_positions(self, patterns: List[Dict]) -> Optional[Dict]:
        """
        Identify which pattern is which based on QR code geometry
        Returns: {'top_left': pattern, 'top_right': pattern, 'bottom_left': pattern}
        """
        if len(patterns) != 3:
            return None
            
        # Convert to list of (x, y, pattern) for easier handling
        pattern_coords = []
        for i, pattern in enumerate(patterns):
            center = pattern['center']
            x, y = center['x'], center['y']
            pattern_coords.append((x, y, pattern))
        
        # Sort by x-coordinate to find leftmost patterns
        pattern_coords.sort(key=lambda p: p[0])
        
        # The two leftmost patterns are left side (top-left and bottom-left)
        left_patterns = pattern_coords[:2]
        right_pattern = pattern_coords[2]  # Rightmost is top-right
        
        # Among left patterns, the one with smaller y is top-left, larger y is bottom-left
        left_patterns.sort(key=lambda p: p[1])
        
        return {
            'top_left': left_patterns[0][2],      # Leftmost + smallest Y
            'bottom_left': left_patterns[1][2],   # Leftmost + largest Y  
            'top_right': right_pattern[2]         # Rightmost
        }
    
    def calculate_fourth_corner(self, positions: Dict) -> Tuple[float, float]:
        """
        Calculate the fourth corner (bottom-right) using parallelogram rule
        Fourth corner = top_left + bottom_left - top_right (vector addition)
        """
        tl = positions['top_left']['center']
        bl = positions['bottom_left']['center'] 
        tr = positions['top_right']['center']
        
        # Convert to coordinates
        tl_x, tl_y = tl['x'], tl['y']
        bl_x, bl_y = bl['x'], bl['y']
        tr_x, tr_y = tr['x'], tr['y']
        
        # Parallelogram rule: BR = TL + BL - TR
        br_x = tl_x + bl_x - tr_x
        br_y = tl_y + bl_y - tr_y
        
        return (br_x, br_y)
    
    def validate_qr_geometry(self, positions: Dict, fourth_corner: Tuple[float, float]) -> Dict:
        """
        Validate if the calculated geometry makes sense for a QR code
        """
        tl = positions['top_left']['center']
        bl = positions['bottom_left']['center']
        tr = positions['top_right']['center']
        br = fourth_corner
        
        # Calculate all side lengths
        def distance(p1, p2):
            if isinstance(p1, dict):
                x1, y1 = p1['x'], p1['y']
            else:
                x1, y1 = p1
            if isinstance(p2, dict):
                x2, y2 = p2['x'], p2['y']
            else:
                x2, y2 = p2
            return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Side lengths
        top_side = distance(tl, tr)
        bottom_side = distance(bl, br)
        left_side = distance(tl, bl)
        right_side = distance(tr, br)
        
        # Diagonal lengths
        diagonal_1 = distance(tl, br)
        diagonal_2 = distance(tr, bl)
        
        # Calculate aspect ratio
        width = (top_side + bottom_side) / 2
        height = (left_side + right_side) / 2
        aspect_ratio = width / height if height > 0 else 0
        
        # Calculate area using shoelace formula
        corners = [tl, tr, br, bl]
        area = 0
        for i in range(4):
            j = (i + 1) % 4
            if isinstance(corners[i], dict):
                xi, yi = corners[i]['x'], corners[i]['y']
            else:
                xi, yi = corners[i]
            if isinstance(corners[j], dict):
                xj, yj = corners[j]['x'], corners[j]['y']
            else:
                xj, yj = corners[j]
            area += xi * yj - xj * yi
        area = abs(area) / 2
        
        # Validation checks
        side_consistency = abs(top_side - bottom_side) / max(top_side, bottom_side) < 0.2
        height_consistency = abs(left_side - right_side) / max(left_side, right_side) < 0.2
        reasonable_aspect = 0.5 < aspect_ratio < 2.0
        
        return {
            'valid': side_consistency and height_consistency and reasonable_aspect,
            'measurements': {
                'top_side': top_side,
                'bottom_side': bottom_side,
                'left_side': left_side,
                'right_side': right_side,
                'diagonal_1': diagonal_1,
                'diagonal_2': diagonal_2,
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio,
                'area': area
            },
            'consistency': {
                'side_consistency': side_consistency,
                'height_consistency': height_consistency,
                'reasonable_aspect': reasonable_aspect
            }
        }
    
    def analyze_three_pattern_image(self, image_name: str, data: Dict) -> Optional[Dict]:
        """
        Analyze a single image with exactly 3 patterns
        """
        patterns = data.get('patterns', [])
        
        if len(patterns) != 3:
            return None
        
        print(f"\n🔍 Analyzing {image_name} (3 patterns detected)")
        
        # Identify pattern positions
        positions = self.identify_pattern_positions(patterns)
        if not positions:
            print(f"❌ Could not identify pattern positions for {image_name}")
            return None
        
        # Calculate fourth corner
        fourth_corner = self.calculate_fourth_corner(positions)
        
        # Validate geometry
        validation = self.validate_qr_geometry(positions, fourth_corner)
        
        # Print analysis results
        print("📍 Pattern Positions:")
        print(f"   Top-Left: ({positions['top_left']['center']['x']:.0f}, {positions['top_left']['center']['y']:.0f})")
        print(f"   Top-Right: ({positions['top_right']['center']['x']:.0f}, {positions['top_right']['center']['y']:.0f})")
        print(f"   Bottom-Left: ({positions['bottom_left']['center']['x']:.0f}, {positions['bottom_left']['center']['y']:.0f})")
        print(f"🎯 Calculated Fourth Corner: ({fourth_corner[0]:.0f}, {fourth_corner[1]:.0f})")
        
        measurements = validation['measurements']
        print("📏 QR Code Dimensions:")
        print(f"   Width: {measurements['width']:.1f}px")
        print(f"   Height: {measurements['height']:.1f}px") 
        print(f"   Aspect Ratio: {measurements['aspect_ratio']:.3f}")
        print(f"   Area: {measurements['area']:.0f}px²")
        
        print(f"✅ Geometry Valid: {validation['valid']}")
        
        return {
            'image_name': image_name,
            'original_patterns': patterns,
            'identified_positions': positions,
            'fourth_corner': {'x': fourth_corner[0], 'y': fourth_corner[1]},
            'validation': validation,
            'complete_rectangle': {
                'top_left': positions['top_left']['center'],
                'top_right': positions['top_right']['center'],
                'bottom_left': positions['bottom_left']['center'],
                'bottom_right': {'x': fourth_corner[0], 'y': fourth_corner[1]}
            }
        }
    
    def create_visualization(self, analysis: Dict) -> None:
        """
        Create a visualization showing the 3 detected patterns and calculated 4th corner
        """
        image_name = analysis['image_name']
        
        # Load original image
        image_path = self.data_dir / f"{image_name}.png"
        if not image_path.exists():
            for ext in ['.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                alt_path = self.data_dir / f"{image_name}{ext}"
                if alt_path.exists():
                    image_path = alt_path
                    break
        
        if not image_path.exists():
            print(f"❌ Image not found: {image_name}")
            return
            
        image = cv2.imread(str(image_path))
        if image is None:
            return
            
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Create figure with subplots
        _fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Define constants for styling
        bbox_small = {"boxstyle": "round,pad=0.3", "facecolor": 'white', "alpha": 0.9}
        bbox_large = {"boxstyle": "round,pad=0.5", "facecolor": 'lightblue', "alpha": 0.9}
        
        # Left plot: Original with detected patterns
        ax1.imshow(image_rgb)
        ax1.set_title(f"{image_name}\n3 Detected Finder Patterns", fontsize=14, fontweight='bold')
        ax1.axis('off')
        
        # Draw detected patterns
        positions = analysis['identified_positions']
        colors = {'top_left': 'red', 'top_right': 'blue', 'bottom_left': 'green'}
        labels = {'top_left': 'TL', 'top_right': 'TR', 'bottom_left': 'BL'}
        
        for pos_name, pattern in positions.items():
            center = pattern['center']
            size = pattern['size']
            color = colors[pos_name]
            label = labels[pos_name]
            
            # Draw bounding box
            bbox = patches.Rectangle((center['x'] - size//2, center['y'] - size//2), 
                                   size, size, linewidth=3, edgecolor=color, facecolor='none')
            ax1.add_patch(bbox)
            
            # Draw center point
            ax1.plot(center['x'], center['y'], 'o', color=color, markersize=10, 
                    markeredgecolor='white', markeredgewidth=2)
            
            # Add label
            ax1.text(center['x'], center['y'] - size//2 - 15, label, color=color, 
                    fontsize=16, fontweight='bold', ha='center', va='bottom',
                    bbox=bbox_small)
        
        # Right plot: Complete rectangle with calculated 4th corner
        ax2.imshow(image_rgb)
        ax2.set_title(f"{image_name}\nComplete QR Rectangle with Calculated 4th Corner", 
                     fontsize=14, fontweight='bold')
        ax2.axis('off')
        
        # Draw all four corners
        rect = analysis['complete_rectangle']
        fourth_corner = analysis['fourth_corner']
        
        # Draw detected patterns again
        for pos_name, pattern in positions.items():
            center = pattern['center']
            size = pattern['size']
            color = colors[pos_name]
            label = labels[pos_name]
            
            bbox = patches.Rectangle((center['x'] - size//2, center['y'] - size//2), 
                                   size, size, linewidth=3, edgecolor=color, facecolor='none')
            ax2.add_patch(bbox)
            ax2.plot(center['x'], center['y'], 'o', color=color, markersize=10, 
                    markeredgecolor='white', markeredgewidth=2)
            ax2.text(center['x'], center['y'] - size//2 - 15, label, color=color, 
                    fontsize=16, fontweight='bold', ha='center', va='bottom',
                    bbox=bbox_small)
        
        # Draw calculated fourth corner
        avg_size = np.mean([p['size'] for p in positions.values()])
        bbox_br = patches.Rectangle((fourth_corner['x'] - avg_size//2, fourth_corner['y'] - avg_size//2), 
                                  avg_size, avg_size, linewidth=3, edgecolor='orange', 
                                  facecolor='none', linestyle='--')
        ax2.add_patch(bbox_br)
        ax2.plot(fourth_corner['x'], fourth_corner['y'], 's', color='orange', markersize=12, 
                markeredgecolor='white', markeredgewidth=2)
        ax2.text(fourth_corner['x'], fourth_corner['y'] - avg_size//2 - 15, 'BR', color='orange', 
                fontsize=16, fontweight='bold', ha='center', va='bottom',
                bbox=bbox_small)
        
        # Draw complete rectangle outline
        corners = [
            (rect['top_left']['x'], rect['top_left']['y']),
            (rect['top_right']['x'], rect['top_right']['y']),
            (rect['bottom_right']['x'], rect['bottom_right']['y']),
            (rect['bottom_left']['x'], rect['bottom_left']['y']),
            (rect['top_left']['x'], rect['top_left']['y'])  # Close the rectangle
        ]
        
        xs, ys = zip(*corners)
        ax2.plot(xs, ys, color='purple', linewidth=3, alpha=0.8)
        
        # Add measurements text
        measurements = analysis['validation']['measurements']
        info_text = f"""Measurements:
Width: {measurements['width']:.1f}px
Height: {measurements['height']:.1f}px
Aspect Ratio: {measurements['aspect_ratio']:.3f}
Area: {measurements['area']:.0f}px²
Valid: {analysis['validation']['valid']}"""
        
        ax2.text(0.02, 0.98, info_text, transform=ax2.transAxes, fontsize=10,
                verticalalignment='top', bbox=bbox_large, fontfamily='monospace')
        
        plt.tight_layout()
        
        # Save visualization
        output_path = self.output_dir / f"{image_name}_fourth_corner_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Visualization saved: {output_path}")
    
    def analyze_three_pattern_images(self) -> Dict:
        """
        Analyze all images with exactly 3 patterns
        """
        print("🔍 QR Three-Pattern Fourth Corner Calculator")
        print("=" * 60)
        
        # Load all detection results
        all_results = self.load_detection_results()
        
        # Filter for images with exactly 3 patterns
        three_pattern_images = []
        for image_name, data in all_results.items():
            patterns = data.get('patterns', [])
            if len(patterns) == 3:
                three_pattern_images.append((image_name, data))
        
        print(f"📊 Found {len(three_pattern_images)} images with exactly 3 patterns:")
        for image_name, _ in three_pattern_images:
            print(f"   • {image_name}")
        
        if not three_pattern_images:
            print("❌ No images with exactly 3 patterns found!")
            return {}
        
        # Analyze each image
        analysis_results = {}
        
        for image_name, data in three_pattern_images:
            analysis = self.analyze_three_pattern_image(image_name, data)
            if analysis:
                analysis_results[image_name] = analysis
                self.create_visualization(analysis)
        
        # Save analysis results
        results_path = self.output_dir / "three_pattern_analysis_results.json"
        with open(results_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"\n📁 Analysis results saved: {results_path}")
        
        # Create summary
        self.create_summary_report(analysis_results)
        
        return analysis_results
    
    def create_summary_report(self, results: Dict) -> None:
        """
        Create a summary report of all three-pattern analyses
        """
        if not results:
            return
        
        print("\n📊 THREE-PATTERN QR CODE ANALYSIS SUMMARY")
        print("=" * 60)
        
        valid_count = sum(1 for r in results.values() if r['validation']['valid'])
        total_count = len(results)
        
        print(f"Total 3-pattern images analyzed: {total_count}")
        print(f"Valid QR geometries: {valid_count}")
        print(f"Success rate: {valid_count/total_count*100:.1f}%")
        
        # Aggregate statistics
        all_widths = []
        all_heights = []
        all_aspects = []
        all_areas = []
        
        for image_name, analysis in results.items():
            measurements = analysis['validation']['measurements']
            all_widths.append(measurements['width'])
            all_heights.append(measurements['height'])
            all_aspects.append(measurements['aspect_ratio'])
            all_areas.append(measurements['area'])
            
            print(f"\n{image_name}:")
            print(f"  Dimensions: {measurements['width']:.1f} × {measurements['height']:.1f}px")
            print(f"  Aspect Ratio: {measurements['aspect_ratio']:.3f}")
            print(f"  Area: {measurements['area']:.0f}px²")
            print(f"  Valid: {'✅' if analysis['validation']['valid'] else '❌'}")
        
        print("\n📈 AGGREGATE STATISTICS:")
        print(f"Average Width: {np.mean(all_widths):.1f}px")
        print(f"Average Height: {np.mean(all_heights):.1f}px")
        print(f"Average Aspect Ratio: {np.mean(all_aspects):.3f}")
        print(f"Average Area: {np.mean(all_areas):.0f}px²")
        
        print("\n🎯 RECOMMENDATION:")
        if valid_count == total_count:
            print("✅ All 3-pattern QR codes have valid geometry!")
            print("✅ Fourth corner calculation is highly reliable for these images.")
            print("✅ 3-pattern design would work excellently for your application.")
        else:
            print(f"⚠️  {total_count - valid_count} images have geometry issues.")
            print("⚠️  Consider checking pattern detection accuracy.")

def main():
    analyzer = QRThreePatternAnalyzer()
    results = analyzer.analyze_three_pattern_images()
    
    if results:
        print(f"\n🎉 Analysis complete! Check results in: {analyzer.output_dir}")
        print("📁 Generated files:")
        for file_path in sorted(analyzer.output_dir.glob("*.png")):
            print(f"   • {file_path.name}")
        for file_path in sorted(analyzer.output_dir.glob("*.json")):
            print(f"   • {file_path.name}")

if __name__ == "__main__":
    main()
