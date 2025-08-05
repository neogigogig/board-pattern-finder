#!/usr/bin/env python3
"""
Test script to verify finder pattern size highlighting
"""
import cv2
import numpy as np
import os
import sys

# Add the current directory to Python path
sys.path.append('/Users/devjitneogi/Documents/personalCode/barcode/parking-board-finder')

from qr_rectangle_detector import GridSystem

def test_pattern_highlighting():
    """Test the pattern highlighting functionality"""
    
    # Create a sample image
    test_image = np.ones((400, 400, 3), dtype=np.uint8) * 255  # White background
    
    # Sample corner points (forming a rectangle)
    corners = [(100, 100), (300, 100), (300, 300), (100, 300)]
    
    # Sample patterns with position, score, and size information
    patterns = [
        {'position': (100, 100), 'score': 0.85, 'size': 25},
        {'position': (300, 100), 'score': 0.82, 'size': 30},
        {'position': (300, 300), 'score': 0.88, 'size': 28},
        {'position': (100, 300), 'score': 0.90, 'size': 22}
    ]
    
    # Create grid system and apply overlay
    grid_system = GridSystem()
    
    # Apply grid overlay with pattern highlighting
    overlay_image = grid_system.apply_grid_overlay(
        test_image, 
        corners, 
        patterns=patterns,
        grid_color=(0, 255, 0),
        line_thickness=2
    )
    
    # Save the test image
    output_path = '/Users/devjitneogi/Documents/personalCode/barcode/parking-board-finder/test_pattern_highlighting.png'
    cv2.imwrite(output_path, overlay_image)
    
    print(f"✅ Test image saved to: {output_path}")
    print(f"📊 Pattern information highlighted:")
    for i, pattern in enumerate(patterns):
        print(f"   Pattern {i+1}: Position {pattern['position']}, Size {pattern['size']}px, Score {pattern['score']:.3f}")
    
    return output_path

if __name__ == "__main__":
    test_pattern_highlighting()
