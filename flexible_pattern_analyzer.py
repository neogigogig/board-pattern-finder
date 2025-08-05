#!/usr/bin/env python3
"""
QR Flexible Pattern Analyzer
Analyzes QR codes with 3-4 patterns and allows selection of best 3 for fourth corner calculation
"""

import cv2
import numpy as np
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Dict, Tuple, Optional

class QRFlexiblePatternAnalyzer:
    def __init__(self, results_dir="results/enhanced-strict-qr-results", data_dir="data-qr-ratio-finder"):
        self.results_dir = Path(results_dir)
        self.data_dir = Path(data_dir)
        self.output_dir = Path("results/flexible-three-pattern-analysis")
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
    
    def get_pattern_combinations(self, patterns: List[Dict]) -> List[List[Dict]]:
        """
        Get all possible combinations of 3 patterns from the detected patterns
        """
        from itertools import combinations
        
        if len(patterns) < 3:
            return []
        elif len(patterns) == 3:
            return [patterns]
        else:
            # Return all combinations of 3 patterns
            return [list(combo) for combo in combinations(patterns, 3)]
    
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
    
    def score_pattern_combination(self, patterns: List[Dict], fourth_corner: Tuple[float, float]) -> float:
        """
        Score a combination of 3 patterns based on QR geometry quality
        """
        positions = self.identify_pattern_positions(patterns)
        if not positions:
            return 0.0
        
        tl = positions['top_left']['center']
        bl = positions['bottom_left']['center']
        tr = positions['top_right']['center']
        br = fourth_corner
        
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
        
        # Calculate metrics
        top_side = distance(tl, tr)
        bottom_side = distance(bl, br)
        left_side = distance(tl, bl)
        right_side = distance(tr, br)
        
        # Scoring factors
        scores = []
        
        # 1. Side consistency (parallel sides should be similar length)
        if max(top_side, bottom_side) > 0:
            side_consistency = 1.0 - abs(top_side - bottom_side) / max(top_side, bottom_side)
            scores.append(side_consistency * 0.25)
        
        if max(left_side, right_side) > 0:
            height_consistency = 1.0 - abs(left_side - right_side) / max(left_side, right_side)
            scores.append(height_consistency * 0.25)
        
        # 2. Aspect ratio (should be close to 1.0 for QR codes)
        width = (top_side + bottom_side) / 2
        height = (left_side + right_side) / 2
        if height > 0:
            aspect_ratio = width / height
            aspect_score = 1.0 - abs(aspect_ratio - 1.0)
            aspect_score = max(0, aspect_score)
            scores.append(aspect_score * 0.25)
        
        # 3. Pattern score sum (higher total pattern scores are better)
        total_pattern_score = sum(p.get('total_score', 0) for p in patterns)
        normalized_pattern_score = min(1.0, total_pattern_score / 3.0)  # Normalize assuming max 1.0 per pattern
        scores.append(normalized_pattern_score * 0.25)
        
        return sum(scores)
    
    def find_best_three_patterns(self, patterns: List[Dict]) -> Tuple[List[Dict], float, Tuple[float, float]]:
        """
        Find the best combination of 3 patterns from all detected patterns
        """
        combinations = self.get_pattern_combinations(patterns)
        
        best_combination = None
        best_score = -1
        best_fourth_corner = None
        
        for combo in combinations:
            positions = self.identify_pattern_positions(combo)
            if positions:
                fourth_corner = self.calculate_fourth_corner(positions)
                score = self.score_pattern_combination(combo, fourth_corner)
                
                if score > best_score:
                    best_score = score
                    best_combination = combo
                    best_fourth_corner = fourth_corner
        
        return best_combination, best_score, best_fourth_corner
    
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
        side_consistency = abs(top_side - bottom_side) / max(top_side, bottom_side) < 0.3 if max(top_side, bottom_side) > 0 else False
        height_consistency = abs(left_side - right_side) / max(left_side, right_side) < 0.3 if max(left_side, right_side) > 0 else False
        reasonable_aspect = 0.5 < aspect_ratio < 2.0
        
        return {
            'valid': side_consistency and height_consistency and reasonable_aspect,
            'measurements': {
                'top_side': top_side,
                'bottom_side': bottom_side,
                'left_side': left_side,
                'right_side': right_side,
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
    
    def analyze_image(self, image_name: str, data: Dict) -> Optional[Dict]:
        """
        Analyze a single image and find the best 3-pattern combination
        """
        patterns = data.get('patterns', [])
        
        if len(patterns) < 3:
            return None
        
        print(f"\n🔍 Analyzing {image_name} ({len(patterns)} patterns detected)")
        
        # Find best combination of 3 patterns
        best_patterns, best_score, fourth_corner = self.find_best_three_patterns(patterns)
        
        if not best_patterns:
            print(f"❌ Could not find valid 3-pattern combination for {image_name}")
            return None
        
        # Identify positions
        positions = self.identify_pattern_positions(best_patterns)
        
        # Validate geometry
        validation = self.validate_qr_geometry(positions, fourth_corner)
        
        # Print analysis results
        print(f"🎯 Best 3-Pattern Combination (Score: {best_score:.3f})")
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
        
        if len(patterns) > 3:
            excluded_patterns = [p for p in patterns if p not in best_patterns]
            print(f"📝 Excluded {len(excluded_patterns)} pattern(s) from analysis")
        
        return {
            'image_name': image_name,
            'original_patterns': patterns,
            'selected_patterns': best_patterns,
            'selection_score': best_score,
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
        Create a visualization showing all patterns, selected 3, and calculated 4th corner
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
        
        # Create figure with three subplots
        _fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(24, 8))
        
        # Define styling
        bbox_small = {"boxstyle": "round,pad=0.3", "facecolor": 'white', "alpha": 0.9}
        bbox_large = {"boxstyle": "round,pad=0.5", "facecolor": 'lightblue', "alpha": 0.9}
        
        # Plot 1: All detected patterns
        ax1.imshow(image_rgb)
        ax1.set_title(f"{image_name}\nAll {len(analysis['original_patterns'])} Detected Patterns", 
                     fontsize=12, fontweight='bold')
        ax1.axis('off')
        
        # Draw all patterns in gray
        for i, pattern in enumerate(analysis['original_patterns']):
            center = pattern['center']
            size = pattern['size']
            
            bbox = patches.Rectangle((center['x'] - size//2, center['y'] - size//2), 
                                   size, size, linewidth=2, edgecolor='gray', facecolor='none')
            ax1.add_patch(bbox)
            ax1.plot(center['x'], center['y'], 'o', color='gray', markersize=8)
            ax1.text(center['x'], center['y'] - size//2 - 10, str(i+1), color='gray', 
                    fontsize=12, fontweight='bold', ha='center', va='bottom')
        
        # Plot 2: Selected 3 patterns
        ax2.imshow(image_rgb)
        ax2.set_title(f"{image_name}\nSelected Best 3 Patterns (Score: {analysis['selection_score']:.3f})", 
                     fontsize=12, fontweight='bold')
        ax2.axis('off')
        
        positions = analysis['identified_positions']
        colors = {'top_left': 'red', 'top_right': 'blue', 'bottom_left': 'green'}
        labels = {'top_left': 'TL', 'top_right': 'TR', 'bottom_left': 'BL'}
        
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
        
        # Plot 3: Complete rectangle with calculated 4th corner
        ax3.imshow(image_rgb)
        ax3.set_title(f"{image_name}\nComplete QR Rectangle with 4th Corner", 
                     fontsize=12, fontweight='bold')
        ax3.axis('off')
        
        fourth_corner = analysis['fourth_corner']
        
        # Draw selected patterns again
        for pos_name, pattern in positions.items():
            center = pattern['center']
            size = pattern['size']
            color = colors[pos_name]
            label = labels[pos_name]
            
            bbox = patches.Rectangle((center['x'] - size//2, center['y'] - size//2), 
                                   size, size, linewidth=3, edgecolor=color, facecolor='none')
            ax3.add_patch(bbox)
            ax3.plot(center['x'], center['y'], 'o', color=color, markersize=10, 
                    markeredgecolor='white', markeredgewidth=2)
            ax3.text(center['x'], center['y'] - size//2 - 15, label, color=color, 
                    fontsize=16, fontweight='bold', ha='center', va='bottom',
                    bbox=bbox_small)
        
        # Draw calculated fourth corner
        avg_size = np.mean([p['size'] for p in positions.values()])
        bbox_br = patches.Rectangle((fourth_corner['x'] - avg_size//2, fourth_corner['y'] - avg_size//2), 
                                  avg_size, avg_size, linewidth=3, edgecolor='orange', 
                                  facecolor='none', linestyle='--')
        ax3.add_patch(bbox_br)
        ax3.plot(fourth_corner['x'], fourth_corner['y'], 's', color='orange', markersize=12, 
                markeredgecolor='white', markeredgewidth=2)
        ax3.text(fourth_corner['x'], fourth_corner['y'] - avg_size//2 - 15, 'BR', color='orange', 
                fontsize=16, fontweight='bold', ha='center', va='bottom',
                bbox=bbox_small)
        
        # Draw complete rectangle outline
        rect = analysis['complete_rectangle']
        corners = [
            (rect['top_left']['x'], rect['top_left']['y']),
            (rect['top_right']['x'], rect['top_right']['y']),
            (rect['bottom_right']['x'], rect['bottom_right']['y']),
            (rect['bottom_left']['x'], rect['bottom_left']['y']),
            (rect['top_left']['x'], rect['top_left']['y'])  # Close the rectangle
        ]
        
        xs, ys = zip(*corners)
        ax3.plot(xs, ys, color='purple', linewidth=3, alpha=0.8)
        
        # Add measurements text
        measurements = analysis['validation']['measurements']
        info_text = f"""Measurements:
Width: {measurements['width']:.1f}px
Height: {measurements['height']:.1f}px
Aspect: {measurements['aspect_ratio']:.3f}
Area: {measurements['area']:.0f}px²
Valid: {analysis['validation']['valid']}
Score: {analysis['selection_score']:.3f}"""
        
        ax3.text(0.02, 0.98, info_text, transform=ax3.transAxes, fontsize=9,
                verticalalignment='top', bbox=bbox_large, fontfamily='monospace')
        
        plt.tight_layout()
        
        # Save visualization
        output_path = self.output_dir / f"{image_name}_flexible_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Visualization saved: {output_path}")
    
    def analyze_target_images(self, target_images: List[str] = None) -> Dict:
        """
        Analyze specific target images or all images with 3+ patterns
        """
        print("🔍 QR Flexible Pattern Analyzer - Fourth Corner Calculator")
        print("=" * 70)
        
        # Load all detection results
        all_results = self.load_detection_results()
        
        # Filter for target images or images with 3+ patterns
        if target_images:
            target_images_data = []
            for img_name in target_images:
                if img_name in all_results:
                    patterns = all_results[img_name].get('patterns', [])
                    if len(patterns) >= 3:
                        target_images_data.append((img_name, all_results[img_name]))
                    else:
                        print(f"⚠️  {img_name} has only {len(patterns)} patterns (need ≥3)")
                else:
                    print(f"❌ {img_name} not found in results")
        else:
            target_images_data = []
            for image_name, data in all_results.items():
                patterns = data.get('patterns', [])
                if len(patterns) >= 3:
                    target_images_data.append((image_name, data))
        
        print(f"📊 Found {len(target_images_data)} images with ≥3 patterns:")
        for image_name, data in target_images_data:
            pattern_count = len(data.get('patterns', []))
            print(f"   • {image_name}: {pattern_count} patterns")
        
        if not target_images_data:
            print("❌ No suitable images found!")
            return {}
        
        # Analyze each image
        analysis_results = {}
        
        for image_name, data in target_images_data:
            analysis = self.analyze_image(image_name, data)
            if analysis:
                analysis_results[image_name] = analysis
                self.create_visualization(analysis)
        
        # Save analysis results
        results_path = self.output_dir / "flexible_analysis_results.json"
        with open(results_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"\n📁 Analysis results saved: {results_path}")
        
        # Create summary
        self.create_summary_report(analysis_results)
        
        return analysis_results
    
    def create_summary_report(self, results: Dict) -> None:
        """
        Create a summary report of all analyses
        """
        if not results:
            return
        
        print("\n📊 FLEXIBLE PATTERN ANALYSIS SUMMARY")
        print("=" * 70)
        
        valid_count = sum(1 for r in results.values() if r['validation']['valid'])
        total_count = len(results)
        
        print(f"Total images analyzed: {total_count}")
        print(f"Valid QR geometries: {valid_count}")
        print(f"Success rate: {valid_count/total_count*100:.1f}%")
        
        for image_name, analysis in results.items():
            measurements = analysis['validation']['measurements']
            original_count = len(analysis['original_patterns'])
            
            print(f"\n{image_name}:")
            print(f"  Original patterns: {original_count} → Selected: 3")
            print(f"  Selection score: {analysis['selection_score']:.3f}")
            print(f"  Dimensions: {measurements['width']:.1f} × {measurements['height']:.1f}px")
            print(f"  Aspect Ratio: {measurements['aspect_ratio']:.3f}")
            print(f"  Valid: {'✅' if analysis['validation']['valid'] else '❌'}")
        
        print("\n🎯 RECOMMENDATION:")
        if valid_count == total_count:
            print("✅ All analyzed images have valid 3-pattern geometry!")
            print("✅ Fourth corner calculation is reliable for these images.")
            print("✅ 3-pattern QR design would work excellently.")
        else:
            print(f"⚠️  {total_count - valid_count} images need attention.")
            print("💡 Consider adjusting pattern detection or selection criteria.")

def main():
    analyzer = QRFlexiblePatternAnalyzer()
    
    # Analyze specific target images (copy 7, 8, 9)
    target_images = ["image copy 7", "image copy 8", "image copy 9"]
    results = analyzer.analyze_target_images(target_images)
    
    if results:
        print(f"\n🎉 Analysis complete! Check results in: {analyzer.output_dir}")
        print("📁 Generated files:")
        for file_path in sorted(analyzer.output_dir.glob("*.png")):
            print(f"   • {file_path.name}")
        for file_path in sorted(analyzer.output_dir.glob("*.json")):
            print(f"   • {file_path.name}")

if __name__ == "__main__":
    main()
