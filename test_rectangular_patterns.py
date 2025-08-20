#!/usr/bin/env python3
"""
Test Rectangular Pattern Detection
Demonstrates flexible ratio support for different pattern shapes
"""

import cv2
import numpy as np
from enhanced_strict_qr_detector import EnhancedStrictQRDetector
import os

def test_rectangular_patterns():
    """Test the detector with different aspect ratios"""
    print("🔬 TESTING RECTANGULAR PATTERN DETECTION")
    print("=" * 60)
    
    # Test different ratios
    test_configurations = [
        {
            'ratio': 1.0,
            'name': 'Square (Standard QR)',
            'output_width': 300,
            'description': 'Traditional 1:1 square QR patterns'
        },
        {
            'ratio': 1.5,
            'name': 'Wide Rectangle (3:2)',
            'output_width': 450,
            'description': 'Landscape orientation, 50% wider than tall'
        },
        {
            'ratio': 0.67,
            'name': 'Tall Rectangle (2:3)',
            'output_width': 300,
            'description': 'Portrait orientation, 50% taller than wide'
        },
        {
            'ratio': 2.0,
            'name': 'Very Wide (2:1)',
            'output_width': 600,
            'description': 'Double-wide rectangular pattern'
        }
    ]
    
    # Test with an existing image
    test_image_path = "data-qr-ratio-finder/image copy.png"
    
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        print("🔍 Searching for available test images...")
        
        # Search for any available images
        data_folder = "data-qr-ratio-finder"
        if os.path.exists(data_folder):
            images = [f for f in os.listdir(data_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if images:
                test_image_path = os.path.join(data_folder, images[0])
                print(f"✅ Using: {test_image_path}")
            else:
                print("❌ No images found in data-qr-ratio-finder folder")
                return
        else:
            print("❌ data-qr-ratio-finder folder not found")
            return
    
    # Load test image
    image = cv2.imread(test_image_path)
    if image is None:
        print(f"❌ Could not load image: {test_image_path}")
        return
    
    print(f"📷 Testing with image: {test_image_path}")
    print(f"📐 Original image size: {image.shape[1]}x{image.shape[0]}")
    
    # Test each configuration
    for i, config in enumerate(test_configurations, 1):
        print(f"\n{'='*20} TEST {i}/4 {'='*20}")
        print(f"📊 {config['name']} (Ratio: {config['ratio']:.2f})")
        print(f"📝 {config['description']}")
        
        # Create detector with specific ratio
        detector = EnhancedStrictQRDetector(width_height_ratio=config['ratio'])
        
        # Detect patterns
        patterns, _, _ = detector.find_qr_patterns_multi_threshold(image)
        
        print(f"🔍 Detected {len(patterns)} finder patterns")
        
        if len(patterns) >= 3:
            # Calculate output height
            output_height = int(config['output_width'] / config['ratio'])
            
            print(f"📏 Output dimensions: {config['output_width']}x{output_height}")
            
            # Extract pattern data
            result = detector.extract_qr_data_if_possible(
                image, patterns[:3], 
                output_width=config['output_width']
            )
            
            if result and 'corrected_image' in result:
                # Save corrected image
                output_filename = f"rectangular_test_{config['ratio']:.2f}_ratio.png"
                output_path = os.path.join("results/enhanced-strict-qr-results", output_filename)
                
                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                cv2.imwrite(output_path, result['corrected_image'])
                
                print(f"💾 Saved corrected pattern: {output_filename}")
                print(f"📊 Pattern info: {result['expected_modules']} modules")
                print(f"🎯 Fourth corner: {result['fourth_corner']}")
            else:
                print("❌ Pattern extraction failed")
        else:
            print("⚠️  Not enough patterns for rectangular extraction")
    
    print(f"\n{'='*60}")
    print("✅ Rectangular pattern testing complete!")
    print("📁 Check results/enhanced-strict-qr-results/ for corrected images")

def demonstrate_ratio_flexibility():
    """Demonstrate the flexibility of the ratio system"""
    print("\n🎨 RATIO FLEXIBILITY DEMONSTRATION")
    print("=" * 50)
    
    print("📐 Supported Pattern Types:")
    print("   • 1.0   - Square (traditional QR codes)")
    print("   • 1.5   - Wide rectangle (3:2 aspect ratio)")
    print("   • 0.67  - Tall rectangle (2:3 aspect ratio)")
    print("   • 2.0   - Very wide (2:1 aspect ratio)")
    print("   • 0.5   - Very tall (1:2 aspect ratio)")
    print("   • 1.33  - Video format (4:3 aspect ratio)")
    print("   • 1.78  - Widescreen (16:9 aspect ratio)")
    
    print("\n🔧 Usage Examples:")
    print("   detector = EnhancedStrictQRDetector(width_height_ratio=1.5)")
    print("   result = detector.extract_qr_data_if_possible(image, patterns, output_width=450)")
    print("   # Creates 450x300 corrected image (3:2 ratio)")
    
    print("\n💡 Benefits:")
    print("   ✅ Handles non-square patterns accurately")
    print("   ✅ Maintains proper perspective correction")
    print("   ✅ Adapts module counting for rectangular grids")
    print("   ✅ Preserves pattern geometry relationships")

if __name__ == "__main__":
    test_rectangular_patterns()
    demonstrate_ratio_flexibility()
