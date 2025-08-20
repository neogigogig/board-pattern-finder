#!/usr/bin/env python3
"""
QR Orientation Analysis Tool
Analyzes real QR code orientations from detected patterns
"""

import cv2
import numpy as np
import json
import os
from pathlib import Path
from qr_orientation_detector import QROrientationDetector
from enhanced_strict_qr_detector import EnhancedStrictQRDetector

def analyze_qr_orientations_from_results():
    """
    Analyze QR code orientations from previously detected patterns
    """
    print("🧭 QR ORIENTATION ANALYSIS FROM DETECTION RESULTS")
    print("=" * 60)
    
    # Load detection results
    results_dir = Path("results/enhanced-strict-qr-results")
    data_dir = Path("data-qr-ratio-finder")
    output_dir = Path("results/qr-orientation-analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize orientation detector
    orientation_detector = QROrientationDetector()
    
    # Find all result JSON files
    json_files = list(results_dir.glob("*_results.json"))
    
    if not json_files:
        print("❌ No detection result files found!")
        return
    
    print(f"📊 Found {len(json_files)} detection result files")
    
    all_orientations = {}
    
    for json_file in json_files:
        try:
            # Load detection results
            with open(json_file, 'r') as f:
                detection_data = json.load(f)
            
            image_name = json_file.stem.replace('_results', '')
            patterns = detection_data.get('patterns', [])
            
            if len(patterns) < 3:
                print(f"⚠️  {image_name}: Only {len(patterns)} patterns (need ≥3)")
                continue
            
            print(f"\n🔍 Analyzing orientation: {image_name}")
            print(f"   Found {len(patterns)} finder patterns")
            
            # Convert pattern format for orientation detector
            finder_patterns = []
            for pattern in patterns:
                center = pattern['center']
                finder_patterns.append({
                    'center': center,
                    'size': pattern['size']
                })
            
            # Detect orientation
            orientation_data = orientation_detector.detect_orientation(finder_patterns)
            
            if orientation_data:
                angles = orientation_data['angles']
                description = orientation_data['description']
                
                print(f"   ✅ Orientation detected:")
                print(f"      Primary Rotation: {angles['primary_rotation']:.1f}°")
                print(f"      Skew Angle: {angles['skew_angle']:.1f}°")
                print(f"      Description: {description}")
                
                # Load original image for visualization
                image_path = None
                for ext in ['.jpeg', '.jpg', '.png']:
                    potential_path = data_dir / f"{image_name}{ext}"
                    if potential_path.exists():
                        image_path = potential_path
                        break
                
                if image_path:
                    image = cv2.imread(str(image_path))
                    if image is not None:
                        # Create orientation visualization
                        viz_path = output_dir / f"{image_name}_orientation.png"
                        orientation_detector.visualize_orientation(
                            image, orientation_data, str(viz_path)
                        )
                
                # Store orientation data
                all_orientations[image_name] = {
                    'angles': angles,
                    'description': description,
                    'positions': {
                        'top_left': orientation_data['positions']['top_left']['center'],
                        'top_right': orientation_data['positions']['top_right']['center'],
                        'bottom_left': orientation_data['positions']['bottom_left']['center']
                    },
                    'fourth_corner': orientation_data['fourth_corner'],
                    'pattern_count': len(patterns)
                }
                
            else:
                print(f"   ❌ Orientation detection failed")
                
        except Exception as e:
            print(f"❌ Error processing {json_file.name}: {e}")
    
    # Save orientation analysis results
    if all_orientations:
        results_path = output_dir / "orientation_analysis_results.json"
        with open(results_path, 'w') as f:
            json.dump(all_orientations, f, indent=2, default=str)
        
        print(f"\n📁 Orientation analysis saved: {results_path}")
        
        # Create summary report
        create_orientation_summary(all_orientations, output_dir)
        
    return all_orientations

def create_orientation_summary(orientations: dict, output_dir: Path):
    """
    Create a summary report of all orientation analyses
    """
    print(f"\n📊 ORIENTATION ANALYSIS SUMMARY")
    print("=" * 50)
    
    if not orientations:
        print("❌ No orientation data to summarize")
        return
    
    total_images = len(orientations)
    print(f"Total images analyzed: {total_images}")
    
    # Analyze rotation distribution
    rotations = [data['angles']['primary_rotation'] for data in orientations.values()]
    skews = [data['angles']['skew_angle'] for data in orientations.values()]
    
    # Categorize rotations
    upright = sum(1 for r in rotations if abs(r) < 15)
    rotated_90 = sum(1 for r in rotations if abs(abs(r) - 90) < 15)
    upside_down = sum(1 for r in rotations if abs(abs(r) - 180) < 15)
    rotated_270 = sum(1 for r in rotations if abs(abs(r) - 270) < 15)
    angled = total_images - upright - rotated_90 - upside_down - rotated_270
    
    print(f"\n🔄 Rotation Distribution:")
    print(f"   Upright (±15°): {upright}")
    print(f"   90° rotated: {rotated_90}")
    print(f"   180° rotated: {upside_down}")
    print(f"   270° rotated: {rotated_270}")
    print(f"   Other angles: {angled}")
    
    # Analyze skew
    well_aligned = sum(1 for s in skews if s < 5)
    slightly_skewed = sum(1 for s in skews if 5 <= s < 15)
    moderately_skewed = sum(1 for s in skews if 15 <= s < 30)
    heavily_skewed = sum(1 for s in skews if s >= 30)
    
    print(f"\n📐 Skew Distribution:")
    print(f"   Well-aligned (<5°): {well_aligned}")
    print(f"   Slightly skewed (5-15°): {slightly_skewed}")
    print(f"   Moderately skewed (15-30°): {moderately_skewed}")
    print(f"   Heavily skewed (≥30°): {heavily_skewed}")
    
    # Individual image details
    print(f"\n📋 Individual Analysis:")
    for image_name, data in orientations.items():
        rotation = data['angles']['primary_rotation']
        skew = data['angles']['skew_angle']
        print(f"   {image_name}:")
        print(f"      Rotation: {rotation:+6.1f}° | Skew: {skew:5.1f}° | {data['description']}")
    
    # Calculate statistics
    avg_rotation = np.mean([abs(r) for r in rotations])
    avg_skew = np.mean(skews)
    
    print(f"\n📈 Statistics:")
    print(f"   Average absolute rotation: {avg_rotation:.1f}°")
    print(f"   Average skew: {avg_skew:.1f}°")
    print(f"   Rotation range: {min(rotations):.1f}° to {max(rotations):.1f}°")
    print(f"   Skew range: {min(skews):.1f}° to {max(skews):.1f}°")
    
    # Save detailed summary
    summary_data = {
        'total_images': total_images,
        'rotation_distribution': {
            'upright': upright,
            'rotated_90': rotated_90,
            'upside_down': upside_down,
            'rotated_270': rotated_270,
            'angled': angled
        },
        'skew_distribution': {
            'well_aligned': well_aligned,
            'slightly_skewed': slightly_skewed,
            'moderately_skewed': moderately_skewed,
            'heavily_skewed': heavily_skewed
        },
        'statistics': {
            'average_absolute_rotation': avg_rotation,
            'average_skew': avg_skew,
            'rotation_range': [min(rotations), max(rotations)],
            'skew_range': [min(skews), max(skews)]
        },
        'individual_results': orientations
    }
    
    summary_path = output_dir / "orientation_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2, default=str)
    
    print(f"\n💾 Detailed summary saved: {summary_path}")

def analyze_single_image_orientation(image_path: str):
    """
    Analyze orientation for a single image using live detection
    """
    print(f"🧭 Analyzing orientation for: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return None
    
    # Detect QR patterns
    detector = EnhancedStrictQRDetector()
    patterns, gray, binary_results = detector.find_qr_patterns_multi_threshold(image)
    
    if len(patterns) < 3:
        print(f"❌ Not enough patterns detected: {len(patterns)} (need ≥3)")
        return None
    
    print(f"✅ Detected {len(patterns)} QR patterns")
    
    # Convert for orientation analysis
    finder_patterns = []
    for pattern in patterns:
        center = pattern['center']
        finder_patterns.append({
            'center': center,
            'size': pattern['size']
        })
    
    # Analyze orientation
    orientation_detector = QROrientationDetector()
    orientation_data = orientation_detector.detect_orientation(finder_patterns)
    
    if orientation_data:
        angles = orientation_data['angles']
        print(f"✅ Orientation Analysis:")
        print(f"   Primary Rotation: {angles['primary_rotation']:.1f}°")
        print(f"   Skew Angle: {angles['skew_angle']:.1f}°")
        print(f"   Description: {orientation_data['description']}")
        
        # Create visualization
        output_path = f"qr_orientation_{Path(image_path).stem}.png"
        orientation_detector.visualize_orientation(image, orientation_data, output_path)
        
        return orientation_data
    else:
        print("❌ Orientation analysis failed")
        return None

if __name__ == "__main__":
    # Analyze orientations from existing detection results
    orientations = analyze_qr_orientations_from_results()
    
    if orientations:
        print(f"\n🎉 Orientation analysis complete!")
        print(f"📁 Results saved in: results/qr-orientation-analysis/")
        print(f"📊 {len(orientations)} images analyzed")
