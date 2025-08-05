#!/usr/bin/env python3
"""
Concentric Pattern Inspector
Specifically examines the concentric ring analysis for a pattern location
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

def analyze_concentric_pattern(image_name, pattern_center, pattern_size, method="adaptive_gaussian"):
    """Analyze the concentric ring structure at a specific location"""
    
    # Load the specific binary image used for detection
    binary_file = Path("results/enhanced-strict-qr-results") / f"binary_{method}_{image_name}.png"
    
    if not binary_file.exists():
        print(f"❌ Binary image not found: {binary_file}")
        return
    
    binary_img = cv2.imread(str(binary_file), cv2.IMREAD_GRAYSCALE)
    if binary_img is None:
        print(f"❌ Could not load image: {binary_file}")
        return
    
    x, y = pattern_center
    
    print(f"🔍 CONCENTRIC ANALYSIS AT ({x}, {y})")
    print(f"Method: {method}")
    print(f"Expected Size: {pattern_size}px")
    print("=" * 60)
    
    # Load the JSON results to see what the algorithm found
    results_file = Path("results/enhanced-strict-qr-results") / f"{image_name}_results.json"
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    # Find the specific pattern
    target_pattern = None
    for pattern in data['patterns']:
        if pattern['center']['x'] == x and pattern['center']['y'] == y:
            target_pattern = pattern
            break
    
    if not target_pattern:
        print(f"❌ Pattern not found in results")
        return
    
    # Show what the algorithm claimed to find
    concentric_analysis = target_pattern['analysis']['concentric']
    print(f"📊 ALGORITHM'S CONCENTRIC ANALYSIS:")
    print(f"   Score: {concentric_analysis['score']}")
    print(f"   Center Dark: {concentric_analysis['center_dark']}")
    print(f"   Ring Count: {concentric_analysis['ring_count']}")
    print("\n   Claimed Ring Pattern:")
    for i, ring in enumerate(concentric_analysis['rings']):
        radius = ring['radius']
        ring_type = ring['type']
        dark_count = ring['dark_count']
        light_count = ring['light_count']
        total = ring['total_pixels']
        print(f"     Ring {i+1} (r={radius}): {ring_type} - {dark_count}D/{light_count}L (total: {total})")
    
    # Now let's manually verify this
    print(f"\n🔬 MANUAL VERIFICATION:")
    
    # Define the radii to check (same as algorithm)
    radii = [3, 6, 9, 12, 15, 18]
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Show the region
    size = max(40, pattern_size)  # Use at least 40px for good visualization
    x_start = max(0, x - size//2)
    x_end = min(binary_img.shape[1], x + size//2)
    y_start = max(0, y - size//2)
    y_end = min(binary_img.shape[0], y + size//2)
    
    region = binary_img[y_start:y_end, x_start:x_end]
    
    ax1.imshow(region, cmap='gray')
    ax1.set_title(f"Binary Region ({method})", fontsize=14, fontweight='bold')
    
    # Draw the concentric circles
    center_in_region = (x - x_start, y - y_start)
    
    for radius in radii:
        circle = plt.Circle(center_in_region, radius, fill=False, color='red', linewidth=2, alpha=0.7)
        ax1.add_patch(circle)
        ax1.text(center_in_region[0] + radius, center_in_region[1], f'r={radius}', 
                color='red', fontsize=10, fontweight='bold')
    
    ax1.plot(center_in_region[0], center_in_region[1], 'ro', markersize=8, markeredgecolor='white', markeredgewidth=2)
    ax1.axis('off')
    
    # Manual analysis of each ring
    print(f"   Manual Ring Analysis:")
    manual_rings = []
    
    for radius in radii:
        # Create a mask for this ring
        Y, X = np.ogrid[:region.shape[0], :region.shape[1]]
        center_y, center_x = center_in_region[1], center_in_region[0]
        
        # Get points at this radius (approximately)
        distance_map = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        ring_mask = (distance_map >= radius - 1) & (distance_map <= radius + 1)
        
        if np.sum(ring_mask) > 0:
            ring_pixels = region[ring_mask]
            dark_count = np.sum(ring_pixels < 128)
            light_count = np.sum(ring_pixels >= 128)
            total_pixels = len(ring_pixels)
            
            if total_pixels > 0:
                dark_ratio = dark_count / total_pixels
                if dark_ratio > 0.6:
                    ring_type = "dark"
                elif dark_ratio < 0.4:
                    ring_type = "light"
                else:
                    ring_type = "mixed"
                
                manual_rings.append({
                    'radius': radius,
                    'type': ring_type,
                    'dark_count': dark_count,
                    'light_count': light_count,
                    'total_pixels': total_pixels,
                    'dark_ratio': dark_ratio
                })
                
                print(f"     Ring r={radius}: {ring_type} - {dark_count}D/{light_count}L ({dark_ratio:.1%} dark)")
            else:
                print(f"     Ring r={radius}: No pixels found")
        else:
            print(f"     Ring r={radius}: Outside region bounds")
    
    # Compare algorithm vs manual results
    ax2.bar(range(len(manual_rings)), [r['dark_ratio'] for r in manual_rings], 
            color=['black' if r['dark_ratio'] > 0.6 else 'lightgray' if r['dark_ratio'] < 0.4 else 'gray' for r in manual_rings])
    ax2.set_xlabel('Ring Number')
    ax2.set_ylabel('Dark Pixel Ratio')
    ax2.set_title('Ring Analysis: Dark Pixel Ratios')
    ax2.set_xticks(range(len(manual_rings)))
    ax2.set_xticklabels([f"r={r['radius']}" for r in manual_rings])
    ax2.axhline(y=0.6, color='red', linestyle='--', alpha=0.7, label='Dark threshold')
    ax2.axhline(y=0.4, color='blue', linestyle='--', alpha=0.7, label='Light threshold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save the analysis
    output_path = Path("results") / "concentric-inspection" / f"{image_name.replace(' ', '_')}_concentric_analysis.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n💾 Analysis saved: {output_path}")
    
    # Final assessment
    print(f"\n🏆 CONCENTRIC ASSESSMENT:")
    
    # Check for proper QR pattern: dark center, light ring, dark ring
    if len(manual_rings) >= 3:
        center_dark = manual_rings[0]['dark_ratio'] > 0.6
        first_ring_light = manual_rings[1]['dark_ratio'] < 0.4  
        second_ring_dark = manual_rings[2]['dark_ratio'] > 0.6
        
        print(f"   Center dark: {'✅' if center_dark else '❌'} ({manual_rings[0]['dark_ratio']:.1%})")
        print(f"   First ring light: {'✅' if first_ring_light else '❌'} ({manual_rings[1]['dark_ratio']:.1%})")
        print(f"   Second ring dark: {'✅' if second_ring_dark else '❌'} ({manual_rings[2]['dark_ratio']:.1%})")
        
        qr_pattern = center_dark and first_ring_light and second_ring_dark
        print(f"   QR Pattern Valid: {'✅' if qr_pattern else '❌'}")
        
        # Compare to algorithm's assessment
        algorithm_score = concentric_analysis['score']
        print(f"   Algorithm Score: {algorithm_score} ({'✅ PASS' if algorithm_score >= 0.5 else '❌ FAIL'})")
        
        if qr_pattern and algorithm_score >= 0.5:
            print(f"   ✅ Both manual and algorithm agree: VALID concentric pattern")
        elif not qr_pattern and algorithm_score < 0.5:
            print(f"   ✅ Both manual and algorithm agree: INVALID concentric pattern")
        else:
            print(f"   ⚠️  DISAGREEMENT between manual analysis and algorithm!")
    else:
        print(f"   ❌ Insufficient rings for analysis")

def main():
    # Analyze the 4th pattern's concentric structure
    analyze_concentric_pattern("image copy 9", (470, 415), 53, "adaptive_gaussian")

if __name__ == "__main__":
    main()
