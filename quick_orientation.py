#!/usr/bin/env python3
"""
Quick QR Orientation Tool
Simple utility to get QR code orientation from finder patterns
"""

from qr_orientation_detector import QROrientationDetector
from typing import List, Dict, Tuple

def get_qr_orientation(finder_patterns: List[Dict]) -> Dict:
    """
    Simple function to get QR code orientation from finder patterns
    
    Args:
        finder_patterns: List of finder pattern dictionaries with 'center' and 'size'
        
    Returns:
        Dictionary with orientation information
    """
    detector = QROrientationDetector()
    orientation_data = detector.detect_orientation(finder_patterns)
    
    if not orientation_data:
        return {
            'success': False,
            'error': 'Could not determine orientation',
            'rotation': None,
            'skew': None,
            'description': None
        }
    
    angles = orientation_data['angles']
    
    return {
        'success': True,
        'rotation': angles['primary_rotation'],
        'skew': angles['skew_angle'],
        'description': orientation_data['description'],
        'angles': angles,
        'positions': orientation_data['positions'],
        'fourth_corner': orientation_data['fourth_corner']
    }

def print_orientation_summary(orientation_data: Dict):
    """Print a clean summary of orientation data"""
    if not orientation_data['success']:
        print(f"❌ {orientation_data['error']}")
        return
    
    rotation = orientation_data['rotation']
    skew = orientation_data['skew']
    description = orientation_data['description']
    
    print(f"🧭 QR Code Orientation:")
    print(f"   Primary Rotation: {rotation:+6.1f}°")
    print(f"   Skew Angle:       {skew:6.1f}°")
    print(f"   Description:      {description}")

# Example usage function
def example_usage():
    """Example of how to use the orientation detection"""
    print("📚 QR Orientation Detection - Usage Examples")
    print("=" * 50)
    
    # Example 1: Upright QR code
    print("\n🔍 Example 1: Upright QR Code")
    patterns_upright = [
        {'center': (100, 100), 'size': 30},  # Top-left
        {'center': (300, 100), 'size': 30},  # Top-right
        {'center': (100, 300), 'size': 30}   # Bottom-left
    ]
    
    orientation = get_qr_orientation(patterns_upright)
    print_orientation_summary(orientation)
    
    # Example 2: Rotated QR code
    print("\n🔍 Example 2: Rotated QR Code (45 degrees)")
    patterns_rotated = [
        {'center': (200, 100), 'size': 30},  # Rotated top-left
        {'center': (300, 200), 'size': 30},  # Rotated top-right
        {'center': (100, 200), 'size': 30}   # Rotated bottom-left
    ]
    
    orientation = get_qr_orientation(patterns_rotated)
    print_orientation_summary(orientation)
    
    # Example 3: Using with actual detection results
    print("\n🔍 Example 3: Integration with Detection Results")
    print("# In your code, after detecting QR patterns:")
    print("patterns, _, _ = detector.find_qr_patterns_multi_threshold(image)")
    print("orientation = get_qr_orientation(patterns)")
    print("print_orientation_summary(orientation)")
    print("")
    print("# Access specific values:")
    print("if orientation['success']:")
    print("    rotation_angle = orientation['rotation']")
    print("    skew_angle = orientation['skew']")
    print("    print(f'QR code is rotated {rotation_angle:.1f} degrees')")

if __name__ == "__main__":
    example_usage()
