#!/usr/bin/env python3
"""
Quick Phase 1 Visualizer
Simple command-line tool to visualize Phase 1 for any image
"""

import sys
import os
from visualize_phase1 import Phase1Visualizer

def main():
    print("🎯 Quick Phase 1 Visualizer")
    print("=" * 30)
    
    # Check for image argument
    if len(sys.argv) < 2:
        print("Usage: python3 quick_phase1.py <image_path>")
        print()
        print("Example:")
        print("  python3 quick_phase1.py test_pattern_highlighting.png")
        print()
        
        # Look for any images in current directory
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
        images = [f for f in os.listdir('.') if any(f.lower().endswith(ext) for ext in image_extensions)]
        
        if images:
            print(f"📷 Found {len(images)} image(s) in current directory:")
            for i, img in enumerate(images[:5]):
                print(f"  {i+1}. {img}")
            
            if len(images) > 5:
                print(f"  ... and {len(images)-5} more")
            
            # Offer to process the first one
            if len(images) > 0:
                response = input(f"\n🤔 Process '{images[0]}'? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    image_path = images[0]
                else:
                    return
            else:
                return
        else:
            print("❌ No image files found in current directory")
            return
    else:
        image_path = sys.argv[1]
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"\n🎨 Processing: {image_path}")
    print("📊 Creating Phase 1 visualization...")
    
    # Create visualizer and process
    visualizer = Phase1Visualizer()
    try:
        visualizer.create_phase1_summary(image_path)
        
        # Show what was created
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        viz_dir = "results/phase1_visualization"
        
        print("\n✅ Visualization complete!")
        print(f"📁 Results saved to: {viz_dir}/")
        print()
        print("📄 Generated files:")
        
        files = [
            (f"{base_name}_fourth_corner.png", "🎯 Fourth corner detection process"),
            (f"{base_name}_perspective_correction.png", "🔄 Before/after perspective correction"),
            (f"{base_name}_ratio_comparison.png", "📊 Multiple aspect ratio comparison"),
            (f"{base_name}_phase1_report.html", "📄 Complete interactive HTML report")
        ]
        
        for filename, description in files:
            filepath = os.path.join(viz_dir, filename)
            if os.path.exists(filepath):
                print(f"  ✅ {filename} - {description}")
            else:
                print(f"  ❌ {filename} - Not created")
        
        # Offer to open the HTML report
        html_report = os.path.join(viz_dir, f"{base_name}_phase1_report.html")
        if os.path.exists(html_report):
            print()
            print("🌐 To view the interactive report:")
            print(f"   Open: {html_report}")
            print("   Or run: python3 view_phase1.py")
        
    except Exception as e:
        print(f"❌ Error during visualization: {e}")
        print("🔍 Check that the image contains detectable QR patterns")

if __name__ == "__main__":
    main()
