#!/usr/bin/env python3
"""
QR Pattern Selection Comparison
Shows the difference between using all detected patterns vs. best 3 finder patterns
"""

import cv2
import numpy as np
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from enhanced_strict_qr_detector import EnhancedStrictQRDetector
from qr_orientation_detector import QROrientationDetector

def compare_pattern_selection(image_path: str):
    """
    Compare orientation detection using all patterns vs. best 3 patterns
    """
    print(f"\n🔍 Pattern Selection Comparison: {Path(image_path).name}")
    print("=" * 60)
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return
    
    # Detect all patterns
    detector = EnhancedStrictQRDetector()
    all_patterns, _, _ = detector.find_qr_patterns_multi_threshold(image)
    
    print(f"📊 Total patterns detected: {len(all_patterns)}")
    
    if len(all_patterns) < 3:
        print("❌ Not enough patterns for analysis")
        return
    
    # Initialize orientation detector
    orientation_detector = QROrientationDetector()
    
    # Analysis 1: Using all detected patterns (first 3)
    first_three = all_patterns[:3]
    finder_patterns_1 = [{'center': p['center'], 'size': p['size']} for p in first_three]
    orientation_1 = orientation_detector.detect_orientation(finder_patterns_1)
    
    # Analysis 2: Using best 3 patterns (by score)
    best_three = sorted(all_patterns, key=lambda p: p.get('score', 0), reverse=True)[:3]
    finder_patterns_2 = [{'center': p['center'], 'size': p['size']} for p in best_three]
    orientation_2 = orientation_detector.detect_orientation(finder_patterns_2)
    
    # Create comparison visualization
    create_comparison_visualization(image, all_patterns, first_three, best_three, 
                                  orientation_1, orientation_2, image_path)
    
    # Print comparison results
    print("\n📊 COMPARISON RESULTS:")
    print("=" * 30)
    
    if orientation_1:
        angles_1 = orientation_1['angles']
        print(f"Using First 3 Patterns:")
        print(f"  Primary Rotation: {angles_1['primary_rotation']:+6.1f}°")
        print(f"  Skew Angle:       {angles_1['skew_angle']:6.1f}°")
        print(f"  Description:      {orientation_1['description']}")
        print(f"  Pattern Scores:   {[p.get('score', 0) for p in first_three]}")
    else:
        print("Using First 3 Patterns: ❌ Failed")
    
    if orientation_2:
        angles_2 = orientation_2['angles']
        print(f"\nUsing Best 3 Patterns:")
        print(f"  Primary Rotation: {angles_2['primary_rotation']:+6.1f}°")
        print(f"  Skew Angle:       {angles_2['skew_angle']:6.1f}°")
        print(f"  Description:      {orientation_2['description']}")
        print(f"  Pattern Scores:   {[p.get('score', 0) for p in best_three]}")
    else:
        print("Using Best 3 Patterns: ❌ Failed")
    
    # Compare results
    if orientation_1 and orientation_2:
        rot_diff = abs(angles_1['primary_rotation'] - angles_2['primary_rotation'])
        skew_diff = abs(angles_1['skew_angle'] - angles_2['skew_angle'])
        
        print(f"\n📏 Differences:")
        print(f"  Rotation difference: {rot_diff:.1f}°")
        print(f"  Skew difference:     {skew_diff:.1f}°")
        
        if rot_diff < 5 and skew_diff < 5:
            print("✅ Results are very similar - pattern selection doesn't matter much")
        elif rot_diff < 15 and skew_diff < 15:
            print("⚠️  Moderate differences - pattern selection has some impact")
        else:
            print("❗ Significant differences - pattern selection is important!")

