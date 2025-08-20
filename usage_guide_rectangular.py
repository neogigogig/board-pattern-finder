#!/usr/bin/env python3
"""
Flexible Pattern Detector Usage Guide
Shows how to use the rectangular pattern detection system
"""

from enhanced_strict_qr_detector import EnhancedStrictQRDetector
from qr_data_reader import QRDataReader

def usage_examples():
    """Demonstrate different usage patterns"""
    print("🎯 FLEXIBLE PATTERN DETECTOR - USAGE GUIDE")
    print("=" * 60)
    
    print("\n📋 STEP 1: Initialize with desired ratio")
    print("   # Square patterns (traditional QR codes)")
    print("   detector = EnhancedStrictQRDetector(width_height_ratio=1.0)")
    print()
    print("   # Wide rectangular patterns (3:2 landscape)")
    print("   detector = EnhancedStrictQRDetector(width_height_ratio=1.5)")
    print()
    print("   # Tall rectangular patterns (2:3 portrait)")
    print("   detector = EnhancedStrictQRDetector(width_height_ratio=0.67)")
    
    print("\n📋 STEP 2: Detect patterns normally")
    print("   patterns, _, _ = detector.find_qr_patterns_multi_threshold(image)")
    
    print("\n📋 STEP 3: Extract with custom dimensions")
    print("   # For wide patterns (3:2 ratio)")
    print("   result = detector.extract_qr_data_if_possible(")
    print("       image, patterns, ")
    print("       output_width=450    # Width you want")
    print("   )   # Height auto-calculated: 450/1.5 = 300")
    print()
    print("   # Or specify both dimensions explicitly")
    print("   result = detector.extract_qr_data_if_possible(")
    print("       image, patterns,")
    print("       output_width=600,")
    print("       output_height=400   # Custom height")
    print("   )")
    
    print("\n📋 STEP 4: Access results")
    print("   if result:")
    print("       corrected_image = result['corrected_image']")
    print("       module_grid = result['expected_modules']  # e.g., '21x14'")
    print("       dimensions = result['output_dimensions']  # e.g., (450, 300)")
    print("       ratio = result['width_height_ratio']      # e.g., 1.5")
    
    print("\n💡 COMMON RATIOS:")
    print("   • 1.0   → Square (QR codes)")
    print("   • 1.5   → 3:2 landscape") 
    print("   • 0.67  → 2:3 portrait")
    print("   • 1.33  → 4:3 video format")
    print("   • 1.78  → 16:9 widescreen")
    print("   • 2.0   → 2:1 ultra-wide")
    
    print("\n🔧 DIRECT QR DATA READER USAGE:")
    print("   # For custom applications")
    print("   reader = QRDataReader(width_height_ratio=1.5)")
    print("   result = reader.extract_qr_data(image, patterns, 450, 300)")

def practical_examples():
    """Show practical real-world examples"""
    print("\n🌍 REAL-WORLD EXAMPLES")
    print("=" * 40)
    
    examples = [
        {
            'use_case': 'Business Cards with QR-like patterns',
            'ratio': 1.75,
            'description': 'Standard business card proportions',
            'code': 'detector = EnhancedStrictQRDetector(width_height_ratio=1.75)'
        },
        {
            'use_case': 'Receipt patterns',
            'ratio': 0.5,
            'description': 'Tall narrow receipts',
            'code': 'detector = EnhancedStrictQRDetector(width_height_ratio=0.5)'
        },
        {
            'use_case': 'Banner/billboard patterns',
            'ratio': 3.0,
            'description': 'Very wide display formats',
            'code': 'detector = EnhancedStrictQRDetector(width_height_ratio=3.0)'
        },
        {
            'use_case': 'Mobile screen patterns',
            'ratio': 0.56,
            'description': 'Modern phone aspect ratios (9:16)',
            'code': 'detector = EnhancedStrictQRDetector(width_height_ratio=0.56)'
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['use_case']}")
        print(f"   📐 Ratio: {example['ratio']:.2f} ({example['description']})")
        print(f"   💻 Code: {example['code']}")

def key_benefits():
    """Highlight the key benefits of flexible ratios"""
    print("\n✨ KEY BENEFITS")
    print("=" * 30)
    
    benefits = [
        "🎯 Accurate perspective correction for any rectangle",
        "📏 Proper module counting for non-square grids",
        "🔄 Maintains geometric relationships between finder patterns",
        "⚡ Same detection algorithms work for any aspect ratio",
        "🎨 Custom output dimensions for different applications",
        "📱 Ready for modern display formats and orientations",
        "🔧 Easy integration - just change one parameter"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")

if __name__ == "__main__":
    usage_examples()
    practical_examples()
    key_benefits()
    
    print(f"\n{'='*60}")
    print("🚀 Ready to use flexible pattern detection!")
    print("📚 Modify width_height_ratio parameter to fit your patterns")
    print("💾 Generated images will match your specified aspect ratio")
