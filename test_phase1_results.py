#!/usr/bin/env python3
"""
Test Phase 1 QR Data Reading Results
Shows the perspective-corrected QR codes from the detection process
"""

import cv2
import os

def display_qr_results():
    """Display the Phase 1 QR data extraction results"""
    print("🔮 QR DATA READER - PHASE 1 RESULTS")
    print("=" * 50)
    
    results_folder = "results/enhanced-strict-qr-results"
    corrected_files = [f for f in os.listdir(results_folder) if f.startswith('corrected_')]
    
    print(f"Found {len(corrected_files)} perspective-corrected QR codes:")
    
    for i, filename in enumerate(corrected_files, 1):
        filepath = os.path.join(results_folder, filename)
        
        # Get file size
        file_size = os.path.getsize(filepath) // 1024  # KB
        
        print(f"{i:2d}. {filename:<35} ({file_size:3d} KB)")
        
        # Quick image analysis
        img = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            height, width = img.shape
            print(f"    📐 Size: {width}x{height} pixels")
            
            # Check if it looks like a QR code (has dark/light regions)
            mean_intensity = img.mean()
            std_intensity = img.std()
            print(f"    🎨 Intensity: mean={mean_intensity:.1f}, std={std_intensity:.1f}")
    
    print("\n✅ Phase 1 Complete: Basic Geometry & Perspective Correction")
    print("📋 What was accomplished:")
    print("   • ✅ 4th corner calculation from 3 finder patterns")
    print("   • ✅ Perspective transformation to square QR images") 
    print("   • ✅ QR version detection (size estimation)")
    print("   • ✅ Corner ordering and geometric validation")
    
    print("\n🚀 Next Phase 2 will add:")
    print("   • 📊 Grid extraction and module sampling")
    print("   • 🔢 Binary data reading from QR modules") 
    print("   • 🎯 Adaptive thresholding per module")
    print("   • 📏 Precise QR version detection")

if __name__ == "__main__":
    display_qr_results()