def create_comparison_visualization(image, all_patterns, first_three, best_three, 
                                  orientation_1, orientation_2, image_path):
    """Create side-by-side comparison visualization"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: All detected patterns
    ax1 = axes[0, 0]
    ax1.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax1.set_title(f"All {len(all_patterns)} Detected Patterns", fontsize=12, fontweight='bold')
    ax1.axis('off')
    
    # Draw all patterns with scores
    for i, pattern in enumerate(all_patterns):
        center = pattern['center']
        if isinstance(center, dict):
            cx, cy = center['x'], center['y']
        else:
            cx, cy = center[0], center[1]
        
        score = pattern.get('score', 0)
        color = plt.cm.viridis(score)  # Color by score
        
        circle = patches.Circle((cx, cy), radius=20, color=color, fill=True, alpha=0.7)
        ax1.add_patch(circle)
        ax1.text(cx, cy - 30, f"{i+1}\n{score:.2f}", color='white', fontsize=10, 
                ha='center', va='center', fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    # Plot 2: First 3 patterns + orientation
    ax2 = axes[0, 1]
    ax2.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax2.set_title("First 3 Patterns + Orientation", fontsize=12, fontweight='bold')
    ax2.axis('off')
    
    if orientation_1:
        draw_orientation_on_axis(ax2, first_three, orientation_1, "First 3")
    
    # Plot 3: Best 3 patterns + orientation
    ax3 = axes[1, 0]
    ax3.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax3.set_title("Best 3 Patterns + Orientation", fontsize=12, fontweight='bold')
    ax3.axis('off')
    
    if orientation_2:
        draw_orientation_on_axis(ax3, best_three, orientation_2, "Best 3")
    
    # Plot 4: Comparison summary
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Create comparison text
    comparison_text = f"Pattern Selection Comparison\n{Path(image_path).name}\n\n"
    
    comparison_text += f"Total patterns detected: {len(all_patterns)}\n\n"
    
    if orientation_1:
        angles_1 = orientation_1['angles']
        comparison_text += f"First 3 Patterns:\n"
        comparison_text += f"  Rotation: {angles_1['primary_rotation']:+.1f}°\n"
        comparison_text += f"  Skew: {angles_1['skew_angle']:.1f}°\n"
        scores_1 = [f"{p.get('score', 0):.2f}" for p in first_three]
        comparison_text += f"  Scores: {scores_1}\n\n"
    
    if orientation_2:
        angles_2 = orientation_2['angles']
        comparison_text += f"Best 3 Patterns:\n"
        comparison_text += f"  Rotation: {angles_2['primary_rotation']:+.1f}°\n"
        comparison_text += f"  Skew: {angles_2['skew_angle']:.1f}°\n"
        scores_2 = [f"{p.get('score', 0):.2f}" for p in best_three]
        comparison_text += f"  Scores: {scores_2}\n\n"
    
    if orientation_1 and orientation_2:
        rot_diff = abs(angles_1['primary_rotation'] - angles_2['primary_rotation'])
        skew_diff = abs(angles_1['skew_angle'] - angles_2['skew_angle'])
        comparison_text += f"Differences:\n"
        comparison_text += f"  Rotation: {rot_diff:.1f}°\n"
        comparison_text += f"  Skew: {skew_diff:.1f}°\n"
    
    ax4.text(0.05, 0.95, comparison_text, transform=ax4.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9))
    
    plt.tight_layout()
    
    # Save comparison
    output_path = f"pattern_comparison_{Path(image_path).stem}.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Comparison visualization saved: {output_path}")
    plt.close()

def draw_orientation_on_axis(ax, patterns, orientation_data, label):
    """Draw orientation analysis on matplotlib axis"""
    positions = orientation_data['positions']
    fourth_corner = orientation_data['fourth_corner']
    
    # Color scheme
    colors = {'top_left': 'red', 'top_right': 'blue', 'bottom_left': 'green'}
    labels_map = {'top_left': 'TL', 'top_right': 'TR', 'bottom_left': 'BL'}
    
    # Draw patterns
    for pos_name, pos_data in positions.items():
        center = pos_data['center']
        color = colors[pos_name]
        label_text = labels_map[pos_name]
        
        circle = patches.Circle(center, radius=15, color=color, fill=True, alpha=0.8)
        ax.add_patch(circle)
        ax.text(center[0], center[1] - 25, label_text, color=color, fontsize=12, 
               fontweight='bold', ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Draw fourth corner
    fourth_circle = patches.Circle(fourth_corner, radius=15, color='purple', 
                                 fill=True, alpha=0.8, linestyle='--')
    ax.add_patch(fourth_circle)
    ax.text(fourth_corner[0], fourth_corner[1] - 25, 'BR', color='purple', 
           fontsize=12, fontweight='bold', ha='center', va='center',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Draw rectangle
    tl = positions['top_left']['center']
    tr = positions['top_right']['center']
    bl = positions['bottom_left']['center']
    
    corners = [tl, tr, fourth_corner, bl, tl]
    xs, ys = zip(*corners)
    ax.plot(xs, ys, 'yellow', linewidth=2, alpha=0.8)

def main():
    """Compare pattern selection for 3-finder pattern images"""
    print("🔍 QR PATTERN SELECTION COMPARISON")
    print("=" * 50)
    
    # Analyze images in 3-finder-pattern folder
    folder_path = "data-qr-ratio-finder/3-finder-pattern"
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"❌ Folder not found: {folder_path}")
        return
    
    # Find image files
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        image_files.extend(folder.glob(ext))
    
    if not image_files:
        print(f"❌ No images found in {folder_path}")
        return
    
    print(f"📊 Comparing pattern selection for {len(image_files)} images")
    
    for image_path in image_files:
        compare_pattern_selection(str(image_path))

if __name__ == "__main__":
    main()
