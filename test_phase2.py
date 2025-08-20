#!/usr/bin/env python3
"""
Test Phase 2: Grid Detection & Module Reading
Demonstrates the new module sampling and binary data extraction capabilities
"""

import cv2
import numpy as np
import os
import json
from enhanced_strict_qr_detector import EnhancedStrictQRDetector

def test_phase2_grid_detection():
    """Test Phase 2 grid sampling and module reading"""
    print("🔬 TESTING PHASE 2: GRID DETECTION & MODULE READING")
    print("=" * 70)
    
    # Test image
    test_image_path = "data-qr-ratio-finder/image copy.png"
    
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return
    
    # Load test image
    image = cv2.imread(test_image_path)
    if image is None:
        print(f"❌ Could not load image: {test_image_path}")
        return
    
    print(f"📷 Testing with: {test_image_path}")
    print(f"📐 Image size: {image.shape[1]}x{image.shape[0]}")
    
    # Create detector (square QR for initial test)
    detector = EnhancedStrictQRDetector(width_height_ratio=1.0)
    
    # Detect patterns
    patterns, _, _ = detector.find_qr_patterns_multi_threshold(image)
    print(f"🔍 Detected {len(patterns)} finder patterns")
    
    if len(patterns) >= 3:
        print("\n" + "="*30 + " PHASE 1 " + "="*30)
        
        # Test Phase 1 only
        result_phase1 = detector.extract_qr_data_if_possible(
            image, patterns[:3], 
            output_width=300,
            enable_phase2=False
        )
        
        if result_phase1:
            print("✅ Phase 1 completed successfully")
        
        print("\n" + "="*30 + " PHASE 2 " + "="*30)
        
        # Test Phase 1 + 2
        result_phase2 = detector.extract_qr_data_if_possible(
            image, patterns[:3], 
            output_width=300,
            enable_phase2=True
        )
        
        if result_phase2 and result_phase2.get('phase2_enabled'):
            print("\n📊 DETAILED PHASE 2 ANALYSIS")
            print("-" * 40)
            
            # Grid information
            grid_shape = result_phase2['grid_shape']
            module_grid = np.array(result_phase2['module_grid'])
            
            print(f"📏 Module Grid: {grid_shape[1]}x{grid_shape[0]} modules")
            print(f"🎯 Total Modules: {module_grid.size}")
            print(f"⚫ Black Modules: {np.sum(module_grid == 1)}")
            print(f"⚪ White Modules: {np.sum(module_grid == 0)}")
            
            # Finder pattern analysis
            finder_analysis = result_phase2['finder_patterns_analysis']
            print(f"\n🔍 Finder Pattern Validation:")
            for corner in ['top_left', 'top_right', 'bottom_left']:
                pattern_info = finder_analysis[f'{corner}_pattern']
                if pattern_info:
                    status = "✅ Detected" if pattern_info['detected'] else "❌ Failed"
                    pos = pattern_info['position']
                    print(f"   {corner.replace('_', ' ').title()}: {status} at {pos}")
            
            # Data modules analysis
            data_analysis = result_phase2['data_modules_analysis']
            print(f"\n📈 Data Module Analysis:")
            print(f"   Total Data Modules: {data_analysis['total_data_modules']}")
            print(f"   Black Data Modules: {data_analysis['black_modules']}")
            print(f"   White Data Modules: {data_analysis['white_modules']}")
            print(f"   Data Density: {data_analysis['data_density']:.2f}")
            print(f"   Function Modules Excluded: {data_analysis['excluded_regions']['total_function_modules']}")
            
            # Save detailed results
            save_phase2_analysis(result_phase2, "phase2_test_results.json")
            
            # Create visualization
            create_grid_visualization(module_grid, "phase2_grid_visualization.png")
            
        else:
            print("❌ Phase 2 failed")
    
    else:
        print("⚠️  Not enough patterns for Phase 2 testing")

