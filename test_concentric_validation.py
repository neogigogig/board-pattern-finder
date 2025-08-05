#!/usr/bin/env python3
"""
Concentric Structure Validation Test
Analyzes the concentric structure validation to determine if it's working correctly
"""

import cv2
import numpy as np
import json
import os
from enhanced_strict_qr_detector import EnhancedStrictQRDetector

def visualize_concentric_analysis(image_path, pattern_data):
    """
    Create detailed visualization of concentric structure analysis
    """
    print(f"\n🔍 CONCENTRIC STRUCTURE ANALYSIS: {os.path.basename(image_path)}")
    print("=" * 60)
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load {image_path}")
        return
    
    detector = EnhancedStrictQRDetector()
    gray, binary_results = detector.preprocess_image(image)
    
    # Analyze each detected pattern
    for i, pattern in enumerate(pattern_data['patterns']):
        center = pattern['center']
        size = pattern['size']
        method = pattern['method']
        concentric_details = pattern['concentric_details']
        
        print(f"\n📊 Pattern {pattern['pattern_id']} Analysis:")
        print(f"   Center: ({center[0]}, {center[1]})")
        print(f"   Size: {size}")
        print(f"   Method: {method}")
        print(f"   Concentric Score: {concentric_details['score']}")
        print(f"   Rejection Reason: {concentric_details['reason']}")
        
        # Get the binary image used for this pattern
        binary_image = binary_results[method]
        
        # Create visualization
        vis_image = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
        cx, cy = center
        
        # Draw center area (3x3)
        cv2.rectangle(vis_image, (cx-1, cy-1), (cx+1, cy+1), (0, 255, 0), 2)
        
        # Calculate ring radii like the function does
        radius = min(size // 2, min(cx, cy, binary_image.shape[1] - cx - 1, binary_image.shape[0] - cy - 1))
        max_radius = min(radius, 15)
        first_ring_r = max(3, max_radius // 3)
        second_ring_r = max(5, (max_radius * 2) // 3)
        
        print(f"   Calculated radii: first={first_ring_r}, second={second_ring_r}")
        
        # Draw rings
        cv2.circle(vis_image, (cx, cy), first_ring_r, (255, 0, 0), 1)  # Blue for first ring
        cv2.circle(vis_image, (cx, cy), second_ring_r, (0, 0, 255), 1)  # Red for second ring
        
        # Sample center pixels like the function does
        center_pixels = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < binary_image.shape[1] and 0 <= ny < binary_image.shape[0]:
                    center_pixels.append(binary_image[ny, nx])
        
        center_dark_count = sum(1 for p in center_pixels if p < 127)
        center_dark_ratio = center_dark_count / len(center_pixels) if center_pixels else 0
        
        print(f"   Center analysis:")
        print(f"     Pixels sampled: {len(center_pixels)}")
        print(f"     Dark pixels: {center_dark_count}")
        print(f"     Dark ratio: {center_dark_ratio:.1%}")
        print(f"     Threshold: 80%")
        print(f"     ✓ Pass: {center_dark_ratio >= 0.8}")
        
        # Analyze rings like the function does
        if 'rings' in concentric_details:
            for ring_idx, ring_info in enumerate(concentric_details['rings']):
                ring_type = "light" if ring_idx == 0 else "dark"
                expected_threshold = "< 30%" if ring_idx == 0 else "> 70%"
                actual_ratio = ring_info['dark_ratio']
                
                print(f"   Ring {ring_idx + 1} analysis (should be {ring_type}):")
                print(f"     Radius: {ring_info['radius']}")
                print(f"     Dark pixels: {ring_info['dark_count']}/{ring_info['total_pixels']}")
                print(f"     Dark ratio: {actual_ratio:.1%}")
                print(f"     Expected: {expected_threshold}")
                
                if ring_idx == 0:  # First ring should be light
                    passes = actual_ratio <= 0.3
                    print(f"     ✓ Pass: {passes}")
                else:  # Second ring should be dark
                    passes = actual_ratio >= 0.7
                    print(f"     ✓ Pass: {passes}")
        
        # Show local region around pattern
        region_size = 80
        x1 = max(0, cx - region_size // 2)
        y1 = max(0, cy - region_size // 2)
        x2 = min(binary_image.shape[1], cx + region_size // 2)
        y2 = min(binary_image.shape[0], cy + region_size // 2)
        
        local_region = vis_image[y1:y2, x1:x2]
        
        # Save visualization
        output_dir = "results/concentric-validation-test"
        os.makedirs(output_dir, exist_ok=True)
        
        pattern_filename = f"pattern_{pattern['pattern_id']}_{method}_concentric_analysis.png"
        pattern_path = os.path.join(output_dir, pattern_filename)
        cv2.imwrite(pattern_path, local_region)
        
        print(f"   💾 Visualization saved: {pattern_path}")

def test_concentric_validation_strictness():
    """
    Test if concentric validation is too strict by analyzing detection patterns
    """
    print("\n🎯 CONCENTRIC VALIDATION STRICTNESS TEST")
    print("=" * 60)
    
    # Load analysis results
    results_dir = "results/pattern-grids"
    json_files = [f for f in os.listdir(results_dir) if f.endswith('_detailed_analysis.json')]
    
    total_patterns = 0
    total_concentric_passed = 0
    rejection_reasons = {}
    
    for json_file in json_files[:3]:  # Test first 3 images
        json_path = os.path.join(results_dir, json_file)
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        image_name = data['image_name']
        image_path = os.path.join("data-qr-ratio-finder", image_name)
        
        print(f"\n📋 Analyzing: {image_name}")
        
        # Visualize concentric analysis
        visualize_concentric_analysis(image_path, data)
        
        # Collect statistics
        for pattern in data['patterns']:
            total_patterns += 1
            concentric_score = pattern['concentric_details']['score']
            
            if concentric_score > 0:
                total_concentric_passed += 1
            else:
                reason = pattern['concentric_details']['reason']
                if reason not in rejection_reasons:
                    rejection_reasons[reason] = 0
                rejection_reasons[reason] += 1
    
    print(f"\n📊 CONCENTRIC VALIDATION STATISTICS")
    print("=" * 40)
    print(f"Total patterns analyzed: {total_patterns}")
    print(f"Patterns passing concentric validation: {total_concentric_passed}")
    print(f"Pass rate: {total_concentric_passed / total_patterns * 100:.1f}%")
    
    print(f"\n🚫 Rejection Reasons:")
    for reason, count in sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True):
        percentage = count / total_patterns * 100
        print(f"   {reason}: {count} patterns ({percentage:.1f}%)")
    
    # Analysis and recommendations
    print(f"\n🔬 ANALYSIS:")
    
    if total_concentric_passed == 0:
        print("⚠️  VERY STRICT: No patterns passed concentric validation")
        print("   This suggests the validation might be too strict for the given images")
        print("   Possible issues:")
        print("   1. Images don't contain genuine QR finder patterns")
        print("   2. Binary thresholding is not optimal for concentric analysis")
        print("   3. Ring sampling radii calculations need adjustment")
        print("   4. Thresholds (80% center dark, 30% first ring, 70% second ring) too strict")
    elif total_concentric_passed / total_patterns < 0.1:
        print("⚠️  TOO STRICT: Very low pass rate suggests overly strict validation")
    elif total_concentric_passed / total_patterns < 0.3:
        print("⚖️  MODERATELY STRICT: Reasonable for high precision requirements")
    else:
        print("✅ BALANCED: Good balance between precision and recall")
    
    # Check specific rejection patterns
    if "first ring too dark: 100.0%" in rejection_reasons:
        first_ring_100_count = rejection_reasons["first ring too dark: 100.0%"]
        if first_ring_100_count / total_patterns > 0.8:
            print(f"\n🔍 SPECIFIC ISSUE: {first_ring_100_count} patterns have 100% dark first ring")
            print("   This suggests:")
            print("   1. Pattern centers are being detected in solid black regions")
            print("   2. Ring radius calculation might be too small")
            print("   3. Binary thresholding creates too much black area")
            print("   4. These might not be genuine QR finder patterns")

def suggest_improvements():
    """
    Suggest specific improvements to the concentric validation function
    """
    print(f"\n💡 IMPROVEMENT SUGGESTIONS")
    print("=" * 40)
    
    print("1. 🔧 RADIUS CALCULATION:")
    print("   - Current: first_ring_r = max(3, max_radius // 3)")
    print("   - Suggested: Use pattern size more intelligently")
    print("   - Consider: first_ring_r = max(4, size // 8)")
    print("   - Reason: Better scaling with actual pattern size")
    
    print("\n2. 🎯 THRESHOLD ADJUSTMENT:")
    print("   - Current: center 80%, first ring 30%, second ring 70%")
    print("   - Suggested: More lenient thresholds")
    print("   - Consider: center 70%, first ring 40%, second ring 60%")
    print("   - Reason: Account for image quality and thresholding artifacts")
    
    print("\n3. 📊 SAMPLING IMPROVEMENT:")
    print("   - Current: Dense sampling every 10 degrees")
    print("   - Suggested: Add robustness checks")
    print("   - Consider: Ignore outlier pixels in ring analysis")
    print("   - Reason: Reduce impact of noise and artifacts")
    
    print("\n4. 🔍 MULTI-METHOD VALIDATION:")
    print("   - Current: Single binary image per pattern")
    print("   - Suggested: Test concentric structure on multiple binary versions")
    print("   - Consider: If any binary method passes, accept pattern")
    print("   - Reason: Different thresholding methods may work better for different patterns")
    
    print("\n5. ⚖️ SCORING REFINEMENT:")
    print("   - Current: Binary pass/fail with 0.85 quality threshold")
    print("   - Suggested: Gradual scoring based on deviation from ideal")
    print("   - Consider: Partial scores for near-ideal patterns")
    print("   - Reason: Allow slightly imperfect but valid QR patterns")

if __name__ == "__main__":
    test_concentric_validation_strictness()
    suggest_improvements()
