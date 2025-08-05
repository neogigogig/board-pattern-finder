#!/usr/bin/env python3
"""
Binary Image Pattern Inspector
Examines what's actually visible at specific coordinates in binary images
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def inspect_pattern_location(image_name, pattern_center, pattern_size):
    """Inspect what's at the pattern location in all binary images"""
    
    results_dir = Path("results/enhanced-strict-qr-results")
    
    # Find all binary images for this image
    binary_files = list(results_dir.glob(f"binary_*{image_name}*"))
    
    print(f"🔍 INSPECTING PATTERN AT ({pattern_center[0]}, {pattern_center[1]})")
    print(f"Expected Size: {pattern_size}px")
    print("=" * 70)
    
    # Create a grid to show all binary images
    num_images = len(binary_files)
    if num_images == 0:
        print("❌ No binary images found!")
        return
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    for i, binary_file in enumerate(sorted(binary_files)):
        if i >= 6:  # Limit to 6 images
            break
            
        # Load binary image
        binary_img = cv2.imread(str(binary_file), cv2.IMREAD_GRAYSCALE)
        if binary_img is None:
            continue
            
        ax = axes[i]
        ax.imshow(binary_img, cmap='gray')
        
        # Extract method name from filename
        method_name = binary_file.name.replace(f"binary_", "").replace(f"_{image_name}.png", "")
        ax.set_title(f"{method_name}", fontsize=12, fontweight='bold')
        
        # Draw the pattern location
        x, y = pattern_center
        size = pattern_size
        
        # Draw bounding box
        rect = plt.Rectangle((x - size//2, y - size//2), size, size, 
                           linewidth=3, edgecolor='red', facecolor='none')
        ax.add_patch(rect)
        
        # Draw center point
        ax.plot(x, y, 'ro', markersize=8, markeredgecolor='white', markeredgewidth=2)
        
        # Add coordinate label
        ax.text(x, y - size//2 - 10, f"({x},{y})", color='red', 
               fontsize=10, fontweight='bold', ha='center', va='bottom',
               bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        ax.axis('off')
        
        # Analyze the pixel region
        x_start = max(0, x - size//2)
        x_end = min(binary_img.shape[1], x + size//2)
        y_start = max(0, y - size//2)
        y_end = min(binary_img.shape[0], y + size//2)
        
        region = binary_img[y_start:y_end, x_start:x_end]
        
        if region.size > 0:
            dark_pixels = np.sum(region < 128)
            light_pixels = np.sum(region >= 128)
            total_pixels = region.size
            dark_ratio = dark_pixels / total_pixels
            
            print(f"\n📊 {method_name.upper()}")
            print(f"   Region: {region.shape[1]}×{region.shape[0]} pixels")
            print(f"   Dark pixels: {dark_pixels}/{total_pixels} ({dark_ratio:.1%})")
            print(f"   Light pixels: {light_pixels}/{total_pixels} ({(1-dark_ratio):.1%})")
            
            # Check for pattern structure
            if region.shape[0] > 10 and region.shape[1] > 10:
                # Sample horizontal line through center
                mid_row = region.shape[0] // 2
                horizontal_line = region[mid_row, :]
                
                # Find runs of dark/light pixels
                runs = []
                current_value = horizontal_line[0] < 128
                current_count = 1
                
                for pixel in horizontal_line[1:]:
                    pixel_dark = pixel < 128
                    if pixel_dark == current_value:
                        current_count += 1
                    else:
                        runs.append((0 if current_value else 1, current_count))
                        current_value = pixel_dark
                        current_count = 1
                
                runs.append((0 if current_value else 1, current_count))
                
                print(f"   Horizontal pattern: {runs}")
                
                # Check if it resembles 1:1:3:1:1 pattern
                if len(runs) >= 5:
                    total_length = sum(count for _, count in runs)
                    ratios = [count/total_length for _, count in runs]
                    print(f"   Ratios: {[f'{r:.3f}' for r in ratios[:5]]}")
                    
                    # Compare to ideal 1:1:3:1:1
                    ideal = [0.125, 0.125, 0.375, 0.125, 0.125]
                    if len(ratios) >= 5:
                        deviations = [abs(ratios[i] - ideal[i]) for i in range(5)]
                        avg_deviation = sum(deviations) / 5
                        print(f"   Avg deviation from 1:1:3:1:1: {avg_deviation:.3f}")
                        
                        if avg_deviation < 0.1:
                            print(f"   ✅ GOOD pattern match!")
                        elif avg_deviation < 0.2:
                            print(f"   ⚠️  Moderate pattern match")
                        else:
                            print(f"   ❌ Poor pattern match")
                else:
                    print(f"   ❌ Insufficient runs for pattern analysis")
            else:
                print(f"   ❌ Region too small for analysis")
    
    # Hide unused subplots
    for i in range(len(binary_files), 6):
        axes[i].axis('off')
    
    plt.suptitle(f"{image_name} - Pattern Location Analysis", fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    # Save the analysis
    output_path = Path("results") / "pattern-inspection" / f"{image_name.replace(' ', '_')}_pattern_inspection.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n💾 Analysis saved: {output_path}")
    
    return output_path

def main():
    # Inspect the 4th pattern location in image copy 9
    inspect_pattern_location("image copy 9", (470, 415), 53)

if __name__ == "__main__":
    main()
