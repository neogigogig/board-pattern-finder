#!/usr/bin/env python3
"""
Visualization Guide for Phase 2 Results
Shows how to view and analyze all the generated visual outputs
"""

import os
import webbrowser
from pathlib import Path

def show_visualization_options():
    """Display all available visualization options"""
    print("🎨 PHASE 2 VISUALIZATION GUIDE")
    print("=" * 60)
    
    results_dir = "results/enhanced-strict-qr-results"
    
    print("\n📁 AVAILABLE VISUALIZATIONS:")
    print("-" * 40)
    
    viz_categories = [
        {
            'name': '1. 🔍 Phase 2 Grid Visualization',
            'files': ['phase2_grid_visualization.png'],
            'description': 'Visual representation of the binary module grid'
        },
        {
            'name': '2. 📐 Perspective-Corrected QR Images',
            'files': ['corrected_image copy.png', 'corrected_image copy 2.png', 'corrected_image copy 3.png'],
            'description': 'Clean, square QR patterns after perspective correction'
        },
        {
            'name': '3. 🔲 Rectangular Pattern Tests',
            'files': ['rectangular_test_1.00_ratio.png', 'rectangular_test_1.50_ratio.png', 
                     'rectangular_test_0.67_ratio.png', 'rectangular_test_2.00_ratio.png'],
            'description': 'Different aspect ratio outputs (square, wide, tall)'
        },
        {
            'name': '4. 📊 Detection Overlays',
            'files': ['detected_image copy.png', 'detected_image copy 2.png'],
            'description': 'Original images with finder pattern detection overlays'
        },
        {
            'name': '5. ⚫⚪ Binary Threshold Visualizations',
            'files': ['binary_adaptive_gaussian_image copy.png', 'binary_otsu_image copy.png'],
            'description': 'Different thresholding methods applied to images'
        }
    ]
    
    for category in viz_categories:
        print(f"\n{category['name']}")
        print(f"   📝 {category['description']}")
        print("   📂 Files:")
        for file in category['files']:
            file_path = os.path.join(results_dir, file)
            if os.path.exists(file_path):
                size_kb = os.path.getsize(file_path) // 1024
                print(f"      ✅ {file} ({size_kb} KB)")
            else:
                print(f"      ❌ {file} (not found)")

