#!/usr/bin/env python3
"""
Create comprehensive visualization grids for all detected patterns
Shows original image, binary images, and detected patterns with component scores
"""

import cv2
import numpy as np
import os
from enhanced_strict_qr_detector import EnhancedStrictQRDetector
import json

def create_pattern_grid(image_path, output_folder):
    """Create a comprehensive visualization grid for a single image"""
    filename = os.path.basename(image_path)
    base_name = os.path.splitext(filename)[0]
    
    print(f"Creating grid for: {filename}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Failed to load {image_path}")
        return
    
    # Initialize detector
    detector = EnhancedStrictQRDetector(ratio_tolerance=0.22)
    detector.reset_debug()
    
    # Detect patterns
    patterns, gray, binary_results = detector.find_qr_patterns_multi_threshold(image)
    
    # Prepare images for grid
    images_for_grid = []
    titles = []
    
    # Original image
    original_display = image.copy()
    cv2.putText(original_display, f"Original ({len(patterns)} patterns)", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    images_for_grid.append(original_display)
    titles.append("Original")
    
    # Grayscale
    gray_display = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.putText(gray_display, "Grayscale", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    images_for_grid.append(gray_display)
    titles.append("Grayscale")
    
    # Binary images
    binary_methods = ['otsu', 'adaptive_mean', 'adaptive_gaussian']
    for method in binary_methods:
        if method in binary_results:
            binary_img = binary_results[method]
            binary_display = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR)
            cv2.putText(binary_display, method.replace('_', ' ').title(), 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            images_for_grid.append(binary_display)
            titles.append(method)
    
    # Detected patterns image
    result_image = image.copy()
    
    # Draw patterns with detailed info
    for j, pattern in enumerate(patterns):
        cx, cy = pattern['center']
        size = pattern['size']
        score = pattern['score']
        method = pattern['method']
        analysis = pattern['analysis']
        
        # Get component scores
        concentric_score = analysis['concentric']['score']
        line_score = analysis['line_pattern_score']
        symmetry_score = analysis['symmetry']['score']
        
        # Color based on overall score
        if score > 0.8:
            color = (0, 255, 0)  # Green for excellent
        elif score > 0.6:
            color = (0, 200, 200)  # Yellow for good
        else:
            color = (0, 100, 255)  # Orange for acceptable
        
        # Draw pattern circle
        cv2.circle(result_image, (cx, cy), size//2, color, 3)
        cv2.circle(result_image, (cx, cy), 5, color, -1)  # Center dot
        
        # Main label
        label = f"P{j+1}: {score:.2f}"
        cv2.putText(result_image, label, 
                   (cx - 40, cy - size//2 - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Component scores
        comp_label = f"C:{concentric_score:.1f} L:{line_score:.1f} S:{symmetry_score:.1f}"
        cv2.putText(result_image, comp_label, 
                   (cx - 50, cy - size//2 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Method
        method_label = f"({method})"
        cv2.putText(result_image, method_label, 
                   (cx - 30, cy + size//2 + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Rejection reason for concentric
        if concentric_score == 0.0 and 'reason' in analysis['concentric']:
            reason = analysis['concentric']['reason']
            if len(reason) > 25:
                reason = reason[:22] + "..."
            cv2.putText(result_image, reason, 
                       (cx - 60, cy + size//2 + 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
    
    # Add title to result image
    cv2.putText(result_image, f"Detected Patterns: {len(patterns)}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    images_for_grid.append(result_image)
    titles.append("Detected")
    
    # Individual pattern analysis images
    for j, pattern in enumerate(patterns):
        cx, cy = pattern['center']
        size = pattern['size']
        analysis = pattern['analysis']
        
        # Create individual pattern view
        pattern_img = image.copy()
        
        # Extract region around pattern
        margin = max(50, size)
        x1 = max(0, cx - margin)
        y1 = max(0, cy - margin)
        x2 = min(image.shape[1], cx + margin)
        y2 = min(image.shape[0], cy + margin)
        
        # Draw pattern details
        color = (0, 255, 255)  # Yellow for individual view
        cv2.circle(pattern_img, (cx, cy), size//2, color, 2)
        cv2.circle(pattern_img, (cx, cy), 3, color, -1)
        
        # Crop to pattern region
        pattern_region = pattern_img[y1:y2, x1:x2]
        
        # Resize if too small
        if pattern_region.shape[0] < 150 or pattern_region.shape[1] < 150:
            scale = max(150 / pattern_region.shape[0], 150 / pattern_region.shape[1])
            new_w = int(pattern_region.shape[1] * scale)
            new_h = int(pattern_region.shape[0] * scale)
            pattern_region = cv2.resize(pattern_region, (new_w, new_h))
        
        # Add pattern info
        concentric_score = analysis['concentric']['score']
        line_score = analysis['line_pattern_score']
        symmetry_score = analysis['symmetry']['score']
        
        info_text = [
            f"Pattern {j+1}",
            f"Score: {pattern['score']:.3f}",
            f"Concentric: {concentric_score:.3f}",
            f"Line: {line_score:.3f}",
            f"Symmetry: {symmetry_score:.3f}",
            f"Method: {pattern['method']}"
        ]
        
        for i, text in enumerate(info_text):
            cv2.putText(pattern_region, text, 
                       (5, 20 + i*15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        images_for_grid.append(pattern_region)
        titles.append(f"Pattern {j+1}")
    
    # Create grid layout
    # Calculate grid dimensions
    num_images = len(images_for_grid)
    cols = min(4, num_images)  # Max 4 columns
    rows = (num_images + cols - 1) // cols
    
    # Resize all images to same size
    target_size = (400, 300)
    resized_images = []
    for img in images_for_grid:
        resized = cv2.resize(img, target_size)
        resized_images.append(resized)
    
    # Create grid
    grid_height = rows * target_size[1]
    grid_width = cols * target_size[0]
    grid = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)
    
    for i, (img, title) in enumerate(zip(resized_images, titles)):
        row = i // cols
        col = i % cols
        
        y1 = row * target_size[1]
        y2 = y1 + target_size[1]
        x1 = col * target_size[0]
        x2 = x1 + target_size[0]
        
        grid[y1:y2, x1:x2] = img
        
        # Add title
        cv2.putText(grid, title, 
                   (x1 + 5, y1 + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Add overall title
    title_height = 50
    final_grid = np.zeros((grid_height + title_height, grid_width, 3), dtype=np.uint8)
    final_grid[title_height:, :] = grid
    
    # Overall title with summary
    summary = f"{filename} - {len(patterns)} patterns detected"
    cv2.putText(final_grid, summary, 
               (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Component score summary
    if patterns:
        avg_concentric = np.mean([p['analysis']['concentric']['score'] for p in patterns])
        avg_line = np.mean([p['analysis']['line_pattern_score'] for p in patterns])
        avg_symmetry = np.mean([p['analysis']['symmetry']['score'] for p in patterns])
        
        score_summary = f"Avg Scores - C:{avg_concentric:.2f} L:{avg_line:.2f} S:{avg_symmetry:.2f}"
        cv2.putText(final_grid, score_summary, 
                   (grid_width - 400, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    # Save grid
    grid_path = os.path.join(output_folder, f"{base_name}_comprehensive_grid.png")
    cv2.imwrite(grid_path, final_grid)
    
    # Save detailed JSON results
    json_results = {
        'image_name': filename,
        'patterns_found': len(patterns),
        'patterns': []
    }
    
    for i, pattern in enumerate(patterns):
        pattern_info = {
            'pattern_id': i + 1,
            'center': pattern['center'],
            'size': pattern['size'],
            'overall_score': pattern['score'],
            'method': pattern['method'],
            'component_scores': {
                'concentric': pattern['analysis']['concentric']['score'],
                'line_pattern': pattern['analysis']['line_pattern_score'],
                'symmetry': pattern['analysis']['symmetry']['score']
            },
            'concentric_details': pattern['analysis']['concentric'],
            'line_pattern_details': {
                'valid_directions': pattern['analysis']['valid_directions'],
                'line_results': pattern['analysis']['line_results']
            },
            'symmetry_details': pattern['analysis']['symmetry']
        }
        json_results['patterns'].append(pattern_info)
    
    json_path = os.path.join(output_folder, f"{base_name}_detailed_analysis.json")
    with open(json_path, 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    
    print(f"✅ Grid saved: {grid_path}")
    print(f"✅ Analysis saved: {json_path}")
    
    return len(patterns)

def create_all_grids():
    """Create grids for all images in the data folder"""
    input_folder = "data-qr-ratio-finder"
    output_folder = "results/pattern-grids"
    
    # Create output directory
    os.makedirs(output_folder, exist_ok=True)
    
    print("🔍 CREATING COMPREHENSIVE PATTERN GRIDS")
    print("=" * 60)
    
    # Get all image files
    image_files = []
    for ext in ['png', 'jpg', 'jpeg']:
        for file in os.listdir(input_folder):
            if file.lower().endswith(f'.{ext}'):
                image_files.append(file)
    
    print(f"Found {len(image_files)} images to process")
    
    total_patterns = 0
    processed_images = 0
    
    for filename in sorted(image_files):
        image_path = os.path.join(input_folder, filename)
        
        try:
            patterns_found = create_pattern_grid(image_path, output_folder)
            total_patterns += patterns_found
            processed_images += 1
            print(f"  Patterns found: {patterns_found}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")
        
        print()
    
    # Create summary
    print("📊 GRID CREATION SUMMARY")
    print("=" * 40)
    print(f"Images processed: {processed_images}")
    print(f"Total patterns found: {total_patterns}")
    print(f"Average patterns per image: {total_patterns/processed_images:.1f}" if processed_images > 0 else "No images processed")
    print(f"\n📁 Grids saved in: {output_folder}")
    print("✅ Grid creation complete!")

if __name__ == "__main__":
    create_all_grids()
