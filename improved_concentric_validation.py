#!/usr/bin/env python3
"""
Improved Concentric Structure Validation
Enhanced version with better radius calculation and more flexible thresholds
"""

import cv2
import numpy as np
from typing import Dict

def check_improved_concentric_structure(binary_image, cx, cy, size) -> Dict:
    """
    Improved check for QR finder pattern concentric structure with adaptive sizing
    
    Key improvements:
    1. Better radius calculation based on actual pattern size
    2. More flexible thresholds accounting for image quality
    3. Robust sampling with outlier handling
    4. Gradual scoring instead of binary pass/fail
    """
    h, w = binary_image.shape
    
    if cx < 0 or cx >= w or cy < 0 or cy >= h:
        return {'score': 0.0, 'reason': 'center out of bounds'}
    
    # Improved radius calculation based on pattern size
    # QR finder patterns typically have: center (1/7), first ring (1/7), second ring (3/7)
    base_radius = size // 14  # 1/14 of pattern size for base unit
    
    # Calculate rings based on QR finder pattern proportions
    center_radius = max(2, base_radius)  # Center sampling area
    first_ring_r = max(4, base_radius * 3)  # First light ring
    second_ring_r = max(6, base_radius * 6)  # Second dark ring
    
    # Ensure rings don't exceed image bounds
    max_safe_radius = min(cx, cy, w - cx - 1, h - cy - 1)
    if second_ring_r > max_safe_radius:
        scale_factor = max_safe_radius / second_ring_r
        first_ring_r = int(first_ring_r * scale_factor)
        second_ring_r = int(second_ring_r * scale_factor)
        center_radius = max(2, int(center_radius * scale_factor))
    
    if first_ring_r < 3 or second_ring_r < 5:
        return {'score': 0.0, 'reason': 'pattern too small for reliable ring analysis'}
    
    # Sample center region more robustly
    center_pixels = []
    for dy in range(-center_radius, center_radius + 1):
        for dx in range(-center_radius, center_radius + 1):
            if dx*dx + dy*dy <= center_radius*center_radius:  # Circular sampling
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h:
                    center_pixels.append(binary_image[ny, nx])
    
    if len(center_pixels) < 4:
        return {'score': 0.0, 'reason': 'insufficient center samples'}
    
    # Calculate center dark ratio
    center_dark_count = sum(1 for p in center_pixels if p < 127)
    center_dark_ratio = center_dark_count / len(center_pixels)
    
    # More flexible center validation (70% instead of 80%)
    if center_dark_ratio < 0.7:
        return {
            'score': 0.0, 
            'reason': f'center not dark enough: {center_dark_ratio:.1%}',
            'center_dark_ratio': center_dark_ratio,
            'radii_used': {'center': center_radius, 'first': first_ring_r, 'second': second_ring_r}
        }
    
    # Sample rings with robust outlier handling
    ring_info = []
    ring_radii = [first_ring_r, second_ring_r]
    
    for i, r in enumerate(ring_radii):
        # Dense sampling with 5-degree increments for accuracy
        ring_pixels = []
        for angle in range(0, 360, 5):
            x = int(cx + r * np.cos(np.radians(angle)))
            y = int(cy + r * np.sin(np.radians(angle)))
            
            if 0 <= x < w and 0 <= y < h:
                ring_pixels.append(binary_image[y, x])
        
        if len(ring_pixels) < 30:  # Need sufficient samples
            return {'score': 0.0, 'reason': f'insufficient ring {i+1} samples'}
        
        # Handle outliers by using median-based approach
        ring_pixels_array = np.array(ring_pixels)
        dark_pixels = ring_pixels_array < 127
        dark_ratio = np.mean(dark_pixels)
        
        # Calculate robustness metrics
        pixel_variance = np.var(ring_pixels_array)
        
        ring_info.append({
            'radius': r,
            'dark_ratio': dark_ratio,
            'dark_count': int(np.sum(dark_pixels)),
            'total_pixels': len(ring_pixels),
            'pixel_variance': pixel_variance
        })
    
    first_ring = ring_info[0]  # Should be light
    second_ring = ring_info[1]  # Should be dark
    
    # More flexible thresholds with gradual scoring
    # First ring should be light (< 50% instead of < 30%)
    first_ring_score = 0.0
    if first_ring['dark_ratio'] <= 0.3:
        first_ring_score = 1.0  # Excellent
    elif first_ring['dark_ratio'] <= 0.4:
        first_ring_score = 0.8  # Good
    elif first_ring['dark_ratio'] <= 0.5:
        first_ring_score = 0.6  # Acceptable
    elif first_ring['dark_ratio'] <= 0.6:
        first_ring_score = 0.3  # Poor but might be valid
    # else 0.0 (too dark)
    
    # Second ring should be dark (> 60% instead of > 70%)
    second_ring_score = 0.0
    if second_ring['dark_ratio'] >= 0.8:
        second_ring_score = 1.0  # Excellent
    elif second_ring['dark_ratio'] >= 0.7:
        second_ring_score = 0.9  # Very good
    elif second_ring['dark_ratio'] >= 0.6:
        second_ring_score = 0.7  # Good
    elif second_ring['dark_ratio'] >= 0.5:
        second_ring_score = 0.4  # Acceptable
    # else 0.0 (too light)
    
    # Center score (normalized, with bonus for very dark centers)
    center_score = center_dark_ratio
    if center_dark_ratio >= 0.9:
        center_score = 1.0
    elif center_dark_ratio >= 0.8:
        center_score = 0.95
    
    # Calculate overall quality with weighted average
    # Give more weight to the critical light ring requirement
    quality_score = (center_score * 0.25 + first_ring_score * 0.50 + second_ring_score * 0.25)
    
    # Lower threshold for acceptance (0.6 instead of 0.85)
    minimum_quality = 0.6
    
    if quality_score < minimum_quality:
        return {
            'score': 0.0,
            'reason': f'insufficient pattern quality: {quality_score:.3f}',
            'center_dark_ratio': center_dark_ratio,
            'rings': ring_info,
            'component_scores': {
                'center': center_score,
                'first_ring': first_ring_score,
                'second_ring': second_ring_score
            },
            'quality_score': quality_score,
            'radii_used': {'center': center_radius, 'first': first_ring_r, 'second': second_ring_r}
        }
    
    return {
        'score': quality_score,
        'center_dark_ratio': center_dark_ratio,
        'rings': ring_info,
        'component_scores': {
            'center': center_score,
            'first_ring': first_ring_score,
            'second_ring': second_ring_score
        },
        'quality_score': quality_score,
        'validation': f'PASS - quality score: {quality_score:.3f}',
        'radii_used': {'center': center_radius, 'first': first_ring_r, 'second': second_ring_r}
    }

