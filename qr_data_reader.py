#!/usr/bin/env python3
"""
QR Data Reader - Phase 1: Basic Geometry
Handles 4th corner detection and perspective correction for QR codes
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import math

class QRDataReader:
    def __init__(self, width_height_ratio: float = 1.0):
        """
        Initialize QR Data Reader
        
        Args:
            width_height_ratio: Ratio of width to height (default 1.0 for square)
                               e.g., 1.5 for 3:2 ratio, 0.75 for 3:4 ratio
        """
        self.debug_info = []
        self.width_height_ratio = width_height_ratio
        
    def reset_debug(self):
        """Reset debug information"""
        self.debug_info = []
        
    def add_debug(self, message, data=None):
        """Add debug information"""
        self.debug_info.append({
            'message': message,
            'data': data
        })
    
    def calculate_fourth_corner(self, finder_patterns: List[Dict]) -> Optional[Tuple[int, int]]:
        """
        Calculate the 4th corner position from 3 finder patterns using parallelogram properties
        
        Args:
            finder_patterns: List of 3 finder pattern dictionaries with 'center' coordinates
            
        Returns:
            Tuple of (x, y) coordinates for the 4th corner, or None if calculation fails
        """
        if len(finder_patterns) < 3:
            self.add_debug("Not enough finder patterns for 4th corner calculation")
            return None
            
        # Extract centers
        centers = [p['center'] for p in finder_patterns]
        
        # Sort patterns to identify top-left, top-right, bottom-left
        # Strategy: find the pattern that's closest to the other two (this will be a corner pattern)
        distances = []
        for i in range(3):
            dist_sum = 0
            for j in range(3):
                if i != j:
                    dx = centers[i][0] - centers[j][0]
                    dy = centers[i][1] - centers[j][1]
                    dist_sum += math.sqrt(dx*dx + dy*dy)
            distances.append((dist_sum, i))
        
        distances.sort()
        
        # The pattern with minimum total distance to others is likely top-left
        top_left_idx = distances[0][1]
        top_left = centers[top_left_idx]
        
        # Get the other two patterns
        other_patterns = [centers[i] for i in range(3) if i != top_left_idx]
        
        # Determine which is top-right and which is bottom-left
        # Top-right should be to the right of top-left
        # Bottom-left should be below top-left
        p1, p2 = other_patterns
        
        # Calculate relative positions
        p1_right = p1[0] > top_left[0]
        p1_down = p1[1] > top_left[1]
        p2_right = p2[0] > top_left[0]
        p2_down = p2[1] > top_left[1]
        
        # Assign top-right and bottom-left
        if p1_right and not p1_down:
            top_right = p1
            bottom_left = p2
        elif p2_right and not p2_down:
            top_right = p2
            bottom_left = p1
        else:
            # Fallback: use distance-based assignment
            if abs(p1[1] - top_left[1]) < abs(p2[1] - top_left[1]):
                top_right = p1
                bottom_left = p2
            else:
                top_right = p2
                bottom_left = p1
        
        # Calculate 4th corner using parallelogram properties
        # bottom_right = top_right + bottom_left - top_left
        bottom_right_x = top_right[0] + bottom_left[0] - top_left[0]
        bottom_right_y = top_right[1] + bottom_left[1] - top_left[1]
        
        self.add_debug(f"Calculated corners: TL{top_left}, TR{top_right}, BL{bottom_left}, BR({bottom_right_x:.0f},{bottom_right_y:.0f})")
        
        return (int(bottom_right_x), int(bottom_right_y))
    
    def order_corners(self, finder_patterns: List[Dict], fourth_corner: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Order corners in clockwise order starting from top-left
        
        Returns:
            List of 4 corners: [top_left, top_right, bottom_right, bottom_left]
        """
        # Get all corners including the calculated 4th corner
        all_corners = [p['center'] for p in finder_patterns]
        all_corners.append(fourth_corner)
        
        # Find centroid
        cx = sum(c[0] for c in all_corners) / 4
        cy = sum(c[1] for c in all_corners) / 4
        
        # Sort by angle from centroid
        def angle_from_center(point):
            return math.atan2(point[1] - cy, point[0] - cx)
        
        corners_with_angles = [(c, angle_from_center(c)) for c in all_corners]
        corners_with_angles.sort(key=lambda x: x[1])
        
        # Extract sorted corners
        sorted_corners = [c[0] for c in corners_with_angles]
        
        # Find top-left (minimum x + y)
        top_left_idx = min(range(4), key=lambda i: sorted_corners[i][0] + sorted_corners[i][1])
        
        # Reorder to start from top-left and go clockwise
        ordered_corners = []
        for i in range(4):
            idx = (top_left_idx + i) % 4
            ordered_corners.append(sorted_corners[idx])
        
        self.add_debug(f"Ordered corners: {ordered_corners}")
        return ordered_corners
    
    def correct_perspective(self, image: np.ndarray, finder_patterns: List[Dict], 
                          output_width: int = 300, output_height: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Apply perspective correction to extract pattern as a rectangular image
        
        Args:
            image: Input image containing pattern
            finder_patterns: List of detected finder patterns
            output_width: Width of output image
            output_height: Height of output image (if None, calculated from width_height_ratio)
            
        Returns:
            Perspective-corrected rectangular image, or None if correction fails
        """
        if len(finder_patterns) < 3:
            self.add_debug("Not enough finder patterns for perspective correction")
            return None
        
        # Calculate output height if not provided
        if output_height is None:
            output_height = int(output_width / self.width_height_ratio)
        
        # Calculate 4th corner
        fourth_corner = self.calculate_fourth_corner(finder_patterns)
        if fourth_corner is None:
            return None
        
        # Order corners properly
        corners = self.order_corners(finder_patterns, fourth_corner)
        
        # Source points (detected corners)
        src_points = np.array(corners, dtype=np.float32)
        
        # Destination points (rectangle with specified ratio)
        dst_points = np.array([
            [0, 0],                           # top-left
            [output_width-1, 0],              # top-right
            [output_width-1, output_height-1], # bottom-right
            [0, output_height-1]              # bottom-left
        ], dtype=np.float32)
        
        # Calculate perspective transform matrix
        transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        
        # Apply perspective correction
        corrected_image = cv2.warpPerspective(image, transform_matrix, (output_width, output_height))
        
        self.add_debug(f"Perspective correction applied: {output_width}x{output_height} (ratio: {self.width_height_ratio:.2f})")
        return corrected_image
    
    def detect_qr_version(self, corrected_image: np.ndarray) -> int:
        """
        Detect QR code version by counting modules (adapted for rectangular patterns)
        
        Args:
            corrected_image: Perspective-corrected pattern image
            
        Returns:
            QR version number (1-40) or estimated module count for rectangular patterns
        """
        # Convert to grayscale if needed
        if len(corrected_image.shape) == 3:
            gray = cv2.cvtColor(corrected_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = corrected_image.copy()
        
        # Apply binary threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Sample a horizontal line through the middle to count transitions
        height, _ = binary.shape
        middle_row = binary[height // 2, :]
        
        # Count black-white transitions
        transitions = 0
        for i in range(1, len(middle_row)):
            if middle_row[i] != middle_row[i-1]:
                transitions += 1
        
        # For rectangular patterns, estimate based on transitions and ratio
        if abs(self.width_height_ratio - 1.0) > 0.01:  # Not square (allow small tolerance)
            # Estimate horizontal modules
            estimated_h_modules = max(21, transitions // 2)
            # Estimate vertical modules based on ratio
            estimated_v_modules = int(estimated_h_modules / self.width_height_ratio)
            
            self.add_debug(f"Rectangular pattern - H modules: {estimated_h_modules}, V modules: {estimated_v_modules}, ratio: {self.width_height_ratio:.2f}")
            return estimated_h_modules  # Return horizontal count as primary
        
        # For square patterns (QR codes), use standard QR version detection
        estimated_modules = max(21, transitions // 2)
        
        # Round to nearest valid QR size: 21, 25, 29, 33, 37, 41, etc.
        # Formula: size = 21 + (version-1) * 4
        version = max(1, round((estimated_modules - 21) / 4) + 1)
        version = min(version, 40)  # Cap at version 40
        
        self.add_debug(f"Square QR version: {version} (transitions: {transitions}, modules: {estimated_modules})")
        return version
    
    def extract_qr_data(self, image: np.ndarray, finder_patterns: List[Dict], 
                       output_width: int = 300, output_height: Optional[int] = None) -> Optional[Dict]:
        """
        Main method to extract pattern data from detected finder patterns
        
        Args:
            image: Input image
            finder_patterns: List of detected finder patterns
            output_width: Width of output corrected image
            output_height: Height of output corrected image (calculated from ratio if None)
            
        Returns:
            Dictionary with extracted pattern information or None if extraction fails
        """
        self.reset_debug()
        
        if len(finder_patterns) < 3:
            self.add_debug("Need at least 3 finder patterns for pattern data extraction")
            return None
        
        # Apply perspective correction
        corrected_pattern = self.correct_perspective(image, finder_patterns, output_width, output_height)
        if corrected_pattern is None:
            return None
        
        # Detect pattern version/size
        version = self.detect_qr_version(corrected_pattern)
        
        # Calculate expected size based on ratio
        if output_height is None:
            output_height = int(output_width / self.width_height_ratio)
        
        # Calculate expected modules
        if abs(self.width_height_ratio - 1.0) > 0.01:  # Rectangular
            expected_h_modules = version
            expected_v_modules = int(version / self.width_height_ratio)
            expected_size_desc = f"{expected_h_modules}x{expected_v_modules}"
        else:  # Square (QR code)
            expected_size = 21 + (version - 1) * 4
            expected_size_desc = f"{expected_size}x{expected_size}"
        
        result = {
            'corrected_image': corrected_pattern,
            'version': version,
            'expected_modules': expected_size_desc,
            'output_dimensions': (output_width, output_height),
            'width_height_ratio': self.width_height_ratio,
            'fourth_corner': self.calculate_fourth_corner(finder_patterns),
            'debug_info': self.debug_info.copy()
        }
        
        self.add_debug(f"Pattern extraction complete: version {version}, size {expected_size_desc}, ratio {self.width_height_ratio:.2f}")
        return result

def test_qr_data_reader():
    """Test function for QR Data Reader with different ratios"""
    print("🔍 Testing QR Data Reader - Flexible Ratios")
    
    # Mock finder patterns for testing
    test_patterns = [
        {'center': (100, 100)},  # top-left
        {'center': (300, 100)},  # top-right  
        {'center': (100, 300)}   # bottom-left
    ]
    
    # Test different ratios
    test_ratios = [
        (1.0, "Square (QR code)"),
        (1.5, "3:2 Rectangle (wide)"),
        (0.75, "3:4 Rectangle (tall)"),
        (2.0, "2:1 Rectangle (very wide)")
    ]
    
    for ratio, description in test_ratios:
        print(f"\n📐 Testing {description} (ratio: {ratio})")
        reader = QRDataReader(width_height_ratio=ratio)
        
        # Test 4th corner calculation
        fourth_corner = reader.calculate_fourth_corner(test_patterns)
        print(f"   📍 4th corner: {fourth_corner}")
        
        # Test corner ordering
        if fourth_corner:
            ordered = reader.order_corners(test_patterns, fourth_corner)
            print(f"   � Ordered corners: {ordered}")
        
        # Calculate expected output dimensions
        output_width = 300
        output_height = int(output_width / ratio)
        print(f"   📏 Output dimensions: {output_width}x{output_height}")
    
    print("\n✅ QR Data Reader flexible ratio test complete!")

if __name__ == "__main__":
    test_qr_data_reader()
