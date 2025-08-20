#!/usr/bin/env python3
"""
Combined Visualization System
Process images through both Phase 1 and Grid analysis
"""

import os
import sys
from visualize_phase1 import Phase1Visualizer
from grid_system_visualizer import GridSystemVisualizer

def create_combined_visualization(image_path: str):
    """Create both Phase 1 and Grid visualizations for an image"""
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False
    
    base_name = os.path.basename(image_path)
    print(f"🎯 Combined Processing: {base_name}")
    print("=" * 50)
    
    try:
        # Phase 1 Visualization
        print("📍 Running Phase 1 Visualization...")
        phase1_viz = Phase1Visualizer()
        phase1_viz.create_phase1_summary(image_path)
        print("   ✅ Phase 1 complete!")
        
        # Grid Visualization
        print("🔢 Running Grid Visualization...")
        grid_viz = GridSystemVisualizer()
        result = grid_viz.create_comprehensive_grid_visualization(image_path)
        if result is not None:
            print("   ✅ Grid analysis complete!")
        else:
            print("   ⚠️ Grid analysis had issues")
        
        print(f"\n✅ Combined visualization complete for: {base_name}")
        print("📁 Results available in:")
        print("   📍 Phase 1: results/phase1_visualization/")
        print("   🔢 Grid: results/grid_visualization/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during combined processing: {e}")
        return False

def process_batch():
    """Process all our favorite real photos through both systems"""
    
    real_photos = [
        "data-qr-ratio-finder/image copy.png",
        "data-qr-ratio-finder/image copy 2.png",
        "data-qr-ratio-finder/image copy 8.png", 
        "data-qr-ratio-finder/image copy 9.png",
        "data-qr-ratio-finder/WhatsApp Image 2025-08-04 at 2.06.06 PM.jpeg"
    ]
    
    print("🎯 Combined Visualization System")
    print("=" * 40)
    print("📊 Processing batch of real QR photos through:")
    print("   📍 Phase 1: Geometric correction (4th corner + perspective)")
    print("   🔢 Grid: Module-level analysis (grid overlay + patterns)")
    print()
    
    successful = 0
    failed = 0
    
    for image_path in real_photos:
        print(f"\n{'='*60}")
        if create_combined_visualization(image_path):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print("📊 BATCH PROCESSING SUMMARY")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Total output files: Phase 1 + Grid visualizations")
    
    # Show gallery links
    print("\n🌐 VIEW RESULTS:")
    print("   📍 Phase 1 Gallery: results/phase1_visualization/real_photos_gallery.html")
    print("   🔢 Grid Gallery: results/grid_visualization/grid_gallery.html")
    
    return successful, failed

def show_combined_summary():
    """Show what the combined system provides"""
    print("🎯 COMBINED VISUALIZATION SYSTEM")
    print("=" * 50)
    print()
    print("📋 WHAT YOU GET:")
    print("   📍 Phase 1 (Geometric Correction):")
    print("      • Fourth corner detection from 3 finder patterns")
    print("      • Perspective correction with flexible ratios")
    print("      • Before/after transformation comparison")
    print("      • Multiple aspect ratio outputs")
    print()
    print("   🔢 Grid System (Module Analysis):")
    print("      • Module boundary detection and overlay")
    print("      • Binary grid extraction (black/white modules)")
    print("      • Finder pattern location highlighting")
    print("      • Statistical analysis and density patterns")
    print()
    print("🎨 VISUALIZATION OUTPUTS:")
    print("   📍 Phase 1: 4 files per image (3 PNG + 1 HTML)")
    print("   🔢 Grid: 4 files per image (3 PNG + 1 HTML)")
    print("   📄 Galleries: Comprehensive HTML viewers")
    print()
    print("🚀 USAGE:")
    print("   # Process single image:")
    print("   python3 combined_visualizer.py path/to/image.png")
    print()
    print("   # Process all real photos:")
    print("   python3 combined_visualizer.py")
    print()

def main():
    if len(sys.argv) > 1:
        # Process specific image
        image_path = sys.argv[1]
        create_combined_visualization(image_path)
    else:
        # Show summary and process batch
        show_combined_summary()
        
        response = input("🤔 Process all real photos? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            process_batch()
        else:
            print("👋 Use 'python3 combined_visualizer.py image_path' for single images")

if __name__ == "__main__":
    main()
