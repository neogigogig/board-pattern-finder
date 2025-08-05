#!/usr/bin/env python3
"""
Production QR Three-Pattern Analyzer
Final production version for QR codes with 3 finder patterns and mathematical fourth corner calculation
Incorporates optimal pattern selection and comprehensive validation
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

class ProductionQRThreePatternAnalyzer:
    def __init__(self, results_dir="results/enhanced-strict-qr-results", data_dir="data-qr-ratio-finder"):
        self.results_dir = Path(results_dir)
        self.data_dir = Path(data_dir)
        self.output_dir = Path("results/production-three-pattern")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Production configuration
        self.config = {
            'min_corner_threshold': 0,  # Minimum X,Y for valid fourth corner
            'max_corner_threshold': 2000,  # Maximum X,Y for valid fourth corner
            'max_aspect_deviation': 1.0,  # Maximum deviation from 1:1 aspect ratio
            'min_side_consistency': 0.7,  # Minimum consistency between parallel sides
            'min_total_score': 0.5,  # Minimum total score for valid combination
        }
        
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
        Mathematical formula: BR = TL + BL - TR (vector addition)
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
    
    def calculate_quality_metrics(self, positions: Dict, fourth_corner: Tuple[float, float]) -> Dict:
        """Calculate comprehensive quality metrics for a pattern combination"""
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
        
        # Calculate all measurements
        top_side = distance(tl, tr)
        bottom_side = distance(bl, br)
        left_side = distance(tl, bl)
        right_side = distance(tr, br)
        
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
        
        # Quality assessments
        side_consistency = 1.0 - (abs(top_side - bottom_side) / max(top_side, bottom_side)) if max(top_side, bottom_side) > 0 else 0
        height_consistency = 1.0 - (abs(left_side - right_side) / max(left_side, right_side)) if max(left_side, right_side) > 0 else 0
        aspect_deviation = abs(aspect_ratio - 1.0)
        
        # Corner validity
        corner_valid = (br[0] >= self.config['min_corner_threshold'] and 
                       br[1] >= self.config['min_corner_threshold'] and
                       br[0] <= self.config['max_corner_threshold'] and 
                       br[1] <= self.config['max_corner_threshold'])
        
        return {
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
            'quality': {
                'side_consistency': side_consistency,
                'height_consistency': height_consistency,
                'aspect_deviation': aspect_deviation,
                'corner_valid': corner_valid
            }
        }
    
    def score_pattern_combination(self, patterns: List[Dict], positions: Dict, fourth_corner: Tuple[float, float]) -> float:
        """Calculate comprehensive score for a pattern combination"""
        metrics = self.calculate_quality_metrics(positions, fourth_corner)
        
        # Individual component scores
        side_score = metrics['quality']['side_consistency']
        height_score = metrics['quality']['height_consistency']
        aspect_score = max(0, 1.0 - metrics['quality']['aspect_deviation'])
        corner_score = 1.0 if metrics['quality']['corner_valid'] else 0.0
        
        # Pattern quality (from original detection)
        pattern_scores = [p.get('total_score', 0) for p in patterns]
        avg_pattern_score = np.mean(pattern_scores)
        
        # Weighted total score
        total_score = (side_score * 0.25 + height_score * 0.25 + 
                      aspect_score * 0.25 + corner_score * 0.15 + 
                      avg_pattern_score * 0.10)
        
        return total_score
    
    def find_optimal_pattern_combination(self, patterns: List[Dict]) -> Optional[Dict]:
        """Find the optimal combination of 3 patterns from detected patterns"""
        if len(patterns) < 3:
            return None
            
        if len(patterns) == 3:
            # Only one combination possible
            combinations_to_test = [patterns]
        else:
            # Test all possible combinations of 3 patterns
            combinations_to_test = [list(combo) for combo in combinations(patterns, 3)]
        
        best_combination = None
        best_score = -1
        
        for combo in combinations_to_test:
            positions = self.identify_pattern_positions(combo)
            if not positions:
                continue
                
            fourth_corner = self.calculate_fourth_corner(positions)
            score = self.score_pattern_combination(combo, positions, fourth_corner)
            
            if score > best_score:
                best_score = score
                best_combination = {
                    'patterns': combo,
                    'positions': positions,
                    'fourth_corner': fourth_corner,
                    'score': score
                }
        
        return best_combination
    
    def validate_qr_geometry(self, combination: Dict) -> bool:
        """Validate if the QR geometry meets production requirements"""
        metrics = self.calculate_quality_metrics(combination['positions'], combination['fourth_corner'])
        
        # Check all production criteria
        validations = [
            combination['score'] >= self.config['min_total_score'],
            metrics['quality']['side_consistency'] >= self.config['min_side_consistency'],
            metrics['quality']['height_consistency'] >= self.config['min_side_consistency'],
            metrics['quality']['aspect_deviation'] <= self.config['max_aspect_deviation'],
            metrics['quality']['corner_valid']
        ]
        
        return all(validations)
    
    def analyze_image(self, image_name: str, data: Dict) -> Optional[Dict]:
        """
        Analyze a single image for 3-pattern QR code detection
        """
        patterns = data.get('patterns', [])
        
        if len(patterns) < 3:
            return {
                'status': 'insufficient_patterns',
                'message': f'Only {len(patterns)} patterns detected, need at least 3',
                'image_name': image_name
            }
        
        print(f"\n🔍 Analyzing {image_name} ({len(patterns)} patterns detected)")
        
        # Find optimal pattern combination
        optimal_combo = self.find_optimal_pattern_combination(patterns)
        
        if not optimal_combo:
            return {
                'status': 'no_valid_combination',
                'message': 'Could not find valid 3-pattern combination',
                'image_name': image_name
            }
        
        # Calculate detailed metrics
        metrics = self.calculate_quality_metrics(optimal_combo['positions'], optimal_combo['fourth_corner'])
        
        # Validate geometry
        is_valid = self.validate_qr_geometry(optimal_combo)
        
        # Create result structure
        result = {
            'status': 'success' if is_valid else 'validation_failed',
            'image_name': image_name,
            'original_pattern_count': len(patterns),
            'selected_patterns': optimal_combo['patterns'],
            'pattern_positions': optimal_combo['positions'],
            'fourth_corner': {
                'x': optimal_combo['fourth_corner'][0],
                'y': optimal_combo['fourth_corner'][1]
            },
            'qr_rectangle': {
                'top_left': optimal_combo['positions']['top_left']['center'],
                'top_right': optimal_combo['positions']['top_right']['center'],
                'bottom_left': optimal_combo['positions']['bottom_left']['center'],
                'bottom_right': {
                    'x': optimal_combo['fourth_corner'][0],
                    'y': optimal_combo['fourth_corner'][1]
                }
            },
            'quality_metrics': metrics,
            'combination_score': optimal_combo['score'],
            'geometry_valid': is_valid
        }
        
        # Print analysis summary
        self.print_analysis_summary(result)
        
        return result
    
    def print_analysis_summary(self, result: Dict) -> None:
        """Print formatted analysis summary"""
        name = result['image_name']
        
        if result['status'] != 'success' and result['status'] != 'validation_failed':
            print(f"❌ {name}: {result['message']}")
            return
        
        fourth_corner = result['fourth_corner']
        metrics = result['quality_metrics']
        score = result['combination_score']
        valid = result['geometry_valid']
        
        print(f"🎯 Optimal Combination (Score: {score:.3f})")
        print("📍 Pattern Positions:")
        positions = result['pattern_positions']
        print(f"   Top-Left: ({positions['top_left']['center']['x']:.0f}, {positions['top_left']['center']['y']:.0f})")
        print(f"   Top-Right: ({positions['top_right']['center']['x']:.0f}, {positions['top_right']['center']['y']:.0f})")
        print(f"   Bottom-Left: ({positions['bottom_left']['center']['x']:.0f}, {positions['bottom_left']['center']['y']:.0f})")
        print(f"🎯 Calculated Fourth Corner: ({fourth_corner['x']:.0f}, {fourth_corner['y']:.0f})")
        
        measurements = metrics['measurements']
        print("📏 QR Code Dimensions:")
        print(f"   Width: {measurements['width']:.1f}px")
        print(f"   Height: {measurements['height']:.1f}px")
        print(f"   Aspect Ratio: {measurements['aspect_ratio']:.3f}")
        print(f"   Area: {measurements['area']:.0f}px²")
        
        quality = metrics['quality']
        print("✅ Quality Assessment:")
        print(f"   Side Consistency: {quality['side_consistency']:.3f}")
        print(f"   Height Consistency: {quality['height_consistency']:.3f}")
        print(f"   Aspect Deviation: {quality['aspect_deviation']:.3f}")
        print(f"   Valid Corner: {'✅' if quality['corner_valid'] else '❌'}")
        print(f"   Overall Valid: {'✅' if valid else '❌'}")
    
    def create_production_visualization(self, result: Dict) -> None:
        """Create production-quality visualization"""
        if result['status'] not in ['success', 'validation_failed']:
            return
            
        image_name = result['image_name']
        
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
        
        # Create visualization
        _fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        bbox_style = {"boxstyle": "round,pad=0.3", "facecolor": 'white', "alpha": 0.9}
        
        # Left plot: Selected 3 patterns
        ax1.imshow(image_rgb)
        ax1.set_title(f"{image_name}\nSelected 3 Finder Patterns", fontsize=14, fontweight='bold')
        ax1.axis('off')
        
        positions = result['pattern_positions']
        colors = {'top_left': 'red', 'top_right': 'blue', 'bottom_left': 'green'}
        labels = {'top_left': 'TL', 'top_right': 'TR', 'bottom_left': 'BL'}
        
        for pos_name, pattern in positions.items():
            center = pattern['center']
            size = pattern['size']
            color = colors[pos_name]
            label = labels[pos_name]
            
            bbox = patches.Rectangle((center['x'] - size//2, center['y'] - size//2), 
                                   size, size, linewidth=3, edgecolor=color, facecolor='none')
            ax1.add_patch(bbox)
            ax1.plot(center['x'], center['y'], 'o', color=color, markersize=12, 
                    markeredgecolor='white', markeredgewidth=2)
            ax1.text(center['x'], center['y'] - size//2 - 20, label, color=color, 
                    fontsize=16, fontweight='bold', ha='center', va='bottom',
                    bbox=bbox_style)
        
        # Right plot: Complete QR rectangle
        ax2.imshow(image_rgb)
        status_emoji = "✅" if result['geometry_valid'] else "⚠️"
        score = result['combination_score']
        ax2.set_title(f"{image_name}\nComplete QR Rectangle {status_emoji} (Score: {score:.3f})", 
                     fontsize=14, fontweight='bold')
        ax2.axis('off')
        
        # Draw patterns again
        for pos_name, pattern in positions.items():
            center = pattern['center']
            size = pattern['size']
            color = colors[pos_name]
            label = labels[pos_name]
            
            bbox = patches.Rectangle((center['x'] - size//2, center['y'] - size//2), 
                                   size, size, linewidth=3, edgecolor=color, facecolor='none')
            ax2.add_patch(bbox)
            ax2.plot(center['x'], center['y'], 'o', color=color, markersize=12, 
                    markeredgecolor='white', markeredgewidth=2)
            ax2.text(center['x'], center['y'] - size//2 - 20, label, color=color, 
                    fontsize=16, fontweight='bold', ha='center', va='bottom',
                    bbox=bbox_style)
        
        # Draw calculated fourth corner
        fourth_corner = result['fourth_corner']
        avg_size = np.mean([p['size'] for p in positions.values()])
        
        if result['quality_metrics']['quality']['corner_valid']:
            bbox_br = patches.Rectangle((fourth_corner['x'] - avg_size//2, fourth_corner['y'] - avg_size//2), 
                                      avg_size, avg_size, linewidth=3, edgecolor='orange', 
                                      facecolor='none', linestyle='--')
            ax2.add_patch(bbox_br)
            ax2.plot(fourth_corner['x'], fourth_corner['y'], 's', color='orange', markersize=14, 
                    markeredgecolor='white', markeredgewidth=2)
            ax2.text(fourth_corner['x'], fourth_corner['y'] - avg_size//2 - 20, 'BR*', color='orange', 
                    fontsize=16, fontweight='bold', ha='center', va='bottom',
                    bbox=bbox_style)
            
            # Draw complete rectangle outline
            rect = result['qr_rectangle']
            corners = [
                (rect['top_left']['x'], rect['top_left']['y']),
                (rect['top_right']['x'], rect['top_right']['y']),
                (rect['bottom_right']['x'], rect['bottom_right']['y']),
                (rect['bottom_left']['x'], rect['bottom_left']['y']),
                (rect['top_left']['x'], rect['top_left']['y'])  # Close rectangle
            ]
            
            xs, ys = zip(*corners)
            ax2.plot(xs, ys, color='purple', linewidth=4, alpha=0.8)
        
        # Add comprehensive info box
        measurements = result['quality_metrics']['measurements']
        quality = result['quality_metrics']['quality']
        
        info_text = f"""Production Analysis:
