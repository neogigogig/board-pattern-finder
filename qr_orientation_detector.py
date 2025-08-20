#!/usr/bin/env python3
"""
QR Code Orientation Detector
Determines the orientation and rotation angle of QR codes based on finder pattern positions
"""

import cv2
import numpy as np
import math
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class QROrientationDetector:
    def __init__(self):
        """Initialize QR Orientation Detector"""
        self.debug_info = []
        
    def reset_debug(self):
        """Reset debug information"""
        self.debug_info = []
        
    def add_debug(self, message, data=None):
        """Add debug information"""
        self.debug_info.append({
            'message': message,
            'data': data
        })
    
    def identify_finder_pattern_positions(self, finder_patterns: List[Dict]) -> Optional[Dict]:
        """
        Identify which finder pattern is which (top-left, top-right, bottom-left)
        based on QR code standard geometry
        
        Args:
            finder_patterns: List of finder pattern dictionaries with 'center' coordinates
            
        Returns:
            Dictionary with identified positions or None if not possible
        """
        if len(finder_patterns) < 3:
            self.add_debug("Need at least 3 finder patterns for orientation detection")
            return None
        
        # Extract centers as (x, y) tuples
        centers = [(p['center']['x'] if isinstance(p['center'], dict) else p['center'][0],
                   p['center']['y'] if isinstance(p['center'], dict) else p['center'][1]) 
                  for p in finder_patterns[:3]]
        
        self.add_debug(f"Analyzing centers: {centers}")
        
        # Calculate centroid
        centroid_x = sum(c[0] for c in centers) / 3
        centroid_y = sum(c[1] for c in centers) / 3
        centroid = (centroid_x, centroid_y)
        
        self.add_debug(f"Centroid: {centroid}")
        
        # Calculate distances from centroid to each pattern
        distances = []
        for i, center in enumerate(centers):
            dist = math.sqrt((center[0] - centroid_x)**2 + (center[1] - centroid_y)**2)
            distances.append((i, dist, center))
        
        # Sort by distance to find the pattern arrangement
        distances.sort(key=lambda x: x[1])
        
        # In a standard QR code orientation:
        # - Two patterns are closer to each other (top-left and top-right, or top-left and bottom-left)
        # - One pattern is farther away (bottom-left or top-right)
        
        # Calculate all pairwise distances
        pairwise_distances = []
        for i in range(3):
            for j in range(i+1, 3):
                dist = math.sqrt((centers[i][0] - centers[j][0])**2 + (centers[i][1] - centers[j][1])**2)
                pairwise_distances.append((i, j, dist))
        
        # Sort by distance to find the closest pair
        pairwise_distances.sort(key=lambda x: x[2])
        
        # The two closest patterns are either:
        # 1. Top-left and top-right (horizontal pair)
        # 2. Top-left and bottom-left (vertical pair)
        closest_pair = pairwise_distances[0]
        pattern1_idx, pattern2_idx = closest_pair[0], closest_pair[1]
        
        # The third pattern is the remaining one
        remaining_idx = None
        for i in range(3):
            if i not in [pattern1_idx, pattern2_idx]:
                remaining_idx = i
                break
        
        pattern1 = centers[pattern1_idx]
        pattern2 = centers[pattern2_idx]
        pattern3 = centers[remaining_idx]
        
        # Determine if the closest pair is horizontal or vertical
        dx = abs(pattern1[0] - pattern2[0])
        dy = abs(pattern1[1] - pattern2[1])
        
        if dx > dy:
            # Horizontal pair - these are top-left and top-right
            # The leftmost is top-left, rightmost is top-right
            if pattern1[0] < pattern2[0]:
                top_left, top_right = pattern1, pattern2
                top_left_idx, top_right_idx = pattern1_idx, pattern2_idx
            else:
                top_left, top_right = pattern2, pattern1
                top_left_idx, top_right_idx = pattern2_idx, pattern1_idx
            
            bottom_left = pattern3
            bottom_left_idx = remaining_idx
            
        else:
            # Vertical pair - these are top-left and bottom-left
            # The topmost is top-left, bottommost is bottom-left
            if pattern1[1] < pattern2[1]:
                top_left, bottom_left = pattern1, pattern2
                top_left_idx, bottom_left_idx = pattern1_idx, pattern2_idx
            else:
                top_left, bottom_left = pattern2, pattern1
                top_left_idx, bottom_left_idx = pattern2_idx, pattern1_idx
            
            top_right = pattern3
            top_right_idx = remaining_idx
        
        # Create result with original pattern objects
        result = {
            'top_left': {
                'pattern': finder_patterns[top_left_idx],
                'center': top_left,
                'index': top_left_idx
            },
            'top_right': {
                'pattern': finder_patterns[top_right_idx],
                'center': top_right,
                'index': top_right_idx
            },
            'bottom_left': {
                'pattern': finder_patterns[bottom_left_idx],
                'center': bottom_left,
                'index': bottom_left_idx
            }
        }
        
        self.add_debug(f"Identified positions: TL={top_left}, TR={top_right}, BL={bottom_left}")
        
        return result
    
    def calculate_orientation_angles(self, positions: Dict) -> Dict:
        """
        Calculate various orientation angles of the QR code
        
        Args:
            positions: Dictionary with identified finder pattern positions
            
        Returns:
            Dictionary with calculated angles
        """
        tl = positions['top_left']['center']
        tr = positions['top_right']['center']
        bl = positions['bottom_left']['center']
        
        # Calculate angles
        angles = {}
        
        # 1. Top edge angle (how much the QR code is rotated)
        top_dx = tr[0] - tl[0]
        top_dy = tr[1] - tl[1]
        top_angle_rad = math.atan2(top_dy, top_dx)
        top_angle_deg = math.degrees(top_angle_rad)
        angles['top_edge_angle'] = top_angle_deg
        
        # 2. Left edge angle
        left_dx = bl[0] - tl[0]
        left_dy = bl[1] - tl[1]
        left_angle_rad = math.atan2(left_dy, left_dx)
        left_angle_deg = math.degrees(left_angle_rad)
        angles['left_edge_angle'] = left_angle_deg
        
        # 3. Primary rotation angle (most meaningful for QR orientation)
        # This is the angle the QR code is rotated from its "standard" orientation
        primary_rotation = top_angle_deg
        
        # Normalize to [-180, 180] range
        while primary_rotation > 180:
            primary_rotation -= 360
        while primary_rotation < -180:
            primary_rotation += 360
            
        angles['primary_rotation'] = primary_rotation
        
        # 4. Quadrant-based rotation (0, 90, 180, 270 degrees)
        quadrant_rotation = round(primary_rotation / 90) * 90
        angles['quadrant_rotation'] = quadrant_rotation
        
        # 5. Skew angles (how much the QR code is skewed from a perfect rectangle)
        expected_angle_diff = 90  # Left edge should be 90° from top edge
        actual_angle_diff = left_angle_deg - top_angle_deg
        
        # Normalize angle difference
        while actual_angle_diff > 180:
            actual_angle_diff -= 360
        while actual_angle_diff < -180:
            actual_angle_diff += 360
            
        skew = abs(actual_angle_diff - expected_angle_diff)
        if skew > 180:
            skew = 360 - skew
            
        angles['skew_angle'] = min(skew, 180 - skew)
        
        self.add_debug(f"Calculated angles: {angles}")
        
        return angles
    
    def get_orientation_description(self, angles: Dict) -> str:
        """
        Get a human-readable description of the QR code orientation
        
        Args:
            angles: Dictionary with calculated angles
            
        Returns:
            String description of orientation
        """
        rotation = angles['primary_rotation']
        skew = angles['skew_angle']
        
        # Determine rotation description
        if abs(rotation) < 15:
            rotation_desc = "upright"
        elif abs(rotation - 90) < 15 or abs(rotation + 270) < 15:
            rotation_desc = "rotated 90° clockwise"
        elif abs(rotation - 180) < 15 or abs(rotation + 180) < 15:
            rotation_desc = "upside down"
        elif abs(rotation - 270) < 15 or abs(rotation + 90) < 15:
            rotation_desc = "rotated 90° counter-clockwise"
        else:
            rotation_desc = f"rotated {rotation:.1f}°"
        
        # Determine skew description
        if skew < 5:
            skew_desc = "well-aligned"
        elif skew < 15:
            skew_desc = "slightly skewed"
        elif skew < 30:
            skew_desc = "moderately skewed"
        else:
            skew_desc = "heavily skewed"
        
        return f"QR code is {rotation_desc} and {skew_desc} (skew: {skew:.1f}°)"
    
    def detect_orientation(self, finder_patterns: List[Dict]) -> Optional[Dict]:
        """
        Complete orientation detection for a QR code
        
        Args:
            finder_patterns: List of finder pattern dictionaries
            
        Returns:
            Complete orientation analysis or None if detection fails
        """
        self.reset_debug()
        
        # Identify finder pattern positions
        positions = self.identify_finder_pattern_positions(finder_patterns)
        if not positions:
            return None
        
        # Calculate orientation angles
        angles = self.calculate_orientation_angles(positions)
        
        # Get description
        description = self.get_orientation_description(angles)
        
        # Calculate fourth corner for completeness
        tl = positions['top_left']['center']
        tr = positions['top_right']['center']
        bl = positions['bottom_left']['center']
        
        # Fourth corner calculation using parallelogram rule
        fourth_corner = (
            tl[0] + bl[0] - tr[0],
            tl[1] + bl[1] - tr[1]
        )
        
        return {
            'positions': positions,
            'angles': angles,
            'description': description,
            'fourth_corner': fourth_corner,
            'debug_info': self.debug_info.copy()
        }
    
    def visualize_orientation(self, image: np.ndarray, orientation_data: Dict, 
                            output_path: str = None) -> None:
        """
        Create a visualization showing QR code orientation analysis
        
        Args:
            image: Original image
            orientation_data: Orientation analysis data
            output_path: Path to save visualization (optional)
        """
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # Display image
        if len(image.shape) == 3:
            ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            ax.imshow(image, cmap='gray')
        
        positions = orientation_data['positions']
        angles = orientation_data['angles']
        fourth_corner = orientation_data['fourth_corner']
        
        # Color scheme for positions
        colors = {
            'top_left': 'red',
            'top_right': 'blue', 
            'bottom_left': 'green'
        }
        
        labels = {
            'top_left': 'TL',
            'top_right': 'TR',
            'bottom_left': 'BL'
        }
        
        # Draw finder patterns
        for pos_name, pos_data in positions.items():
            center = pos_data['center']
            color = colors[pos_name]
            label = labels[pos_name]
            
            # Draw circle
            circle = patches.Circle(center, radius=20, color=color, fill=True, alpha=0.7)
            ax.add_patch(circle)
            
            # Add label
            ax.text(center[0], center[1] - 30, label, color=color, fontsize=14, 
                   fontweight='bold', ha='center', va='center',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Draw fourth corner
        fourth_circle = patches.Circle(fourth_corner, radius=20, color='purple', 
                                     fill=True, alpha=0.7, linestyle='--')
        ax.add_patch(fourth_circle)
        ax.text(fourth_corner[0], fourth_corner[1] - 30, 'BR', color='purple', 
               fontsize=14, fontweight='bold', ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Draw orientation lines
        tl = positions['top_left']['center']
        tr = positions['top_right']['center']
        bl = positions['bottom_left']['center']
        
        # Top edge (shows primary rotation)
        ax.plot([tl[0], tr[0]], [tl[1], tr[1]], 'orange', linewidth=4, alpha=0.8, label='Top Edge')
        
        # Left edge
        ax.plot([tl[0], bl[0]], [tl[1], bl[1]], 'cyan', linewidth=4, alpha=0.8, label='Left Edge')
        
        # Complete rectangle
        all_corners = [tl, tr, fourth_corner, bl, tl]  # Close the rectangle
        xs, ys = zip(*all_corners)
        ax.plot(xs, ys, 'yellow', linewidth=3, alpha=0.6, linestyle='--', label='QR Rectangle')
        
        # Add orientation information text
        info_text = f"""QR Code Orientation Analysis:
        
Primary Rotation: {angles['primary_rotation']:.1f}°
Quadrant Rotation: {angles['quadrant_rotation']}°
Skew Angle: {angles['skew_angle']:.1f}°

Top Edge Angle: {angles['top_edge_angle']:.1f}°
Left Edge Angle: {angles['left_edge_angle']:.1f}°

{orientation_data['description']}"""
        
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.9))
        
        # Add arrow showing rotation direction
        center_x = (tl[0] + tr[0] + bl[0]) / 3
        center_y = (tl[1] + tr[1] + bl[1]) / 3
        
        # Draw rotation arrow
        rotation_rad = math.radians(angles['primary_rotation'])
        arrow_length = 50
        arrow_end_x = center_x + arrow_length * math.cos(rotation_rad)
        arrow_end_y = center_y + arrow_length * math.sin(rotation_rad)
        
        ax.annotate('', xy=(arrow_end_x, arrow_end_y), xytext=(center_x, center_y),
                   arrowprops=dict(arrowstyle='->', lw=3, color='red', alpha=0.8))
        ax.text(center_x, center_y - 70, f'Rotation: {angles["primary_rotation"]:.1f}°', 
               ha='center', va='center', fontsize=12, fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        ax.set_title('QR Code Orientation Analysis', fontsize=16, fontweight='bold')
        ax.axis('off')
        ax.legend(loc='upper right')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✅ Orientation visualization saved: {output_path}")
        
        plt.show()

def test_orientation_detection():
    """Test the orientation detector with sample data"""
    print("🧭 Testing QR Code Orientation Detection")
    print("=" * 50)
    
    # Sample finder patterns (simulated)
    test_patterns = [
        {'center': (100, 100), 'size': 30},  # Top-left
        {'center': (300, 120), 'size': 30},  # Top-right (slightly rotated)
        {'center': (80, 300), 'size': 30}    # Bottom-left
    ]
    
    detector = QROrientationDetector()
    orientation_data = detector.detect_orientation(test_patterns)
    
    if orientation_data:
        print("✅ Orientation Detection Successful!")
        print(f"Description: {orientation_data['description']}")
        print(f"Primary Rotation: {orientation_data['angles']['primary_rotation']:.1f}°")
        print(f"Skew Angle: {orientation_data['angles']['skew_angle']:.1f}°")
        print(f"Fourth Corner: {orientation_data['fourth_corner']}")
        
        print("\nDetailed Angles:")
        for angle_name, angle_value in orientation_data['angles'].items():
            print(f"  {angle_name}: {angle_value:.1f}°")
        
        print("\nDebug Information:")
        for debug_item in orientation_data['debug_info']:
            print(f"  {debug_item['message']}")
    else:
        print("❌ Orientation detection failed")

if __name__ == "__main__":
    test_orientation_detection()
