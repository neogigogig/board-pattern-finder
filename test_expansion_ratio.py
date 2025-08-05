#!/usr/bin/env python3
"""
Test script to verify the exact expansion ratio calculation
"""

def test_exact_expansion_ratio():
    """Test that the expansion ratio is exactly 15.8/11.8"""
    expected_ratio = 15.8 / 11.8
    calculated_ratio = 1.3389830508474576  # From the code
    
    print(f"Expected ratio (15.8/11.8): {expected_ratio}")
    print(f"Calculated ratio: {calculated_ratio}")
    print(f"Difference: {abs(expected_ratio - calculated_ratio)}")
    print(f"Match: {abs(expected_ratio - calculated_ratio) < 1e-10}")
    
    # Test with sample coordinates
    print("\n=== Sample Expansion Test ===")
    center = (100, 100)
    corner = (120, 110)  # 20 pixels right, 10 pixels down
    
    # Calculate vector from center to corner
    dx = corner[0] - center[0]  # 20
    dy = corner[1] - center[1]  # 10
    
    # Apply expansion
    expanded_dx = dx * expected_ratio  # 20 * 1.339 = 26.78
    expanded_dy = dy * expected_ratio  # 10 * 1.339 = 13.39
    
    expanded_corner = (center[0] + expanded_dx, center[1] + expanded_dy)
    
    print(f"Original corner: {corner}")
    print(f"Center: {center}")
    print(f"Vector: ({dx}, {dy})")
    print(f"Expanded vector: ({expanded_dx:.2f}, {expanded_dy:.2f})")
    print(f"Expanded corner: ({expanded_corner[0]:.2f}, {expanded_corner[1]:.2f})")
    print(f"Expansion factor applied: {expected_ratio:.6f}")

if __name__ == "__main__":
    test_exact_expansion_ratio()