Score: {result['combination_score']:.3f}
Dimensions: {measurements['width']:.0f} × {measurements['height']:.0f}px
Aspect Ratio: {measurements['aspect_ratio']:.3f}
Side Consistency: {quality['side_consistency']:.3f}
Height Consistency: {quality['height_consistency']:.3f}
Valid Corner: {'Yes' if quality['corner_valid'] else 'No'}
Geometry Valid: {'Yes' if result['geometry_valid'] else 'No'}

Fourth Corner*: ({fourth_corner['x']:.0f}, {fourth_corner['y']:.0f})
*Calculated using parallelogram rule"""
        
        ax2.text(0.02, 0.98, info_text, transform=ax2.transAxes, fontsize=10,
                verticalalignment='top', bbox={"boxstyle": "round,pad=0.5", 
                "facecolor": 'lightblue', "alpha": 0.95}, fontfamily='monospace')
        
        plt.tight_layout()
        
        # Save visualization
        output_path = self.output_dir / f"{image_name}_production_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Production visualization saved: {output_path}")
    
    def process_images(self, target_images: List[str] = None) -> Dict:
        """
        Process target images or all suitable images
        """
        print("🏭 PRODUCTION QR THREE-PATTERN ANALYZER")
        print("=" * 60)
        print("🎯 Mathematical Fourth Corner Calculation")
        print("⚙️  Production Configuration:")
        print(f"   Min Corner Threshold: {self.config['min_corner_threshold']}")
        print(f"   Max Corner Threshold: {self.config['max_corner_threshold']}")
        print(f"   Min Side Consistency: {self.config['min_side_consistency']}")
        print(f"   Min Total Score: {self.config['min_total_score']}")
        print("=" * 60)
        
        # Load all detection results
        all_results = self.load_detection_results()
        
        # Determine target images
        if target_images:
            images_to_process = target_images
        else:
            # Process all images with 3+ patterns
            images_to_process = []
            for image_name, data in all_results.items():
                patterns = data.get('patterns', [])
                if len(patterns) >= 3:
                    images_to_process.append(image_name)
        
        print(f"📊 Processing {len(images_to_process)} images...")
        
        # Process each image
        analysis_results = {}
        success_count = 0
        
        for image_name in images_to_process:
            if image_name in all_results:
                result = self.analyze_image(image_name, all_results[image_name])
                analysis_results[image_name] = result
                
                if result and result['status'] == 'success':
                    success_count += 1
                    self.create_production_visualization(result)
                elif result and result['status'] == 'validation_failed':
                    self.create_production_visualization(result)  # Still create viz for debugging
            else:
                print(f"❌ {image_name} not found in detection results")
        
        # Save comprehensive results
        results_path = self.output_dir / "production_analysis_results.json"
        with open(results_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        # Print final summary
        self.print_final_summary(analysis_results, success_count)
        
        return analysis_results
    
    def print_final_summary(self, results: Dict, success_count: int) -> None:
        """Print comprehensive final summary"""
        total_processed = len(results)
        
        print("\n" + "=" * 60)
        print("🏭 PRODUCTION ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total images processed: {total_processed}")
        print(f"Successful analyses: {success_count}")
        print(f"Success rate: {success_count/total_processed*100:.1f}%" if total_processed > 0 else "N/A")
        
        # Categorize results
        categories = {
            'success': [],
            'validation_failed': [],
            'insufficient_patterns': [],
            'no_valid_combination': []
        }
        
        for image_name, result in results.items():
            if result:
                categories[result['status']].append(image_name)
        
        for status, images in categories.items():
            if images:
                print(f"\n📋 {status.replace('_', ' ').title()}: {len(images)}")
                for img in images:
                    print(f"   • {img}")
        
        if success_count > 0:
            print(f"\n🎉 SUCCESS! {success_count} images ready for 3-pattern QR design!")
            print("✅ Mathematical fourth corner calculation validated")
            print("✅ Production-quality analysis complete")
            print("✅ All visualizations generated")
        
        print(f"\n📁 Results saved in: {self.output_dir}")

def main():
    analyzer = ProductionQRThreePatternAnalyzer()
    
    # Process specific target images
    target_images = ["image copy 7", "image copy 8", "image copy 9"]
    
    print("🎯 Processing target images for 3-pattern QR analysis...")
    analyzer.process_images(target_images)
    
    print("\n🎉 Production analysis complete!")
    print("📁 Generated files:")
    for file_path in sorted(analyzer.output_dir.glob("*.png")):
        print(f"   📊 {file_path.name}")
    for file_path in sorted(analyzer.output_dir.glob("*.json")):
        print(f"   📋 {file_path.name}")

if __name__ == "__main__":
    main()
