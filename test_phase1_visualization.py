#!/usr/bin/env python3
"""
Test Phase 1 Visualization
Quick test script to visualize Phase 1 functionality
"""

import os
import sys
from visualize_phase1 import Phase1Visualizer

def test_with_existing_images():
    """Test Phase 1 visualization with any existing images in the workspace"""
    
    # Look for image files in the current directory
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    image_files = []
    
    for file in os.listdir('.'):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(file)
    
    if not image_files:
        print("📷 No image files found in current directory")
        print("🎨 Running test with mock data instead...")
        
        # Import and run the test function
        from visualize_phase1 import test_phase1_visualization
        test_phase1_visualization()
        return
    
    print(f"📷 Found {len(image_files)} image files:")
    for i, img in enumerate(image_files[:5]):  # Show first 5
        print(f"   {i+1}. {img}")
    
    if len(image_files) > 5:
        print(f"   ... and {len(image_files)-5} more")
    
    # Use the first image for visualization
    test_image = image_files[0]
    print(f"\n🎯 Creating Phase 1 visualization for: {test_image}")
    
    # Create visualizer and process the image
    visualizer = Phase1Visualizer()
    visualizer.create_phase1_summary(test_image)

def show_phase1_capabilities():
    """Display what Phase 1 visualization shows"""
    print("🎨 PHASE 1 VISUALIZATION CAPABILITIES")
    print("=" * 50)
    print()
    print("📋 What Phase 1 Does:")
    print("   🎯 Fourth Corner Detection - Calculate missing corner from 3 finder patterns")
    print("   🔄 Perspective Correction - Transform skewed pattern to rectangular view")
    print("   📊 Flexible Ratios - Support rectangular patterns (not just square)")
    print("   🔧 Geometric Validation - Proper corner ordering and dimensions")
    print()
    print("📁 Visualization Outputs:")
    print("   📍 fourth_corner.png - Shows 4th corner calculation process")
    print("   🔄 perspective_correction.png - Before/after perspective transformation")
    print("   📊 ratio_comparison.png - Different aspect ratios side by side")
    print("   📄 phase1_report.html - Interactive HTML report with all visualizations")
    print()
    print("🚀 Key Features:")
    print("   ✅ Works with any aspect ratio (1:1, 3:2, 2:3, 2:1, etc.)")
    print("   ✅ Clear geometric annotation and labeling")
    print("   ✅ Step-by-step process visualization")
    print("   ✅ Professional HTML report generation")
    print("   ✅ Handles perspective distortion and skew")
    print()

if __name__ == "__main__":
    show_phase1_capabilities()
    print()
    
    if len(sys.argv) > 1:
        # Specific image provided
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            print(f"🎯 Processing specified image: {image_path}")
            visualizer = Phase1Visualizer()
            visualizer.create_phase1_summary(image_path)
        else:
            print(f"❌ Image not found: {image_path}")
    else:
        # Auto-detect images or run test
        test_with_existing_images()