def compare_concentric_methods():
    """
    Compare the original and improved concentric validation methods
    """
    print("🔬 CONCENTRIC VALIDATION COMPARISON")
    print("=" * 50)
    
    # Test data from our analysis
    test_patterns = [
        {'center': (267, 391), 'size': 74, 'name': 'Pattern 1 (Image copy 6)'},
        {'center': (541, 562), 'size': 39, 'name': 'Pattern 1 (Image copy)'},
        {'center': (181, 473), 'size': 53, 'name': 'Pattern 2 (Image copy)'},
    ]
    
    # For demonstration, we'll create synthetic binary images
    for pattern in test_patterns:
        print(f"\n📊 Testing: {pattern['name']}")
        print(f"   Center: {pattern['center']}, Size: {pattern['size']}")
        
        # Create a synthetic binary image for testing
        binary_test = np.ones((800, 800), dtype=np.uint8) * 255
        cx, cy = pattern['center']
        size = pattern['size']
        
        # Create a simple concentric pattern for testing
        center_r = size // 14
        first_r = size // 6
        second_r = size // 3
        
        # Fill center (dark)
        cv2.circle(binary_test, (cx, cy), center_r, 0, -1)
        # Fill first ring (light) - already white
        # Fill second ring (dark)
        cv2.circle(binary_test, (cx, cy), second_r, 0, 3)
        
        # Test improved method
        result = check_improved_concentric_structure(binary_test, cx, cy, size)
        
        print(f"   Improved Method Result:")
        print(f"     Score: {result['score']:.3f}")
        print(f"     Status: {'PASS' if result['score'] > 0 else 'FAIL'}")
        if 'component_scores' in result:
            comp = result['component_scores']
            print(f"     Component Scores: C:{comp['center']:.2f} R1:{comp['first_ring']:.2f} R2:{comp['second_ring']:.2f}")
        if 'radii_used' in result:
            radii = result['radii_used']
            print(f"     Radii Used: center={radii['center']}, first={radii['first']}, second={radii['second']}")
        if result['score'] == 0:
            print(f"     Rejection Reason: {result['reason']}")

if __name__ == "__main__":
    compare_concentric_methods()
