#!/usr/bin/env python3
"""
Phase 1 Visualization Tool
Visualizes the geometric correction process: 4th corner detection and perspective correction
"""

import cv2
import numpy as np
import os
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from qr_data_reader import QRDataReader
from enhanced_strict_qr_detector import EnhancedStrictQRDetector

class Phase1Visualizer:
    def __init__(self):
        self.results_dir = "results/phase1_visualization"
        os.makedirs(self.results_dir, exist_ok=True)
        
    def visualize_fourth_corner_calculation(self, image: np.ndarray, finder_patterns: List[Dict], 
                                          fourth_corner: Tuple[int, int], output_path: str):
        """Create visualization showing 4th corner calculation process"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # Display the original image
        if len(image.shape) == 3:
            ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            ax.imshow(image, cmap='gray')
        
        # Extract centers
        centers = [p['center'] for p in finder_patterns]
        
        # Color scheme
        colors = ['red', 'green', 'blue']
        labels = ['Pattern 1', 'Pattern 2', 'Pattern 3']
        
        # Draw finder pattern centers
        for i, (center, color, label) in enumerate(zip(centers, colors, labels)):
            circle = patches.Circle(center, radius=15, color=color, fill=True, alpha=0.7)
            ax.add_patch(circle)
            ax.annotate(label, center, xytext=(10, 10), textcoords='offset points',
                       fontsize=12, fontweight='bold', color=color)
        
        # Draw the calculated 4th corner
        fourth_circle = patches.Circle(fourth_corner, radius=15, color='purple', fill=True, alpha=0.7)
        ax.add_patch(fourth_circle)
        ax.annotate('4th Corner\n(Calculated)', fourth_corner, xytext=(10, 10), 
                   textcoords='offset points', fontsize=12, fontweight='bold', color='purple')
        
        # Draw lines connecting the patterns to show parallelogram
        all_corners = centers + [fourth_corner]
        
        # Create parallelogram outline
        parallelogram_order = [0, 1, 3, 2, 0]  # Close the shape
        for i in range(len(parallelogram_order)-1):
            start_idx = parallelogram_order[i]
            end_idx = parallelogram_order[i+1]
            start_point = all_corners[start_idx]
            end_point = all_corners[end_idx]
            
            ax.plot([start_point[0], end_point[0]], [start_point[1], end_point[1]], 
                   'yellow', linewidth=3, alpha=0.8)
        
        # Add calculation explanation
        ax.text(0.02, 0.98, '4th Corner Calculation:\nUsing parallelogram properties\nP4 = P2 + P3 - P1', 
                transform=ax.transAxes, fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title('Phase 1: Fourth Corner Detection', fontsize=16, fontweight='bold')
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"🎯 Saved 4th corner visualization: {output_path}")
    
    def visualize_perspective_correction(self, original: np.ndarray, corrected: np.ndarray, 
                                       finder_patterns: List[Dict], fourth_corner: Tuple[int, int],
                                       ratio: float, output_path: str):
        """Create before/after visualization of perspective correction"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Original image with corner annotations
        if len(original.shape) == 3:
            ax1.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        else:
            ax1.imshow(original, cmap='gray')
        
        # Draw corner markers
        centers = [p['center'] for p in finder_patterns]
        all_corners = centers + [fourth_corner]
        corner_labels = ['TL', 'TR', 'BL', 'BR']
        colors = ['red', 'green', 'blue', 'purple']
        
        for corner, label, color in zip(all_corners, corner_labels, colors):
            circle = patches.Circle(corner, radius=12, color=color, fill=True, alpha=0.8)
            ax1.add_patch(circle)
            ax1.annotate(label, corner, xytext=(0, 0), textcoords='offset points',
                        ha='center', va='center', fontsize=10, fontweight='bold', color='white')
        
        ax1.set_title('Original Image\n(Detected Corners)', fontsize=14, fontweight='bold')
        ax1.axis('off')
        
        # Corrected image
        if len(corrected.shape) == 3:
            ax2.imshow(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB))
        else:
            ax2.imshow(corrected, cmap='gray')
        
        ax2.set_title(f'Perspective Corrected\n(Ratio: {ratio:.2f})', fontsize=14, fontweight='bold')
        ax2.axis('off')
        
        # Add dimension info
        h, w = corrected.shape[:2]
        ax2.text(0.02, 0.02, f'Dimensions: {w}x{h}\nWidth:Height = {ratio:.2f}:1', 
                transform=ax2.transAxes, fontsize=10, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"🔄 Saved perspective correction visualization: {output_path}")
    
    def visualize_ratio_comparison(self, image: np.ndarray, finder_patterns: List[Dict], 
                                 test_ratios: List[Tuple[float, str]], output_path: str):
        """Create comparison of different aspect ratios"""
        num_ratios = len(test_ratios)
        fig, axes = plt.subplots(2, num_ratios, figsize=(4*num_ratios, 8))
        
        if num_ratios == 1:
            axes = axes.reshape(2, 1)
        
        for i, (ratio, description) in enumerate(test_ratios):
            # Create QR reader with specific ratio
            reader = QRDataReader(width_height_ratio=ratio)
            
            # Apply perspective correction
            corrected = reader.correct_perspective(image, finder_patterns, output_width=200)
            
            # Original with corners (top row)
            if len(image.shape) == 3:
                axes[0, i].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            else:
                axes[0, i].imshow(image, cmap='gray')
            
            # Draw corners
            centers = [p['center'] for p in finder_patterns]
            fourth_corner = reader.calculate_fourth_corner(finder_patterns)
            if fourth_corner:
                all_corners = centers + [fourth_corner]
                for corner in all_corners:
                    circle = patches.Circle(corner, radius=8, color='red', fill=True, alpha=0.7)
                    axes[0, i].add_patch(circle)
            
            axes[0, i].set_title(f'Original\n{description}', fontsize=12)
            axes[0, i].axis('off')
            
            # Corrected image (bottom row)
            if corrected is not None:
                if len(corrected.shape) == 3:
                    axes[1, i].imshow(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB))
                else:
                    axes[1, i].imshow(corrected, cmap='gray')
                
                h, w = corrected.shape[:2]
                axes[1, i].set_title(f'Corrected {w}x{h}\nRatio: {ratio:.2f}', fontsize=12)
            else:
                axes[1, i].text(0.5, 0.5, 'Correction\nFailed', ha='center', va='center',
                               transform=axes[1, i].transAxes, fontsize=14, color='red')
                axes[1, i].set_title(f'Failed\nRatio: {ratio:.2f}', fontsize=12, color='red')
            
            axes[1, i].axis('off')
        
        plt.suptitle('Phase 1: Aspect Ratio Comparison', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Saved ratio comparison: {output_path}")
    
    def create_phase1_summary(self, image_path: str, output_dir: Optional[str] = None):
        """Create comprehensive Phase 1 visualization for a given image"""
        if output_dir is None:
            output_dir = self.results_dir
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return
        
        print(f"🎨 Creating Phase 1 visualization for: {os.path.basename(image_path)}")
        
        # Detect QR patterns
        detector = EnhancedStrictQRDetector()
        detection_result = detector.find_qr_patterns_multi_threshold(image)
        
        # Extract just the patterns (method returns multiple values)
        if isinstance(detection_result, tuple):
            finder_patterns = detection_result[0]
        else:
            finder_patterns = detection_result
        
        if not finder_patterns:
            print("❌ No QR patterns detected in image")
            return
        
        if len(finder_patterns) < 3:
            print("❌ Not enough finder patterns detected")
            return
        
        # Base filename
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # Test different ratios
        test_ratios = [
            (1.0, "Square (1:1)"),
            (1.5, "Rectangle (3:2)"),
            (0.67, "Rectangle (2:3)"),
            (2.0, "Wide (2:1)")
        ]
        
        # Create QR reader for default ratio
        reader = QRDataReader(width_height_ratio=1.0)
        
        # Calculate 4th corner
        fourth_corner = reader.calculate_fourth_corner(finder_patterns)
        if fourth_corner is None:
            print("❌ Could not calculate 4th corner")
            return
        
        # 1. Fourth corner visualization
        corner_path = os.path.join(output_dir, f"{base_name}_fourth_corner.png")
        self.visualize_fourth_corner_calculation(image, finder_patterns, fourth_corner, corner_path)
        
        # 2. Perspective correction visualization (default ratio)
        corrected = reader.correct_perspective(image, finder_patterns, output_width=300)
        if corrected is not None:
            perspective_path = os.path.join(output_dir, f"{base_name}_perspective_correction.png")
            self.visualize_perspective_correction(image, corrected, finder_patterns, fourth_corner, 1.0, perspective_path)
        
        # 3. Ratio comparison
        ratio_path = os.path.join(output_dir, f"{base_name}_ratio_comparison.png")
        self.visualize_ratio_comparison(image, finder_patterns, test_ratios, ratio_path)
        
        # 4. Create summary report
        self.create_html_report(base_name, output_dir)
        
        print(f"✅ Phase 1 visualization complete! Check {output_dir}")
    
    def create_html_report(self, base_name: str, output_dir: str):
        """Create HTML report for Phase 1 results"""
        html_path = os.path.join(output_dir, f"{base_name}_phase1_report.html")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phase 1 Visualization Report - {base_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .visualization-section {{
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .image-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .image-container img {{
            max-width: 100%;
            height: auto;
            border: 2px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .description {{
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }}
        .phase-info {{
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .feature-list {{
            list-style-type: none;
            padding: 0;
        }}
        .feature-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .feature-list li:before {{
            content: "🔹 ";
            color: #3498db;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Phase 1 Visualization Report</h1>
        <h2>Image: {base_name}</h2>
        
        <div class="phase-info">
            <h3>📋 Phase 1 Overview</h3>
            <p><strong>Phase 1</strong> focuses on geometric correction of detected QR patterns:</p>
            <ul class="feature-list">
                <li><strong>Fourth Corner Detection:</strong> Calculate missing corner using parallelogram properties</li>
                <li><strong>Perspective Correction:</strong> Transform skewed pattern to rectangular view</li>
                <li><strong>Flexible Ratios:</strong> Support for rectangular patterns (not just square)</li>
                <li><strong>Geometric Validation:</strong> Ensure proper corner ordering and dimensions</li>
            </ul>
        </div>
        
        <div class="visualization-section">
            <h2>🎯 1. Fourth Corner Detection</h2>
            <div class="description">
                <p>Shows how the missing fourth corner is calculated from three detected finder patterns using parallelogram geometry.</p>
            </div>
            <div class="image-container">
                <img src="{base_name}_fourth_corner.png" alt="Fourth Corner Detection">
            </div>
        </div>
        
        <div class="visualization-section">
            <h2>🔄 2. Perspective Correction</h2>
            <div class="description">
                <p>Demonstrates the transformation from the original skewed view to a properly aligned rectangular output.</p>
            </div>
            <div class="image-container">
                <img src="{base_name}_perspective_correction.png" alt="Perspective Correction">
            </div>
        </div>
        
        <div class="visualization-section">
            <h2>📊 3. Aspect Ratio Comparison</h2>
            <div class="description">
                <p>Compares different aspect ratios to show flexibility in handling rectangular patterns of various dimensions.</p>
            </div>
            <div class="image-container">
                <img src="{base_name}_ratio_comparison.png" alt="Ratio Comparison">
            </div>
        </div>
        
        <div class="phase-info">
            <h3>🔧 Technical Details</h3>
            <ul class="feature-list">
                <li><strong>Input:</strong> Original image with detected finder patterns</li>
                <li><strong>Processing:</strong> Geometric calculations and perspective transformation</li>
                <li><strong>Output:</strong> Perspective-corrected rectangular image</li>
                <li><strong>Flexibility:</strong> Configurable width-to-height ratios</li>
                <li><strong>Quality:</strong> Preserves pattern structure while correcting distortion</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #666;">
            <p>Generated by Phase 1 Visualizer | QR Data Reader System</p>
        </div>
    </div>
</body>
</html>"""
        
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        print(f"📄 Created HTML report: {html_path}")

def test_phase1_visualization():
    """Test Phase 1 visualization with sample data"""
    print("🎨 Testing Phase 1 Visualization")
    
    # Create visualizer
    visualizer = Phase1Visualizer()
    
    # Create a test image with mock QR pattern
    test_image = np.ones((400, 400, 3), dtype=np.uint8) * 255
    
    # Draw mock finder patterns (black squares)
    finder_positions = [(50, 50), (350, 50), (50, 350)]
    for pos in finder_positions:
        cv2.rectangle(test_image, (pos[0]-15, pos[1]-15), (pos[0]+15, pos[1]+15), (0, 0, 0), -1)
    
    # Save test image
    test_image_path = "test_qr_pattern.png"
    cv2.imwrite(test_image_path, test_image)
    
    # Mock finder patterns
    finder_patterns = [
        {'center': (50, 50), 'size': 30},
        {'center': (350, 50), 'size': 30},
        {'center': (50, 350), 'size': 30}
    ]
    
    # Test individual visualizations
    reader = QRDataReader(width_height_ratio=1.0)
    fourth_corner = reader.calculate_fourth_corner(finder_patterns)
    
    if fourth_corner:
        # Test fourth corner visualization
        visualizer.visualize_fourth_corner_calculation(
            test_image, finder_patterns, fourth_corner,
            os.path.join(visualizer.results_dir, "test_fourth_corner.png")
        )
        
        # Test perspective correction visualization
        corrected = reader.correct_perspective(test_image, finder_patterns, output_width=200)
        if corrected is not None:
            visualizer.visualize_perspective_correction(
                test_image, corrected, finder_patterns, fourth_corner, 1.0,
                os.path.join(visualizer.results_dir, "test_perspective_correction.png")
            )
        
        # Test ratio comparison
        test_ratios = [(1.0, "Square"), (1.5, "Wide"), (0.67, "Tall")]
        visualizer.visualize_ratio_comparison(
            test_image, finder_patterns, test_ratios,
            os.path.join(visualizer.results_dir, "test_ratio_comparison.png")
        )
        
        # Create test report
        visualizer.create_html_report("test", visualizer.results_dir)
    
    print(f"✅ Test visualizations created in: {visualizer.results_dir}")
    
    # Clean up test image
    if os.path.exists(test_image_path):
        os.remove(test_image_path)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Visualize specific image
        image_path = sys.argv[1]
        visualizer = Phase1Visualizer()
        visualizer.create_phase1_summary(image_path)
    else:
        # Run test
        test_phase1_visualization()