def test_rectangular_phase2():
    """Test Phase 2 with rectangular patterns"""
    print(f"\n🔲 TESTING PHASE 2 WITH RECTANGULAR PATTERNS")
    print("=" * 60)
    
    test_image_path = "data-qr-ratio-finder/image copy.png"
    
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found")
        return
    
    image = cv2.imread(test_image_path)
    if image is None:
        return
    
    # Test different ratios with Phase 2
    test_ratios = [
        (1.0, "Square", 300, 300),
        (1.5, "Wide Rectangle", 450, 300),
        (0.67, "Tall Rectangle", 300, 447)
    ]
    
    for ratio, name, width, height in test_ratios:
        print(f"\n📐 Testing {name} (ratio: {ratio:.2f})")
        print("-" * 30)
        
        detector = EnhancedStrictQRDetector(width_height_ratio=ratio)
        patterns, _, _ = detector.find_qr_patterns_multi_threshold(image)
        
        if len(patterns) >= 3:
            result = detector.extract_qr_data_if_possible(
                image, patterns[:3],
                output_width=width,
                enable_phase2=True
            )
            
            if result and result.get('phase2_enabled'):
                grid_shape = result['grid_shape']
                data_analysis = result['data_modules_analysis']
                
                print(f"   ✅ Grid: {grid_shape[1]}x{grid_shape[0]}")
                print(f"   📊 Data Modules: {data_analysis['total_data_modules']}")
                print(f"   🎯 Density: {data_analysis['data_density']:.2f}")
            else:
                print(f"   ❌ Failed")

def save_phase2_analysis(result: dict, filename: str):
    """Save Phase 2 analysis to JSON file"""
    
    # Create a simplified version for JSON serialization
    analysis_data = {
        'phase': 'Phase 1 + 2',
        'timestamp': str(np.datetime64('now')),
        'pattern_info': {
            'version': result['version'],
            'expected_modules': result['expected_modules'],
            'output_dimensions': result['output_dimensions'],
            'width_height_ratio': result['width_height_ratio']
        },
        'grid_analysis': {
            'grid_shape': result['grid_shape'],
            'total_modules': int(np.array(result['module_grid']).size),
            'black_modules': int(np.sum(np.array(result['module_grid']) == 1)),
            'white_modules': int(np.sum(np.array(result['module_grid']) == 0))
        },
        'finder_patterns': result['finder_patterns_analysis'],
        'data_modules': result['data_modules_analysis'],
        'debug_info': result['debug_info']
    }
    
    output_path = os.path.join("results/enhanced-strict-qr-results", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    print(f"💾 Saved analysis: {filename}")

def create_grid_visualization(module_grid: np.ndarray, filename: str):
    """Create a visualization of the module grid"""
    
    # Scale up the grid for visibility
    scale_factor = 20
    height, width = module_grid.shape
    
    # Create scaled image
    vis_image = np.zeros((height * scale_factor, width * scale_factor), dtype=np.uint8)
    
    for row in range(height):
        for col in range(width):
            # Black modules = 0 (black), White modules = 255 (white)
            color = 0 if module_grid[row, col] == 1 else 255
            
            y1 = row * scale_factor
            y2 = (row + 1) * scale_factor
            x1 = col * scale_factor
            x2 = (col + 1) * scale_factor
            
            vis_image[y1:y2, x1:x2] = color
    
    # Add grid lines for clarity
    for i in range(1, height):
        y = i * scale_factor
        vis_image[y:y+1, :] = 128  # Gray lines
    
    for i in range(1, width):
        x = i * scale_factor
        vis_image[:, x:x+1] = 128  # Gray lines
    
    output_path = os.path.join("results/enhanced-strict-qr-results", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    cv2.imwrite(output_path, vis_image)
    print(f"🎨 Saved visualization: {filename}")

def demonstrate_phase2_features():
    """Demonstrate Phase 2 capabilities"""
    print(f"\n✨ PHASE 2 FEATURES DEMONSTRATION")
    print("=" * 50)
    
    features = [
        "🔬 Adaptive module sampling with Gaussian thresholding",
        "📊 Binary grid extraction (0s and 1s)",
        "🎯 Finder pattern validation in sampled grid",
        "📈 Data module analysis (excluding function patterns)",
        "🚫 Automatic exclusion of timing patterns",
        "📏 Support for rectangular grids with custom ratios",
        "💾 Detailed analysis output with statistics",
        "🎨 Grid visualization generation"
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    print(f"\n🔧 Usage:")
    print(f"   result = detector.extract_qr_data_if_possible(")
    print(f"       image, patterns, enable_phase2=True")
    print(f"   )")
    print(f"   grid = np.array(result['module_grid'])")
    print(f"   data_modules = result['data_modules_analysis']")

if __name__ == "__main__":
    test_phase2_grid_detection()
    test_rectangular_phase2()
    demonstrate_phase2_features()
