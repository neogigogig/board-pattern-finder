#!/usr/bin/env python3
"""
Finder Pattern Based QR Orientation Detector
Uses our own finder pattern detection, but applies the proper QR orientation method
Based on: https://temugeb.github.io/python/computer_vision/2021/06/15/QR-Code_Orientation.html

This detector:
1. Uses our existing finder pattern detection to locate the 3 patterns
2. Identifies which pattern is which (BL, TL, TR) using geometric analysis
3. Calculates the 4th corner (BR) using parallelogram construction
4. Applies proper QR coordinate system orientation (Point #1 as origin, etc.)
5. Uses solvePnP for accurate 3D pose estimation
"""

import cv2 as cv
import numpy as np
import math
import os
import json
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt

class FinderPatternOrientationDetector:
    def __init__(self):
        """Initialize Finder Pattern Based QR Orientation Detector"""
        self.debug_info = []
        
        # QR coordinate system based on proper method
        # Point ordering for solvePnP (from the article):
        # Point #1 (origin): bottom-left finder pattern
        # Point #2 (Y direction): top-left finder pattern  
        # Point #3 (X+Y direction): top-right corner (calculated)
        # Point #4 (X direction): bottom-right corner (calculated)
        self.qr_3d_points = np.array([[0,0,0],  # BL (origin)
                                     [0,1,0],   # TL (Y direction)
                                     [1,1,0],   # TR (X+Y direction)
                                     [1,0,0]],  # BR (X direction)
                                    dtype='float32').reshape((4,1,3))
        
        # Default camera matrix (estimated for typical camera)
        self.camera_matrix = np.array([[800, 0, 320],
                                      [0, 800, 240],
                                      [0, 0, 1]], dtype='float32')
        
        self.dist_coeffs = np.zeros((4,1))  # No distortion
        
    def reset_debug(self):
        """Reset debug information"""
        self.debug_info = []
        
    def add_debug(self, message, data=None):
        """Add debug information"""
        self.debug_info.append({
            'message': message,
            'data': data
        })
    
    def identify_finder_patterns_geometry(self, patterns: List[Dict]) -> Optional[Dict]:
        """
        Identify the 3 finder patterns and assign them to BL, TL, TR positions
        Returns pattern assignment with geometry
        """
        if len(patterns) < 3:
            self.add_debug(f"Not enough patterns found: {len(patterns)} < 3")
            return None
        
        # If we have more than 3 patterns, try different combinations
        # to find the best 3 that form a valid QR triangle
        best_assignment = None
        best_score = float('-inf')
        
        import itertools
        
        # Try all combinations of 3 patterns from available patterns
        for pattern_combo in itertools.combinations(range(len(patterns)), 3):
            selected_patterns = [patterns[i] for i in pattern_combo]
            centers = [(p['center']['x'], p['center']['y']) for p in selected_patterns]
            
            # Find best assignment for this combination
            assignment = self._find_best_pattern_assignment(centers, selected_patterns)
            
            if assignment and assignment['assignment_score'] > best_score:
                best_score = assignment['assignment_score']
                best_assignment = assignment
                self.add_debug(f"Better combination found with patterns {pattern_combo}, score: {best_score:.2f}")
        
        if best_assignment is None:
            self.add_debug("Could not determine valid pattern assignment")
            return None
        
        self.add_debug(f"Final best assignment score: {best_score:.2f}")
        return best_assignment
    
    def _find_best_pattern_assignment(self, centers: List[Tuple], patterns: List[Dict]) -> Optional[Dict]:
        """
        Find the best assignment of 3 finder patterns to BL, TL, TR
        Uses QR code geometric constraints
        """
        best_score = float('-inf')
        best_assignment = None
        
        # Try all 6 possible assignments (3! = 6 permutations)
        import itertools
        
        self.add_debug(f"Evaluating assignments for centers: {centers}")
        
        for i, perm in enumerate(itertools.permutations(range(3))):
            bl_idx, tl_idx, tr_idx = perm
            
            bl_center = centers[bl_idx]
            tl_center = centers[tl_idx]
            tr_center = centers[tr_idx]
            
            # Score this assignment based on QR geometry
            score = self._score_pattern_assignment(bl_center, tl_center, tr_center)
            
            self.add_debug(f"Assignment {i+1}: BL{bl_center} TL{tl_center} TR{tr_center} -> Score: {score:.2f}")
            
            if score > best_score:
                best_score = score
                best_assignment = {
                    'bottom_left': {
                        'pattern': patterns[bl_idx],
                        'center': bl_center,
                        'index': bl_idx
                    },
                    'top_left': {
                        'pattern': patterns[tl_idx],
                        'center': tl_center,
                        'index': tl_idx
                    },
                    'top_right': {
                        'pattern': patterns[tr_idx],
                        'center': tr_center,
                        'index': tr_idx
                    },
                    'assignment_score': score
                }
        
        if best_assignment:
            self.add_debug(f"Best assignment: BL{best_assignment['bottom_left']['center']} "
                          f"TL{best_assignment['top_left']['center']} "
                          f"TR{best_assignment['top_right']['center']} "
                          f"Score: {best_score:.2f}")
        
        return best_assignment
    
    def _score_pattern_assignment(self, bl: Tuple, tl: Tuple, tr: Tuple) -> float:
        """
        Score a potential BL-TL-TR assignment based on QR code geometry
        Higher score = better assignment
        
        For a QR code:
        - TL-TR edge should be roughly horizontal to the top edge
        - TL-BL edge should be roughly vertical to the left edge
        - The triangle should form a right angle at TL
        - BL should be "below" the TL-TR line
        """
        score = 0.0
        
        # Calculate vectors
        tl_to_tr = (tr[0] - tl[0], tr[1] - tl[1])  # Top edge vector
        tl_to_bl = (bl[0] - tl[0], bl[1] - tl[1])  # Left edge vector
        
        # Calculate magnitudes
        top_mag = math.sqrt(tl_to_tr[0]**2 + tl_to_tr[1]**2)
        left_mag = math.sqrt(tl_to_bl[0]**2 + tl_to_bl[1]**2)
        
        if top_mag == 0 or left_mag == 0:
            return -100.0  # Invalid configuration
        
        # 1. Check angle between TL-TR and TL-BL vectors (should be close to 90°)
        dot_product = tl_to_tr[0] * tl_to_bl[0] + tl_to_tr[1] * tl_to_bl[1]
        cos_angle = dot_product / (top_mag * left_mag)
        cos_angle = max(-1, min(1, cos_angle))
        angle_deg = math.degrees(math.acos(cos_angle))
        
        # Reward angles close to 90°
        angle_error = abs(angle_deg - 90.0)
        if angle_error < 15.0:  # Very good angle
            score += 40.0 - angle_error * 2
        elif angle_error < 30.0:  # Acceptable angle
            score += 20.0 - angle_error
        else:  # Poor angle
            score -= angle_error / 2
        
        # 2. Check aspect ratio (QR should be roughly square)
        aspect_ratio = max(top_mag, left_mag) / min(top_mag, left_mag)
        if aspect_ratio < 1.5:  # Very square
            score += 30.0
        elif aspect_ratio < 2.0:  # Reasonably square
            score += 20.0 - (aspect_ratio - 1) * 20
        elif aspect_ratio < 3.0:  # Acceptable
            score += 10.0 - (aspect_ratio - 2) * 10
        else:  # Too rectangular
            score -= aspect_ratio * 5
        
        # 3. Check if BL is on the correct side of the TL-TR line
        # Cross product to determine which side of TL-TR line BL is on
        cross_product = tl_to_tr[0] * tl_to_bl[1] - tl_to_tr[1] * tl_to_bl[0]
        
        # For a standard QR orientation, BL should be on the "positive" side
        # This helps distinguish correct orientation
        if cross_product > 0:
            score += 25.0
        else:
            score += 10.0  # Still possible, just less likely
        
        # 4. Prefer more compact triangles (smaller perimeter relative to area)
        # This helps avoid selecting outlier patterns
        triangle_area = abs(cross_product) / 2
        perimeter = top_mag + left_mag + math.sqrt((bl[0] - tr[0])**2 + (bl[1] - tr[1])**2)
        
        if triangle_area > 0:
            compactness = triangle_area / (perimeter**2) * 1000  # Scale for readability
            score += compactness * 10
        
        # 5. Geometric consistency check
        # Calculate the fourth corner and check if it forms a reasonable parallelogram
        br_calc = (bl[0] + tl_to_tr[0], bl[1] + tl_to_tr[1])
        bl_to_br = (br_calc[0] - bl[0], br_calc[1] - bl[1])
        tr_to_br = (br_calc[0] - tr[0], br_calc[1] - tr[1])
        
        # Check if opposite sides are parallel (vectors should be similar)
        side_similarity = abs(tl_to_tr[0] * bl_to_br[0] + tl_to_tr[1] * bl_to_br[1]) / (top_mag * math.sqrt(bl_to_br[0]**2 + bl_to_br[1]**2) + 1e-6)
        score += side_similarity * 15
        
        return score
    
    def calculate_fourth_corner(self, pattern_assignment: Dict) -> Tuple[float, float]:
        """
        Calculate the 4th corner (bottom-right) using parallelogram construction
        BR = BL + (TR - TL)
        """
        bl = pattern_assignment['bottom_left']['center']
        tl = pattern_assignment['top_left']['center']
        tr = pattern_assignment['top_right']['center']
        
        # Vector from TL to TR
        tl_to_tr = (tr[0] - tl[0], tr[1] - tl[1])
        
        # BR = BL + vector(TL->TR)
        br_x = bl[0] + tl_to_tr[0]
        br_y = bl[1] + tl_to_tr[1]
        
        br_center = (br_x, br_y)
        
        self.add_debug(f"Fourth corner calculation: BL{bl} + TL->TR{tl_to_tr} = BR{br_center}")
        
        return br_center
    
    def calculate_qr_orientation_with_solvepnp(self, pattern_assignment: Dict, br_corner: Tuple) -> Optional[Dict]:
        """
        Calculate QR orientation using solvePnP method (proper 3D pose estimation)
        """
        bl = pattern_assignment['bottom_left']['center']
        tl = pattern_assignment['top_left']['center'] 
        tr = pattern_assignment['top_right']['center']
        br = br_corner
        
        # Prepare 2D points in the correct order for solvePnP
        # According to the article's coordinate system:
        # Point #1: BL (origin)
        # Point #2: TL (Y direction)
        # Point #3: TR (X+Y direction)
        # Point #4: BR (X direction)
        points_2d = np.array([bl, tl, tr, br], dtype='float32')
        
        self.add_debug(f"2D points for solvePnP: BL{bl}, TL{tl}, TR{tr}, BR{br}")
        
        # Use solvePnP to get rotation and translation
        ret, rvec, tvec = cv.solvePnP(self.qr_3d_points, points_2d, 
                                     self.camera_matrix, self.dist_coeffs)
        
        if not ret:
            self.add_debug("solvePnP failed")
            return None
        
        # Convert rotation vector to rotation matrix
        rotation_matrix, _ = cv.Rodrigues(rvec)
        
        # Calculate orientation angles from rotation matrix
        orientation = self._extract_orientation_angles(rotation_matrix)
        
        # Calculate 3D axes for visualization
        unit_axes = np.array([[0,0,0], [1,0,0], [0,1,0], [0,0,1]], 
                           dtype='float32').reshape((4,1,3))
        axis_points, _ = cv.projectPoints(unit_axes, rvec, tvec,
                                        self.camera_matrix, self.dist_coeffs)
        axis_points = axis_points.reshape((4,2))
        
        result = {
            'corners': {
                'bottom_left': bl,
                'top_left': tl,
                'top_right': tr,
                'bottom_right': br
            },
            'rotation_vector': rvec.flatten().tolist(),
            'translation_vector': tvec.flatten().tolist(),
            'rotation_matrix': rotation_matrix.tolist(),
            'orientation': orientation,
            'axis_points': axis_points.tolist(),
            'assignment_score': pattern_assignment['assignment_score'],
            'method': 'finder_patterns_solvepnp'
        }
        
        self.add_debug("Orientation calculated successfully using solvePnP", orientation)
        
        return result
    
    def _extract_orientation_angles(self, R) -> Dict:
        """
        Extract orientation angles from rotation matrix
        """
        # Extract Euler angles (ZYX convention)
        # Main QR rotation is around Z-axis (yaw)
        yaw = math.atan2(R[1,0], R[0,0])
        pitch = math.atan2(-R[2,0], math.sqrt(R[2,1]**2 + R[2,2]**2))
        roll = math.atan2(R[2,1], R[2,2])
        
        # Convert to degrees
        yaw_deg = math.degrees(yaw)
        pitch_deg = math.degrees(pitch)
        roll_deg = math.degrees(roll)
        
        # Main QR rotation (in image plane)
        qr_rotation = yaw_deg
        if qr_rotation < 0:
            qr_rotation += 360
        
        return {
            'qr_rotation_deg': qr_rotation,
            'yaw_deg': yaw_deg,
            'pitch_deg': pitch_deg,
            'roll_deg': roll_deg,
            'yaw_rad': yaw,
            'pitch_rad': pitch,
            'roll_rad': roll
        }
    
    def get_orientation_description(self, orientation: Dict) -> str:
        """Get human-readable orientation description"""
        rotation = orientation['qr_rotation_deg']
        
        if rotation < 15 or rotation > 345:
            desc = "upright (0°)"
        elif 75 < rotation < 105:
            desc = "rotated 90° clockwise"
        elif 165 < rotation < 195:
            desc = "upside down (180°)"
        elif 255 < rotation < 285:
            desc = "rotated 90° counter-clockwise (270°)"
        else:
            desc = f"rotated {rotation:.1f}°"
        
        return f"QR code is {desc}"
    
    def analyze_qr_from_finder_patterns(self, finder_patterns: List[Dict]) -> Optional[Dict]:
        """
        Complete QR orientation analysis from finder patterns
        """
        self.reset_debug()
        
        # Step 1: Identify which pattern is which (BL, TL, TR)
        pattern_assignment = self.identify_finder_patterns_geometry(finder_patterns)
        if pattern_assignment is None:
            return None
        
        # Step 2: Calculate 4th corner (BR)
        br_corner = self.calculate_fourth_corner(pattern_assignment)
        
        # Step 3: Use solvePnP for proper 3D orientation
        orientation_result = self.calculate_qr_orientation_with_solvepnp(pattern_assignment, br_corner)
        if orientation_result is None:
            return None
        
        # Add debug info
        orientation_result['debug_info'] = self.debug_info.copy()
        
        return orientation_result
    
    def visualize_finder_pattern_orientation(self, image, result, output_path=None):
        """
        Create visualization showing finder pattern based QR orientation
        """
        if result is None:
            print("No result to visualize")
            return None
        
        # Convert image for matplotlib
        if len(image.shape) == 3:
            display_image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        else:
            display_image = cv.cvtColor(image, cv.COLOR_GRAY2RGB)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Left plot: Finder pattern identification
        ax1.imshow(display_image)
        ax1.set_title('Finder Pattern QR Analysis\nBL → TL → TR → BR', fontsize=14, fontweight='bold')
        
        corners = result['corners']
        
        # Draw finder patterns (BL, TL, TR are detected, BR is calculated)
        finder_colors = {'bottom_left': 'blue', 'top_left': 'green', 'top_right': 'red'}
        calculated_color = 'purple'
        
        # Draw detected finder patterns
        for corner_name in ['bottom_left', 'top_left', 'top_right']:
            point = corners[corner_name]
            color = finder_colors[corner_name]
            ax1.scatter(point[0], point[1], c=color, s=1000, alpha=0.8, 
                       marker='o', edgecolors='black', linewidth=3)
        
        # Draw calculated BR corner
        br_point = corners['bottom_right']
        ax1.scatter(br_point[0], br_point[1], c=calculated_color, s=1000, alpha=0.8,
                   marker='s', edgecolors='black', linewidth=3)
        
        # Add labels
        labels = {
            'bottom_left': 'BL\n(Finder)',
            'top_left': 'TL\n(Finder)', 
            'top_right': 'TR\n(Finder)',
            'bottom_right': 'BR\n(Calc)'
        }
        
        offset = 50
        for corner_name, point in corners.items():
            if corner_name == 'bottom_right':
                color = calculated_color
            else:
                color = finder_colors[corner_name]
            
            label = labels[corner_name]
            ax1.text(point[0], point[1] + offset, label, ha='center', va='center',
                    bbox={'boxstyle': 'round,pad=0.3', 'facecolor': color, 'alpha': 0.8},
                    fontsize=11, fontweight='bold', color='white')
        
        # Draw QR rectangle
        rect_points = [corners['bottom_left'], corners['bottom_right'],
                      corners['top_right'], corners['top_left'], corners['bottom_left']]
        rect_x = [p[0] for p in rect_points]
        rect_y = [p[1] for p in rect_points]
        ax1.plot(rect_x, rect_y, 'yellow', linewidth=4, alpha=0.9)
        
        ax1.set_xlim(0, display_image.shape[1])
        ax1.set_ylim(display_image.shape[0], 0)
        ax1.axis('off')
        
        # Right plot: 3D coordinate system
        ax2.imshow(display_image)
        ax2.set_title('QR 3D Coordinate System\n(solvePnP Method)', fontsize=14, fontweight='bold')
        
        # Draw QR rectangle
        ax2.plot(rect_x, rect_y, 'yellow', linewidth=4, alpha=0.9)
        
        # Draw 3D axes
        axis_points = np.array(result['axis_points'])
        origin = axis_points[0]
        x_axis = axis_points[1]
        y_axis = axis_points[2]
        z_axis = axis_points[3]
        
        # X-axis (red)
        ax2.arrow(origin[0], origin[1], x_axis[0] - origin[0], x_axis[1] - origin[1],
                 head_width=25, head_length=35, fc='red', ec='red', alpha=0.9, linewidth=4)
        ax2.text(x_axis[0], x_axis[1], 'X', fontsize=16, fontweight='bold', color='red')
        
        # Y-axis (green)
        ax2.arrow(origin[0], origin[1], y_axis[0] - origin[0], y_axis[1] - origin[1],
                 head_width=25, head_length=35, fc='green', ec='green', alpha=0.9, linewidth=4)
        ax2.text(y_axis[0], y_axis[1], 'Y', fontsize=16, fontweight='bold', color='green')
        
        # Z-axis (blue) 
        ax2.arrow(origin[0], origin[1], z_axis[0] - origin[0], z_axis[1] - origin[1],
                 head_width=25, head_length=35, fc='blue', ec='blue', alpha=0.9, linewidth=4)
        ax2.text(z_axis[0], z_axis[1], 'Z', fontsize=16, fontweight='bold', color='blue')
        
        # Add orientation information
        orientation = result['orientation']
        description = self.get_orientation_description(orientation)
        score = result['assignment_score']
        
        info_text = f"Finder Pattern Analysis\n{'='*22}\nAssignment Score: {score:.1f}\nQR Rotation: {orientation['qr_rotation_deg']:.1f}°\nYaw: {orientation['yaw_deg']:.1f}°\nPitch: {orientation['pitch_deg']:.1f}°\nRoll: {orientation['roll_deg']:.1f}°\n\n{description}"
        
        ax2.text(0.02, 0.98, info_text, transform=ax2.transAxes,
                bbox={'boxstyle': 'round,pad=0.5', 'facecolor': 'white', 'alpha': 0.95},
                fontsize=11, va='top', ha='left')
        
        ax2.set_xlim(0, display_image.shape[1])
        ax2.set_ylim(display_image.shape[0], 0)
        ax2.axis('off')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Finder pattern orientation visualization saved to: {output_path}")
        
        plt.show()
        
        return fig

