#!/usr/bin/env python3
"""
QR Pattern Grid Overlay Generator
Creates grid overlays for QR pattern detection results similar to rectangle analysis
"""

import cv2
import numpy as np
import json
import os
from typing import List, Dict, Tuple
import glob

class QRGridOverlay:
    def __init__(self, grid_size: Tuple[int, int] = (21, 21)):
        """Initialize QR Grid Overlay system"""
        self.grid_size = grid_size  # Standard QR code grid size
        
    def create_pattern_overlay(self, image: np.ndarray, patterns: List[Dict], 
                             image_name: str) -> np.ndarray:
        """
        Create grid overlay showing detected QR patterns
        
        Args:
            image: Original image
            patterns: List of detected patterns with centers and scores
            image_name: Name of the image for labeling
            
        Returns:
            Image with grid overlay and pattern annotations
        """
        overlay = image.copy()
        
        # Color scheme for different pattern scores
        colors = {
            'high': (0, 255, 0),      # Green for high scores
            'medium': (0, 255, 255),   # Yellow for medium scores  
            'low': (0, 0, 255),        # Red for low scores
            'rejected': (128, 128, 128) # Gray for rejected patterns
        }
        
        # Draw each detected pattern
        for i, pattern in enumerate(patterns):
            center = tuple(pattern['center'])
            size = pattern['size']
            score = pattern['overall_score']
            
            # Determine color based on score
            if score >= 0.8:
                color = colors['high']
            elif score >= 0.6:
                color = colors['medium']
            elif score >= 0.4:
                color = colors['low']
            else:
                color = colors['rejected']
            
            # Draw pattern boundary
            half_size = size // 2
            top_left = (center[0] - half_size, center[1] - half_size)
            bottom_right = (center[0] + half_size, center[1] + half_size)
            cv2.rectangle(overlay, top_left, bottom_right, color, 2)
            
            # Draw center cross
            cross_size = 5
            cv2.line(overlay, 
                    (center[0] - cross_size, center[1]), 
                    (center[0] + cross_size, center[1]), 
                    color, 2)
            cv2.line(overlay, 
                    (center[0], center[1] - cross_size), 
                    (center[0], center[1] + cross_size), 
                    color, 2)
            
            # Add pattern label with scores
            label_y = center[1] - half_size - 10
            if label_y < 20:
                label_y = center[1] + half_size + 25
                
            # Main pattern label
            pattern_label = f"P{pattern['pattern_id']}"
            cv2.putText(overlay, pattern_label, 
                       (center[0] - 15, label_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Score breakdown
            comp_scores = pattern['component_scores']
            score_text = f"C:{comp_scores['concentric']:.2f} L:{comp_scores['line_pattern']:.2f} S:{comp_scores['symmetry']:.2f}"
            cv2.putText(overlay, score_text, 
                       (center[0] - 40, label_y + 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Overall score
            overall_text = f"Tot:{score:.2f}"
            cv2.putText(overlay, overall_text, 
                       (center[0] - 20, label_y + 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Method indicator
            method_text = pattern['method'][:4].upper()
            cv2.putText(overlay, method_text, 
                       (center[0] - 15, label_y + 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Add image title and summary
        title_text = f"{image_name} - {len(patterns)} patterns detected"
        cv2.putText(overlay, title_text, 
                   (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Add legend
        legend_y = 60
        legend_items = [
            ("HIGH: 0.8+", colors['high']),
            ("MED: 0.6-0.8", colors['medium']),
            ("LOW: 0.4-0.6", colors['low']),
            ("REJ: <0.4", colors['rejected'])
        ]
        
        for i, (text, color) in enumerate(legend_items):
            cv2.putText(overlay, text, 
                       (10, legend_y + i * 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return overlay
    
    def create_score_breakdown_overlay(self, image: np.ndarray, patterns: List[Dict],
                                     image_name: str) -> np.ndarray:
        """
        Create detailed score breakdown overlay
        
        Args:
            image: Original image
            patterns: List of detected patterns
            image_name: Name of the image
            
        Returns:
            Image with detailed score analysis
        """
        overlay = image.copy()
        
        # Create semi-transparent background for text
        text_bg = np.zeros_like(overlay)
        
        # Color coding for score components
        concentric_color = (255, 0, 0)    # Blue for concentric
        line_color = (0, 255, 0)          # Green for line pattern
        symmetry_color = (0, 0, 255)      # Red for symmetry
        
        y_offset = 30
        line_height = 25
        
        # Title
        cv2.putText(text_bg, f"Score Breakdown - {image_name}", 
                   (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_offset += line_height * 2
        
        # Headers
        header = "Pat | Concentric | Line Pat | Symmetry | Total | Method"
        cv2.putText(text_bg, header, 
                   (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += line_height
        
        # Pattern details
        for pattern in patterns:
            comp = pattern['component_scores']
            
            # Pattern row
            row_text = f"P{pattern['pattern_id']:2d} |"
            cv2.putText(text_bg, row_text, 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Concentric score
            conc_text = f"   {comp['concentric']:.3f}   |"
            cv2.putText(text_bg, conc_text, 
                       (60, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, concentric_color, 1)
            
            # Line pattern score
            line_text = f"  {comp['line_pattern']:.3f}  |"
            cv2.putText(text_bg, line_text, 
                       (170, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 1)
            
            # Symmetry score
            sym_text = f"  {comp['symmetry']:.3f}  |"
            cv2.putText(text_bg, sym_text, 
                       (260, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, symmetry_color, 1)
            
            # Total score
            total_text = f" {pattern['overall_score']:.3f} |"
            cv2.putText(text_bg, total_text, 
                       (340, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Method
            method_text = pattern['method']
            cv2.putText(text_bg, method_text, 
                       (400, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            y_offset += line_height
        
        # Add scoring explanation
        y_offset += line_height
        explanations = [
            "Scoring: Concentric(40%) + Line Pattern(40%) + Symmetry(20%)",
            "Concentric: Validates QR finder pattern ring structure", 
            "Line Pattern: Checks 1:1:3:1:1 ratio in scan lines",
            "Symmetry: Measures horizontal/vertical symmetry"
        ]
        
        for explanation in explanations:
            cv2.putText(text_bg, explanation, 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_offset += 18
        
        # Blend text background with original image
        alpha = 0.7
        overlay = cv2.addWeighted(overlay, alpha, text_bg, 1 - alpha, 0)
        
        return overlay
    
    def process_all_pattern_results(self, results_dir: str = "results/pattern-grids",
                                  output_dir: str = "results/qr-grid-overlays"):
        """
        Process all pattern detection results and create grid overlays
        
        Args:
            results_dir: Directory containing pattern analysis JSON files
            output_dir: Directory to save overlay images
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all analysis JSON files
        json_files = glob.glob(os.path.join(results_dir, "*_detailed_analysis.json"))
        
        summary_data = {}
        
        for json_file in json_files:
            try:
                # Load analysis data
                with open(json_file, 'r') as f:
                    analysis_data = json.load(f)
                
                image_name = analysis_data['image_name']
                patterns = analysis_data['patterns']
                
                print(f"Processing {image_name}...")
                
                # Load original image
                image_path = os.path.join("data-qr-ratio-finder", image_name)
                if not os.path.exists(image_path):
                    print(f"⚠️  Image not found: {image_path}")
                    continue
                
                image = cv2.imread(image_path)
                if image is None:
                    print(f"⚠️  Could not load image: {image_path}")
                    continue
                
                # Create pattern overlay
                pattern_overlay = self.create_pattern_overlay(image, patterns, image_name)
                
                # Create score breakdown overlay  
                score_overlay = self.create_score_breakdown_overlay(image, patterns, image_name)
                
                # Save overlays
                base_name = os.path.splitext(image_name)[0]
                
                pattern_output = os.path.join(output_dir, f"{base_name}_pattern_overlay.png")
                cv2.imwrite(pattern_output, pattern_overlay)
                
                score_output = os.path.join(output_dir, f"{base_name}_score_breakdown.png")
                cv2.imwrite(score_output, score_overlay)
                
                # Update summary
                summary_data[image_name] = {
                    "patterns_found": len(patterns),
                    "highest_score": max([p['overall_score'] for p in patterns]) if patterns else 0,
                    "avg_score": sum([p['overall_score'] for p in patterns]) / len(patterns) if patterns else 0,
                    "pattern_overlay": pattern_output,
                    "score_breakdown": score_output,
                    "component_breakdown": {
                        "avg_concentric": sum([p['component_scores']['concentric'] for p in patterns]) / len(patterns) if patterns else 0,
                        "avg_line_pattern": sum([p['component_scores']['line_pattern'] for p in patterns]) / len(patterns) if patterns else 0,
                        "avg_symmetry": sum([p['component_scores']['symmetry'] for p in patterns]) / len(patterns) if patterns else 0
                    }
                }
                
                print(f"✓ Created overlays for {image_name}")
                
            except Exception as e:
                print(f"❌ Error processing {json_file}: {e}")
                continue
        
        # Save summary
        summary_file = os.path.join(output_dir, "overlay_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        print("\n🎯 Grid overlay generation complete!")
        print(f"📁 Output directory: {output_dir}")
        print(f"📊 Summary saved to: {summary_file}")
        print(f"🔍 Processed {len(summary_data)} images")

def main():
    """Main execution function"""
    print("🎯 Starting QR Pattern Grid Overlay Generation...")
    
    overlay_generator = QRGridOverlay()
    overlay_generator.process_all_pattern_results()

if __name__ == "__main__":
    main()
