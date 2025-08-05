#!/usr/bin/env python3
"""
QR Comprehensive Pattern Analyzer
Shows all possible 3-pattern combinations and their scores for better analysis
"""

import cv2
import numpy as np
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Dict, Tuple, Optional
from itertools import combinations

class QRComprehensiveAnalyzer:
    def __init__(self, results_dir="results/enhanced-strict-qr-results", data_dir="data-qr-ratio-finder"):
        self.results_dir = Path(results_dir)
        self.data_dir = Path(data_dir)
        self.output_dir = Path("results/comprehensive-pattern-analysis")
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
        """Identify which pattern is which based on QR code geometry"""
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
        """Calculate the fourth corner using parallelogram rule"""
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
    
    def analyze_combination(self, patterns: List[Dict], combo_index: int) -> Dict:
        """Analyze a single combination of 3 patterns"""
        positions = self.identify_pattern_positions(patterns)
        if not positions:
            return {'valid': False, 'error': 'Could not identify positions'}
        
        fourth_corner = self.calculate_fourth_corner(positions)
        
        # Calculate geometric metrics
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
        
        # Calculate measurements
        top_side = distance(tl, tr)
        bottom_side = distance(bl, br)
        left_side = distance(tl, bl)
        right_side = distance(tr, br)
        
        width = (top_side + bottom_side) / 2
        height = (left_side + right_side) / 2
        aspect_ratio = width / height if height > 0 else 0
        
        # Calculate quality metrics
        side_diff = abs(top_side - bottom_side) / max(top_side, bottom_side) if max(top_side, bottom_side) > 0 else 1
        height_diff = abs(left_side - right_side) / max(left_side, right_side) if max(left_side, right_side) > 0 else 1
        aspect_deviation = abs(aspect_ratio - 1.0)
        
        # Check if fourth corner is reasonable (within image bounds and positive)
        reasonable_corner = br[0] > 0 and br[1] > 0 and br[0] < 2000 and br[1] < 2000
        
        # Calculate overall score
        side_score = max(0, 1.0 - side_diff)
        height_score = max(0, 1.0 - height_diff)
        aspect_score = max(0, 1.0 - aspect_deviation)
        corner_score = 1.0 if reasonable_corner else 0.0
        pattern_scores = [p.get('total_score', 0) for p in patterns]
        avg_pattern_score = np.mean(pattern_scores)
        
        total_score = (side_score * 0.2 + height_score * 0.2 + aspect_score * 0.2 + 
                      corner_score * 0.2 + avg_pattern_score * 0.2)
        
        return {
            'valid': True,
            'combo_index': combo_index,
            'patterns': patterns,
            'positions': positions,
            'fourth_corner': fourth_corner,
            'measurements': {
                'top_side': top_side,
                'bottom_side': bottom_side,
                'left_side': left_side,
                'right_side': right_side,
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio
            },
            'quality_metrics': {
                'side_consistency': 1.0 - side_diff,
                'height_consistency': 1.0 - height_diff,
                'aspect_deviation': aspect_deviation,
                'reasonable_corner': reasonable_corner
            },
            'scores': {
                'side_score': side_score,
                'height_score': height_score,
                'aspect_score': aspect_score,
                'corner_score': corner_score,
                'pattern_score': avg_pattern_score,
                'total_score': total_score
            },
            'pattern_scores': pattern_scores
        }
    
    def analyze_all_combinations(self, image_name: str, patterns: List[Dict]) -> Dict:
        """Analyze all possible 3-pattern combinations for an image"""
        if len(patterns) < 3:
            return {'error': f'Only {len(patterns)} patterns detected, need at least 3'}
        
        print(f"\n🔍 Analyzing {image_name} - {len(patterns)} patterns detected")
        
        # Get all combinations of 3 patterns
        all_combos = list(combinations(patterns, 3))
        combo_results = []
        
        print(f"📊 Evaluating {len(all_combos)} possible 3-pattern combinations...")
        
        for i, combo in enumerate(all_combos):
            result = self.analyze_combination(list(combo), i)
            if result['valid']:
                combo_results.append(result)
        
        if not combo_results:
            return {'error': 'No valid combinations found'}
        
        # Sort by total score
        combo_results.sort(key=lambda x: x['scores']['total_score'], reverse=True)
        
        # Print summary of all combinations
        print("\n📈 COMBINATION ANALYSIS SUMMARY:")
        print("=" * 60)
        print(f"{'#':<3} {'Score':<6} {'Aspect':<7} {'4th Corner':<15} {'Valid Corner':<12}")
        print("-" * 60)
        
        for i, result in enumerate(combo_results[:10]):  # Show top 10
            score = result['scores']['total_score']
            aspect = result['measurements']['aspect_ratio']
            corner = result['fourth_corner']
            valid_corner = result['quality_metrics']['reasonable_corner']
            
            print(f"{i+1:<3} {score:<6.3f} {aspect:<7.3f} "
                  f"({corner[0]:>4.0f},{corner[1]:>4.0f})   {'✅' if valid_corner else '❌'}")
        
        return {
            'image_name': image_name,
            'original_patterns': patterns,
            'total_combinations': len(all_combos),
            'valid_combinations': len(combo_results),
            'combinations': combo_results,
            'best_combination': combo_results[0]
        }
    
    def create_comprehensive_visualization(self, analysis: Dict) -> None:
        """Create visualization showing top combinations"""
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
        
        # Show top 4 combinations
        top_combos = analysis['combinations'][:4]
        
        _fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()
        
        bbox_small = {"boxstyle": "round,pad=0.3", "facecolor": 'white', "alpha": 0.9}
        
        for idx, combo in enumerate(top_combos):
            ax = axes[idx]
            ax.imshow(image_rgb)
            
            score = combo['scores']['total_score']
            corner = combo['fourth_corner']
            reasonable = combo['quality_metrics']['reasonable_corner']
            
            title = f"Combo #{idx+1} (Score: {score:.3f})\n4th Corner: ({corner[0]:.0f}, {corner[1]:.0f}) {'✅' if reasonable else '❌'}"
            ax.set_title(title, fontsize=11, fontweight='bold')
            ax.axis('off')
            
            # Draw selected patterns
            positions = combo['positions']
            colors = {'top_left': 'red', 'top_right': 'blue', 'bottom_left': 'green'}
            labels = {'top_left': 'TL', 'top_right': 'TR', 'bottom_left': 'BL'}
            
            for pos_name, pattern in positions.items():
                center = pattern['center']
                size = pattern['size']
                color = colors[pos_name]
                label = labels[pos_name]
                
                bbox = patches.Rectangle((center['x'] - size//2, center['y'] - size//2), 
                                       size, size, linewidth=2, edgecolor=color, facecolor='none')
                ax.add_patch(bbox)
                ax.plot(center['x'], center['y'], 'o', color=color, markersize=8, 
                       markeredgecolor='white', markeredgewidth=1)
                ax.text(center['x'], center['y'] - size//2 - 10, label, color=color, 
                       fontsize=10, fontweight='bold', ha='center', va='bottom',
                       bbox=bbox_small)
            
            # Draw calculated fourth corner
            avg_size = np.mean([p['size'] for p in positions.values()])
            if reasonable:
                bbox_br = patches.Rectangle((corner[0] - avg_size//2, corner[1] - avg_size//2), 
                                          avg_size, avg_size, linewidth=2, edgecolor='orange', 
                                          facecolor='none', linestyle='--')
                ax.add_patch(bbox_br)
                ax.plot(corner[0], corner[1], 's', color='orange', markersize=8, 
                       markeredgecolor='white', markeredgewidth=1)
                ax.text(corner[0], corner[1] - avg_size//2 - 10, 'BR', color='orange', 
                       fontsize=10, fontweight='bold', ha='center', va='bottom',
                       bbox=bbox_small)
                
                # Draw rectangle outline
                corners = [
                    (positions['top_left']['center']['x'], positions['top_left']['center']['y']),
                    (positions['top_right']['center']['x'], positions['top_right']['center']['y']),
                    (corner[0], corner[1]),
                    (positions['bottom_left']['center']['x'], positions['bottom_left']['center']['y']),
                    (positions['top_left']['center']['x'], positions['top_left']['center']['y'])
                ]
                xs, ys = zip(*corners)
                ax.plot(xs, ys, color='purple', linewidth=2, alpha=0.7)
        
        plt.suptitle(f"{image_name} - Top 4 Pattern Combinations", fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Save visualization
        output_path = self.output_dir / f"{image_name}_comprehensive_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Comprehensive visualization saved: {output_path}")
    
    def analyze_target_images(self, target_images: List[str]) -> Dict:
        """Analyze specific target images"""
        print("🔍 QR Comprehensive Pattern Analyzer")
        print("=" * 50)
        
        # Load all detection results
        all_results = self.load_detection_results()
        
        analysis_results = {}
        
        for img_name in target_images:
            if img_name in all_results:
                patterns = all_results[img_name].get('patterns', [])
                if len(patterns) >= 3:
                    analysis = self.analyze_all_combinations(img_name, patterns)
                    if 'error' not in analysis:
                        analysis_results[img_name] = analysis
                        self.create_comprehensive_visualization(analysis)
                        
                        # Print best result summary
                        best = analysis['best_combination']
                        print(f"\n🎯 BEST COMBINATION for {img_name}:")
                        print(f"   Score: {best['scores']['total_score']:.3f}")
                        print(f"   Fourth Corner: ({best['fourth_corner'][0]:.0f}, {best['fourth_corner'][1]:.0f})")
                        print(f"   Aspect Ratio: {best['measurements']['aspect_ratio']:.3f}")
                        print(f"   Reasonable Corner: {'✅' if best['quality_metrics']['reasonable_corner'] else '❌'}")
                    else:
                        print(f"❌ {img_name}: {analysis['error']}")
                else:
                    print(f"⚠️  {img_name} has only {len(patterns)} patterns (need ≥3)")
            else:
                print(f"❌ {img_name} not found in results")
        
        # Save comprehensive results
        results_path = self.output_dir / "comprehensive_analysis_results.json"
        with open(results_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"\n📁 Analysis results saved: {results_path}")
        
        return analysis_results

def main():
    analyzer = QRComprehensiveAnalyzer()
    
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