def analyze_finder_pattern_orientation():
    """
    Analyze QR orientation using our finder pattern detection + proper orientation method
    """
    print("Finder Pattern Based QR Orientation Detection")
    print("=" * 55)
    print("Method: Our finder pattern detection + proper solvePnP orientation")
    print("Based on: https://temugeb.github.io/python/computer_vision/2021/06/15/QR-Code_Orientation.html")
    print("=" * 55)
    
    detector = FinderPatternOrientationDetector()
    
    # Analyze images from 3-finder-pattern folder
    three_pattern_dir = "data-qr-ratio-finder/3-finder-pattern"
    if not os.path.exists(three_pattern_dir):
        print(f"Error: Directory not found: {three_pattern_dir}")
        return
    
    image_files = [f for f in os.listdir(three_pattern_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print("No image files found")
        return
    
    print(f"Found {len(image_files)} images to analyze")
    
    # Check for existing detection results
    results_dir = "results/enhanced-strict-qr-results"
    all_results = {}
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processing: {image_file}")
        print("-" * 50)
        
        image_path = os.path.join(three_pattern_dir, image_file)
        
        # Look for existing finder pattern detection results
        result_file = os.path.join(results_dir, f"{os.path.splitext(image_file)[0]}_results.json")
        
        if os.path.exists(result_file):
            # Load existing detection results
            with open(result_file, 'r') as f:
                detection_data = json.load(f)
            
            patterns = detection_data.get('patterns', [])
            print(f"Found {len(patterns)} finder patterns in existing results")
            
            if len(patterns) >= 3:
                # Use best 3 patterns
                sorted_patterns = sorted(patterns, key=lambda p: p.get('score', 0), reverse=True)
                best_patterns = sorted_patterns[:3]
                
                scores_str = ", ".join([f"{p.get('score', 0):.3f}" for p in best_patterns])
                print(f"Using top 3 patterns (scores: {scores_str})")
                
                # Analyze orientation using our method
                result = detector.analyze_qr_from_finder_patterns(best_patterns)
                
                if result:
                    # Load image for visualization
                    image = cv.imread(image_path)
                    if image is not None:
                        # Create visualization
                        output_path = f"finder_pattern_orientation_{i}.png"
                        detector.visualize_finder_pattern_orientation(image, result, output_path)
                    
                    # Store results
                    all_results[image_file] = result
                    
                    # Print summary
                    orientation = result['orientation']
                    description = detector.get_orientation_description(orientation)
                    
                    print(f"✅ QR Orientation Analysis Results:")
                    print(f"   BL: ({result['corners']['bottom_left'][0]:.1f}, {result['corners']['bottom_left'][1]:.1f}) [Finder Pattern]")
                    print(f"   TL: ({result['corners']['top_left'][0]:.1f}, {result['corners']['top_left'][1]:.1f}) [Finder Pattern]")
                    print(f"   TR: ({result['corners']['top_right'][0]:.1f}, {result['corners']['top_right'][1]:.1f}) [Finder Pattern]")
                    print(f"   BR: ({result['corners']['bottom_right'][0]:.1f}, {result['corners']['bottom_right'][1]:.1f}) [Calculated]")
                    print(f"   Assignment Score: {result['assignment_score']:.2f}")
                    print(f"   QR Rotation: {orientation['qr_rotation_deg']:.1f}°")
                    print(f"   3D Pose - Yaw: {orientation['yaw_deg']:.1f}°, Pitch: {orientation['pitch_deg']:.1f}°, Roll: {orientation['roll_deg']:.1f}°")
                    print(f"   Description: {description}")
                else:
                    print("❌ Could not determine QR orientation")
            else:
                print(f"❌ Insufficient patterns ({len(patterns)} < 3)")
        else:
            print(f"❌ No detection results found: {result_file}")
            print("   Run enhanced_strict_qr_detector.py first")
    
    # Save results
    if all_results:
        output_file = "finder_pattern_orientation_results.json"
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n" + "=" * 55)
        print(f"✅ Analysis Complete!")
        print(f"📊 Successfully processed {len(all_results)} QR codes")
        print(f"💾 Results saved to: {output_file}")
        print(f"🖼️  Visualizations: finder_pattern_orientation_*.png")
        print("=" * 55)
    else:
        print(f"\n❌ No results obtained")

if __name__ == "__main__":
    analyze_finder_pattern_orientation()