def create_html_gallery():
    """Create an HTML gallery to view all visualizations"""
    results_dir = "results/enhanced-strict-qr-results"
    
    # Key visualization files to include in gallery
    gallery_files = [
        {
            'title': 'Phase 2 Grid Visualization',
            'file': 'phase2_grid_visualization.png',
            'description': 'Binary module grid with 21x21 modules. Black squares = 1, White squares = 0, Gray lines = grid boundaries.'
        },
        {
            'title': 'Square Pattern (1:1 ratio)',
            'file': 'rectangular_test_1.00_ratio.png',
            'description': 'Standard square QR pattern (300x300 pixels)'
        },
        {
            'title': 'Wide Rectangle (3:2 ratio)',
            'file': 'rectangular_test_1.50_ratio.png',
            'description': 'Wide rectangular pattern (450x300 pixels)'
        },
        {
            'title': 'Tall Rectangle (2:3 ratio)',
            'file': 'rectangular_test_0.67_ratio.png',
            'description': 'Tall rectangular pattern (300x447 pixels)'
        },
        {
            'title': 'Very Wide Rectangle (2:1 ratio)',
            'file': 'rectangular_test_2.00_ratio.png',
            'description': 'Ultra-wide rectangular pattern (600x300 pixels)'
        },
        {
            'title': 'Corrected QR Image',
            'file': 'corrected_image copy.png',
            'description': 'Perspective-corrected QR code ready for module sampling'
        },
        {
            'title': 'Detection Overlay',
            'file': 'detected_image copy.png',
            'description': 'Original image with finder pattern detection overlays'
        },
        {
            'title': 'Binary Threshold (Adaptive)',
            'file': 'binary_adaptive_gaussian_image copy.png',
            'description': 'Adaptive Gaussian thresholding result'
        }
    ]
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phase 2 QR Detection Visualization Gallery</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .card img {
            width: 100%;
            height: 300px;
            object-fit: contain;
            background: #f8f9fa;
            border-bottom: 1px solid #eee;
        }
        .card-content {
            padding: 15px;
        }
        .card-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .card-description {
            color: #666;
            line-height: 1.4;
        }
        .stats {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .stats h3 {
            margin-top: 0;
            color: #1976d2;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Phase 2 QR Detection Visualization Gallery</h1>
        <p>Comprehensive visual analysis of grid detection and module reading results</p>
    </div>
    
    <div class="stats">
        <h3>📊 Phase 2 Statistics</h3>
        <ul>
            <li><strong>Grid Sampling:</strong> 21x21 modules = 441 total modules</li>
            <li><strong>Data Modules:</strong> 280 (after excluding function patterns)</li>
            <li><strong>Binary Accuracy:</strong> 44 black modules, 397 white modules</li>
            <li><strong>Data Density:</strong> 0.13 (13% black modules)</li>
            <li><strong>Aspect Ratios Tested:</strong> 1:1, 3:2, 2:3, 2:1</li>
        </ul>
    </div>
    
    <div class="gallery">
"""
    
    for item in gallery_files:
        file_path = os.path.join(results_dir, item['file'])
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) // 1024
            html_content += f"""
        <div class="card">
            <img src="{item['file']}" alt="{item['title']}">
            <div class="card-content">
                <div class="card-title">{item['title']}</div>
                <div class="card-description">
                    {item['description']}
                    <br><small>File size: {size_kb} KB</small>
                </div>
            </div>
        </div>
"""
    
    html_content += """
    </div>
    
    <div style="text-align: center; margin-top: 40px; padding: 20px; background: white; border-radius: 10px;">
        <h3>🚀 Next Steps</h3>
        <p>Phase 2 has successfully extracted binary module data. Ready for Phase 3: Data Decoding!</p>
    </div>
</body>
</html>
"""
    
    # Save HTML file
    html_path = os.path.join(results_dir, "phase2_visualization_gallery.html")
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    return html_path

def show_viewing_methods():
    """Show different ways to view the visualizations"""
    print(f"\n💻 VIEWING METHODS:")
    print("=" * 30)
    
    methods = [
        {
            'method': '1. 🌐 Web Browser Gallery',
            'description': 'Interactive HTML gallery with all visualizations',
            'command': 'Open: results/enhanced-strict-qr-results/phase2_visualization_gallery.html'
        },
        {
            'method': '2. 🖼️  Image Viewer',
            'description': 'Open individual PNG files in your default image viewer',
            'command': 'Double-click any .png file in results/enhanced-strict-qr-results/'
        },
        {
            'method': '3. 📁 Finder/File Explorer',
            'description': 'Browse files directly in your file manager',
            'command': 'Navigate to: results/enhanced-strict-qr-results/'
        },
        {
            'method': '4. 🔍 VS Code Preview',
            'description': 'Preview images directly in VS Code',
            'command': 'Right-click PNG files → "Open Preview"'
        },
        {
            'method': '5. 📊 JSON Analysis',
            'description': 'View detailed numerical data',
            'command': 'Open: phase2_test_results.json'
        }
    ]
    
    for method in methods:
        print(f"\n{method['method']}")
        print(f"   📝 {method['description']}")
        print(f"   💻 {method['command']}")

def show_key_visualizations():
    """Highlight the most important visualizations"""
    print(f"\n⭐ KEY VISUALIZATIONS TO CHECK:")
    print("=" * 40)
    
    key_files = [
        {
            'file': 'phase2_grid_visualization.png',
            'importance': '🔥 MOST IMPORTANT',
            'what': 'Shows the actual binary grid with 0s and 1s',
            'look_for': 'Black squares (1s), white squares (0s), grid structure'
        },
        {
            'file': 'rectangular_test_1.00_ratio.png',
            'importance': '⭐ HIGH',
            'what': 'Clean perspective-corrected square QR',
            'look_for': 'Sharp corners, clear modules, proper alignment'
        },
        {
            'file': 'rectangular_test_1.50_ratio.png',
            'importance': '⭐ HIGH',
            'what': 'Wide rectangular pattern (3:2 ratio)',
            'look_for': 'Rectangular shape, maintained proportions'
        },
        {
            'file': 'detected_image copy.png',
            'importance': '📍 REFERENCE',
            'what': 'Original detection with overlays',
            'look_for': 'Green circles on finder patterns, detection accuracy'
        },
        {
            'file': 'phase2_test_results.json',
            'importance': '📊 DATA',
            'what': 'Complete numerical analysis',
            'look_for': 'Module counts, densities, grid structure data'
        }
    ]
    
    for viz in key_files:
        print(f"\n{viz['importance']} - {viz['file']}")
        print(f"   📋 What it shows: {viz['what']}")
        print(f"   👀 Look for: {viz['look_for']}")

if __name__ == "__main__":
    show_visualization_options()
    
    print(f"\n🎨 CREATING HTML GALLERY...")
    html_path = create_html_gallery()
    print(f"✅ Gallery created: {html_path}")
    
    show_viewing_methods()
    show_key_visualizations()
    
    print(f"\n{'='*60}")
    print(f"🚀 QUICK START:")
    print(f"   1. Open: results/enhanced-strict-qr-results/phase2_visualization_gallery.html")
    print(f"   2. View: phase2_grid_visualization.png (the binary grid)")
    print(f"   3. Compare: rectangular_test_*.png files (different ratios)")
    print(f"   4. Analyze: phase2_test_results.json (detailed data)")
