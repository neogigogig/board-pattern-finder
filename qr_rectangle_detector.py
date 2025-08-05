#!/usr/bin/env python3
"""
QR Rectangle Detector and Grid System
Finds 4 QR finder patterns that form a rectangle and creates a grid overlay system
"""

import cv2
import numpy as np
import os
import json
from typing import List, Tuple, Dict, Optional
from itertools import combinations
import math

class QRRectangleDetector:
    def __init__(self, 
                 angle_tolerance=15,      # degrees tolerance for "parallel" lines
                 size_ratio_tolerance=0.3, # 30% tolerance for pattern size similarity
                 distance_ratio_tolerance=0.2): # 20% tolerance for opposite side length similarity
        """
        Initialize QR Rectangle Detector
        
        Args:
            angle_tolerance: Maximum angle difference for parallel lines (degrees)
            size_ratio_tolerance: Maximum ratio difference for pattern sizes
            distance_ratio_tolerance: Maximum ratio difference for opposite side lengths
        """
        self.angle_tolerance = angle_tolerance
        self.size_ratio_tolerance = size_ratio_tolerance
        self.distance_ratio_tolerance = distance_ratio_tolerance
        
    def calculate_angle(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Calculate angle of line from p1 to p2 in degrees"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.degrees(math.atan2(dy, dx))
    
    def normalize_angle(self, angle: float) -> float:
        """Normalize angle to [0, 180) range"""
        angle = angle % 180
        return angle
    
    def are_parallel(self, p1: Tuple[int, int], p2: Tuple[int, int], 
                     p3: Tuple[int, int], p4: Tuple[int, int]) -> bool:
        """Check if line p1-p2 is parallel to line p3-p4"""
        angle1 = self.normalize_angle(self.calculate_angle(p1, p2))
        angle2 = self.normalize_angle(self.calculate_angle(p3, p4))
        
        # Check both directions (parallel lines can have 180° difference)
        diff = min(abs(angle1 - angle2), abs(angle1 - angle2 + 180), abs(angle1 - angle2 - 180))
        return diff <= self.angle_tolerance
    
    def calculate_distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    def are_similar_sizes(self, patterns: List[Dict]) -> bool:
        """Check if patterns have similar sizes"""
        if len(patterns) != 4:
            return False
            
        # Extract pattern sizes (assuming they have 'size' or we can calculate from coordinates)
        sizes = []
        for pattern in patterns:
            # If pattern has explicit size, use it
            if 'size' in pattern:
                sizes.append(pattern['size'])
            else:
                # Estimate size from score or use default
                sizes.append(20)  # Default estimate
        
        if not sizes:
            return True  # If no size info, assume similar
            
        min_size = min(sizes)
        max_size = max(sizes)
        
        if min_size == 0:
            return False
            
        ratio = max_size / min_size
        return ratio <= (1 + self.size_ratio_tolerance)
    
    def order_corners_clockwise(self, points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Order 4 corner points in clockwise order: top-left, top-right, bottom-right, bottom-left
        """
        if len(points) != 4:
            return points
        
        # Convert to numpy array for easier manipulation
        pts = np.array(points, dtype=np.float32)
        
        # Find center point
        center_x = np.mean(pts[:, 0])
        center_y = np.mean(pts[:, 1])
        
        # Calculate angles from center to each point
        angles = []
        for i, (x, y) in enumerate(pts):
            angle = math.atan2(y - center_y, x - center_x)
            angles.append((angle, i, (int(x), int(y))))
        
        # Sort by angle to get clockwise order (starting from top-left-ish)
        angles.sort(key=lambda x: x[0])
        
        # Extract ordered points
        ordered_points = [point for _, _, point in angles]
        
        # Ensure we start with top-left: find point with minimum x+y
        min_sum_idx = min(range(4), key=lambda i: ordered_points[i][0] + ordered_points[i][1])
        
        # Rotate list to start with top-left point
        ordered_points = ordered_points[min_sum_idx:] + ordered_points[:min_sum_idx]
        
        return ordered_points
    
    def is_valid_rectangle(self, points: List[Tuple[int, int]]) -> Tuple[bool, Dict]:
        """
        Check if 4 points form a valid rectangle (allowing for perspective distortion)
        
        Returns:
            bool: True if valid rectangle
            dict: Analysis results with scores and measurements
        """
        if len(points) != 4:
            return False, {"error": "Need exactly 4 points"}
        
        # Order corners properly: top-left, top-right, bottom-right, bottom-left
        ordered_points = self.order_corners_clockwise(points)
        p1, p2, p3, p4 = ordered_points
        
        # Calculate side lengths
        side1 = self.calculate_distance(p1, p2)  # top side
        side2 = self.calculate_distance(p2, p3)  # right side  
        side3 = self.calculate_distance(p3, p4)  # bottom side
        side4 = self.calculate_distance(p4, p1)  # left side
        
        # Check if opposite sides are similar in length
        horizontal_ratio = min(side1, side3) / max(side1, side3) if max(side1, side3) > 0 else 0
        vertical_ratio = min(side2, side4) / max(side2, side4) if max(side2, side4) > 0 else 0
        
        # Check if opposite sides are parallel
        parallel_horizontal = self.are_parallel(p1, p2, p4, p3)  # top || bottom
        parallel_vertical = self.are_parallel(p2, p3, p1, p4)    # right || left
        
        # Calculate rectangle quality score
        parallelism_score = (int(parallel_horizontal) + int(parallel_vertical)) / 2.0
        similarity_score = (horizontal_ratio + vertical_ratio) / 2.0
        
        # Overall rectangle score
        rectangle_score = (parallelism_score * 0.6) + (similarity_score * 0.4)
        
        is_valid = (parallelism_score >= 0.5 and  # At least one pair of parallel sides
                   similarity_score >= 0.6)       # Reasonably similar opposite sides
        
        analysis = {
            "rectangle_score": rectangle_score,
            "parallelism_score": parallelism_score,
            "similarity_score": similarity_score,
            "parallel_horizontal": parallel_horizontal,
            "parallel_vertical": parallel_vertical,
            "horizontal_ratio": horizontal_ratio,
            "vertical_ratio": vertical_ratio,
            "side_lengths": [side1, side2, side3, side4],
            "sorted_points": ordered_points  # Use properly ordered points
        }
        
        return is_valid, analysis
    
    def find_best_rectangle(self, patterns: List[Dict], min_score: float = 0.6) -> Optional[Dict]:
        """
        Find the best rectangular arrangement of 4 patterns from detected patterns.
        Prioritizes patterns with higher scores.
        
        Args:
            patterns: List of detected QR patterns with 'position' and 'score'
            min_score: Minimum pattern score to consider
            
        Returns:
            Dict with best rectangle info or None if no valid rectangle found
        """
        if len(patterns) < 4:
            print(f"❌ Need at least 4 patterns, found {len(patterns)}")
            return None
        
        # Filter and sort patterns by score (highest first)
        good_patterns = [p for p in patterns if p.get('score', 0) >= min_score]
        good_patterns.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        if len(good_patterns) < 4:
            print(f"❌ Only {len(good_patterns)} patterns meet minimum score {min_score}")
            # If not enough high-scoring patterns, try with all patterns
            print("� Falling back to all patterns...")
            good_patterns = sorted(patterns, key=lambda x: x.get('score', 0), reverse=True)
            if len(good_patterns) < 4:
                return None
        
        print(f"�🔍 Analyzing {len(good_patterns)} patterns for rectangular arrangements...")
        print(f"📊 Top pattern scores: {[round(p.get('score', 0), 3) for p in good_patterns[:8]]}")
        
        # Extract positions with priority ordering
        positions = []
        for i, pattern in enumerate(good_patterns):
            if 'position' in pattern:
                pos = pattern['position']
                positions.append((pos[0], pos[1], i, pattern.get('score', 0)))  # x, y, index, score
            else:
                print(f"⚠️  Pattern {i} missing position info")
                continue
        
        if len(positions) < 4:
            print(f"❌ Only {len(positions)} patterns have position info")
            return None
        
        best_rectangle = None
        best_score = 0
        best_analysis = None
        total_combinations = 0
        valid_rectangles = 0
        
        # Prioritize combinations that include the highest-scoring patterns
        # Sort positions by score to try best patterns first
        positions.sort(key=lambda x: x[3], reverse=True)
        
        # Try combinations starting with the best patterns
        for combo in combinations(positions, 4):
            total_combinations += 1
            points = [(p[0], p[1]) for p in combo]  # Extract just x,y coordinates
            pattern_indices = [p[2] for p in combo]  # Extract pattern indices in good_patterns
            pattern_scores = [p[3] for p in combo]   # Extract pattern scores
            
            is_valid, analysis = self.is_valid_rectangle(points)
            
            if is_valid:
                valid_rectangles += 1
                
                # Calculate combined score with higher weight on pattern quality
                avg_pattern_score = sum(pattern_scores) / len(pattern_scores)
                min_pattern_score = min(pattern_scores)
                
                # Boost score if all patterns are high quality
                quality_bonus = 1.0
                if min_pattern_score >= 0.8:
                    quality_bonus = 1.2
                elif min_pattern_score >= 0.7:
                    quality_bonus = 1.1
                
                combined_score = (analysis['rectangle_score'] * 0.5 + avg_pattern_score * 0.5) * quality_bonus
                
                print("✅ Valid rectangle found:")
                print(f"   Rectangle score: {analysis['rectangle_score']:.3f}")
                print(f"   Pattern scores: {[f'{s:.3f}' for s in pattern_scores]}")
                print(f"   Avg pattern score: {avg_pattern_score:.3f}")
                print(f"   Quality bonus: {quality_bonus:.1f}")
                print(f"   Combined score: {combined_score:.3f}")
                print(f"   Points: {points}")
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_rectangle = {
                        'points': analysis['sorted_points'],
                        'pattern_indices': pattern_indices,
                        'patterns': [good_patterns[i] for i in pattern_indices],
                        'combined_score': combined_score,
                        'rectangle_score': analysis['rectangle_score'],
                        'pattern_scores': pattern_scores,
                        'avg_pattern_score': avg_pattern_score,
                        'quality_bonus': quality_bonus
                    }
                    best_analysis = analysis
        
        print("\n📊 Rectangle Analysis Summary:")
        print(f"   Total combinations tested: {total_combinations}")
        print(f"   Valid rectangles found: {valid_rectangles}")
        
        if best_rectangle:
            print(f"   Best rectangle score: {best_score:.3f}")
            print(f"   Best rectangle analysis: {best_analysis}")
            return best_rectangle
        else:
            print("   ❌ No valid rectangles found")
            return None

class GridSystem:
    def __init__(self, grid_size: Tuple[int, int] = (21, 21), expand_beyond_patterns: bool = True):
        """
        Initialize Grid System for QR code analysis
        
        Args:
            grid_size: Tuple of (width, height) for grid dimensions
                      Default (21, 21) is standard QR code size
            expand_beyond_patterns: If True, expand rectangle to include area outside finder patterns
        """
        self.grid_size = grid_size
        self.expand_beyond_patterns = expand_beyond_patterns
        
    def expand_corners_beyond_finder_patterns(self, corners: List[Tuple[int, int]], 
                                            patterns: List[Dict] = None) -> List[Tuple[int, int]]:
        """
        Expand the rectangle corners to include area beyond the finder patterns
        Uses exact expansion ratio: 15.8/11.8 = 1.339
        
        Args:
            corners: Original corner points from finder pattern centers
            patterns: List of pattern dictionaries (not used for exact ratio)
            
        Returns:
            Expanded corner points that include outer QR code area
        """
        if not self.expand_beyond_patterns:
            return corners
            
        # Use exact ratio provided: 15.8/11.8
        exact_expansion_ratio = 15.8 / 11.8  # ≈ 1.339
        
        # Calculate rectangle center
        center_x = sum(corner[0] for corner in corners) / len(corners)
        center_y = sum(corner[1] for corner in corners) / len(corners)
        
        # Expand each corner away from center by the exact ratio
        expanded_corners = []
        for corner in corners:
            # Vector from center to corner
            dx = corner[0] - center_x
            dy = corner[1] - center_y
            
            # Scale by exact expansion ratio
            new_x = center_x + dx * exact_expansion_ratio
            new_y = center_y + dy * exact_expansion_ratio
            expanded_corners.append((int(new_x), int(new_y)))
                
        return expanded_corners
        
    def order_corners_clockwise(self, corners: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Order corners in clockwise direction starting from top-left
        
        Args:
            corners: List of 4 corner points
            
        Returns:
            Ordered corners: [top-left, top-right, bottom-right, bottom-left]
        """
        if len(corners) != 4:
            return corners
            
        # Convert to numpy array for easier manipulation
        pts = np.array(corners, dtype=np.float32)
        
        # Find center point
        center_x = np.mean(pts[:, 0])
        center_y = np.mean(pts[:, 1])
        
        # Calculate angles from center to each point
        angles = []
        for x, y in pts:
            angle = math.atan2(y - center_y, x - center_x)
            angles.append((angle, (int(x), int(y))))
        
        # Sort by angle (clockwise from top-left)
        angles.sort(key=lambda x: x[0])
        
        # Extract sorted points
        sorted_points = [point for _, point in angles]
        
        return sorted_points
        
    def create_perspective_transform(self, corners: List[Tuple[int, int]], 
                                   target_size: int = 420) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create perspective transformation matrix from 4 corner points
        
        Args:
            corners: List of 4 corner points [(x,y), ...]
            target_size: Size of the target square image
            
        Returns:
            Tuple of (transformation_matrix, target_corners)
        """
        if len(corners) != 4:
            raise ValueError("Need exactly 4 corners for perspective transform")
        
        # Convert to numpy array
        src_points = np.array(corners, dtype=np.float32)
        
        # Define target rectangle (square)
        target_corners = np.array([
            [0, 0],                           # top-left
            [target_size, 0],                 # top-right  
            [target_size, target_size],       # bottom-right
            [0, target_size]                  # bottom-left
        ], dtype=np.float32)
        
        # Calculate perspective transformation matrix
        transform_matrix = cv2.getPerspectiveTransform(src_points, target_corners)
        
        return transform_matrix, target_corners
    
    def apply_grid_overlay(self, image: np.ndarray, corners: List[Tuple[int, int]], 
                          patterns: List[Dict] = None,
                          grid_color: Tuple[int, int, int] = (0, 255, 0),
                          line_thickness: int = 1) -> np.ndarray:
        """
        Apply grid overlay to image based on corner points
        
        Args:
            image: Input image
            corners: 4 corner points of the detected rectangle
            patterns: Optional list of pattern dictionaries for corner expansion
            grid_color: RGB color for grid lines
            line_thickness: Thickness of grid lines
            
        Returns:
            Image with grid overlay applied
        """
        # Expand corners to include area beyond finder patterns if enabled
        working_corners = self.expand_corners_beyond_finder_patterns(corners)
            
        # Order corners properly (clockwise from top-left)
        working_corners = self.order_corners_clockwise(working_corners)
        
        overlay_image = image.copy()
        
        if len(working_corners) != 4:
            print("❌ Need exactly 4 corners for grid overlay")
            return overlay_image
        
        # Draw the outer rectangle
        pts = np.array(working_corners, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(overlay_image, [pts], True, grid_color, line_thickness + 1)
        
        # Create grid lines using bilinear interpolation
        grid_w, grid_h = self.grid_size
        
        # Draw grid lines more systematically
        # Vertical lines
        for i in range(grid_w + 1):
            u = i / grid_w
            # Top edge point
            top_point = (
                int(working_corners[0][0] * (1 - u) + working_corners[1][0] * u),
                int(working_corners[0][1] * (1 - u) + working_corners[1][1] * u)
            )
            # Bottom edge point  
            bottom_point = (
                int(working_corners[3][0] * (1 - u) + working_corners[2][0] * u),
                int(working_corners[3][1] * (1 - u) + working_corners[2][1] * u)
            )
            cv2.line(overlay_image, top_point, bottom_point, grid_color, line_thickness)
        
        # Horizontal lines
        for j in range(grid_h + 1):
            v = j / grid_h
            # Left edge point
            left_point = (
                int(working_corners[0][0] * (1 - v) + working_corners[3][0] * v),
                int(working_corners[0][1] * (1 - v) + working_corners[3][1] * v)
            )
            # Right edge point
            right_point = (
                int(working_corners[1][0] * (1 - v) + working_corners[2][0] * v),
                int(working_corners[1][1] * (1 - v) + working_corners[2][1] * v)
            )
            cv2.line(overlay_image, left_point, right_point, grid_color, line_thickness)
        
        # Highlight finder pattern sizes if patterns are provided
        if patterns:
            self.highlight_finder_pattern_sizes(overlay_image, corners, patterns)
        
        return overlay_image
    
    def highlight_finder_pattern_sizes(self, image: np.ndarray, corners: List[Tuple[int, int]], 
                                     patterns: List[Dict]) -> None:
        """
        Placeholder method for finder pattern highlighting (currently disabled)
        
        Args:
            image: Image to draw on (modified in place)
            corners: 4 corner points of the detected rectangle
            patterns: List of pattern dictionaries containing position and size
        """
        # Pattern size visualization has been removed
        pass
    
    def extract_grid_cells(self, image: np.ndarray, corners: List[Tuple[int, int]], 
                          patterns: List[Dict] = None) -> np.ndarray:
        """
        Extract and analyze grid cells from the image
        
        Args:
            image: Input image
            corners: 4 corner points of the detected rectangle
            patterns: Optional list of pattern dictionaries for corner expansion
            
        Returns:
            2D array representing the grid cell values (0 for black, 1 for white)
        """
        if len(corners) != 4:
            raise ValueError("Need exactly 4 corners")
        
        # Expand corners to include area beyond finder patterns if enabled
        working_corners = self.expand_corners_beyond_finder_patterns(corners)
            
        # Order corners properly
        working_corners = self.order_corners_clockwise(working_corners)
        
        # Create perspective transform to normalize the QR code
        transform_matrix, _ = self.create_perspective_transform(working_corners, target_size=420)
        
        # Apply perspective correction
        corrected = cv2.warpPerspective(image, transform_matrix, (420, 420))
        
        # Convert to grayscale if needed
        if len(corrected.shape) == 3:
            corrected_gray = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)
        else:
            corrected_gray = corrected
        
        # Apply binary threshold
        _, binary = cv2.threshold(corrected_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Extract grid values
        grid_w, grid_h = self.grid_size
        cell_w = 420 // grid_w
        cell_h = 420 // grid_h
        
        grid_values = np.zeros((grid_h, grid_w), dtype=int)
        
        for i in range(grid_h):
            for j in range(grid_w):
                # Calculate cell boundaries
                y1 = i * cell_h
                y2 = (i + 1) * cell_h
                x1 = j * cell_w  
                x2 = (j + 1) * cell_w
                
                # Extract cell region
                cell = binary[y1:y2, x1:x2]
                
                # Determine if cell is black (0) or white (1)
                # Use mean value - if > 127, consider it white
                mean_value = np.mean(cell)
                grid_values[i, j] = 1 if mean_value > 127 else 0
        
        return grid_values

    def extract_border_cells(self, image: np.ndarray, corners: List[Tuple[int, int]], 
                            patterns: List[Dict] = None) -> Dict:
        """
        Extract and analyze border cells of the grid specifically
        
        Args:
            image: Input image
            corners: 4 corner points of the detected rectangle
            patterns: Optional list of pattern dictionaries for corner expansion
            
        Returns:
            Dictionary containing border cell values and analysis
        """
        if len(corners) != 4:
            raise ValueError("Need exactly 4 corners")
        
        # Expand corners to include area beyond finder patterns if enabled
        working_corners = self.expand_corners_beyond_finder_patterns(corners)
            
        # Order corners properly
        working_corners = self.order_corners_clockwise(working_corners)
        
        # Create perspective transform to normalize the QR code
        transform_matrix, _ = self.create_perspective_transform(working_corners, target_size=420)
        
        # Apply perspective correction
        corrected = cv2.warpPerspective(image, transform_matrix, (420, 420))
        
        # Convert to grayscale if needed
        if len(corrected.shape) == 3:
            corrected_gray = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)
        else:
            corrected_gray = corrected
        
        # Apply binary threshold
        _, binary = cv2.threshold(corrected_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Extract grid values
        grid_w, grid_h = self.grid_size
        cell_w = 420 // grid_w
        cell_h = 420 // grid_h
        
        # Initialize border cell containers
        border_cells = {
            'top': [],      # Row 0
            'bottom': [],   # Row grid_h-1
            'left': [],     # Column 0 
            'right': [],    # Column grid_w-1
            'corners': []   # Corner cells
        }
        
        # Extract border cells
        for i in range(grid_h):
            for j in range(grid_w):
                # Calculate cell boundaries
                y1 = i * cell_h
                y2 = (i + 1) * cell_h
                x1 = j * cell_w  
                x2 = (j + 1) * cell_w
                
                # Extract cell region
                cell = binary[y1:y2, x1:x2]
                
                # Determine if cell is black (0) or white (1)
                mean_value = np.mean(cell)
                cell_value = 0 if mean_value > 127 else 1  # 0=white, 1=black
                
                # Store cell information
                cell_info = {
                    'position': (i, j),
                    'value': cell_value,
                    'mean_intensity': mean_value,
                    'pixel_coords': ((x1, y1), (x2, y2))
                }
                
                # Categorize border cells
                is_corner = False
                
                if i == 0:  # Top row
                    border_cells['top'].append(cell_info)
                    if j == 0 or j == grid_w-1:  # Top corners
                        border_cells['corners'].append(cell_info)
                        is_corner = True
                        
                if i == grid_h-1:  # Bottom row
                    border_cells['bottom'].append(cell_info)
                    if j == 0 or j == grid_w-1:  # Bottom corners
                        if not is_corner:  # Avoid duplicating corners
                            border_cells['corners'].append(cell_info)
                        
                if j == 0 and i != 0 and i != grid_h-1:  # Left column (excluding corners)
                    border_cells['left'].append(cell_info)
                    
                if j == grid_w-1 and i != 0 and i != grid_h-1:  # Right column (excluding corners)
                    border_cells['right'].append(cell_info)
        
        # Create summary analysis
        analysis = {
            'border_cells': border_cells,
            'summary': {
                'top_pattern': [cell['value'] for cell in border_cells['top']],
                'bottom_pattern': [cell['value'] for cell in border_cells['bottom']],
                'left_pattern': [cell['value'] for cell in border_cells['left']],
                'right_pattern': [cell['value'] for cell in border_cells['right']],
                'corner_pattern': [cell['value'] for cell in border_cells['corners']],
                'total_border_cells': (
                    len(border_cells['top']) + 
                    len(border_cells['bottom']) + 
                    len(border_cells['left']) + 
                    len(border_cells['right'])
                ),
                'black_border_cells': sum([
                    sum(cell['value'] for cell in border_cells['top']),
                    sum(cell['value'] for cell in border_cells['bottom']),
                    sum(cell['value'] for cell in border_cells['left']),
                    sum(cell['value'] for cell in border_cells['right'])
                ]),
                'grid_size': self.grid_size
            }
        }
        
        return analysis


def process_qr_rectangle_detection(results_dir: str, output_dir: str = None):
    """
    Process QR detection results to find rectangles and create grid overlays
    
    Args:
        results_dir: Directory containing detection results
        output_dir: Directory to save rectangle detection results
    """
    if output_dir is None:
        output_dir = os.path.join(results_dir, "rectangle_analysis")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load detection results
    summary_file = os.path.join(results_dir, "detailed_detection_summary.json")
    if not os.path.exists(summary_file):
        print(f"❌ Detection summary not found: {summary_file}")
        return
    
    with open(summary_file, 'r') as f:
        detection_results = json.load(f)
    
    # Initialize detectors
    rectangle_detector = QRRectangleDetector()
    grid_system = GridSystem()
    
    results_summary = {}
    
    # Process each image
    for image_name, results in detection_results.items():
        if 'patterns_found' not in results or results['patterns_found'] < 4:
            continue
            
        print(f"\n🖼️  Processing: {image_name}")
        print(f"   Found {results['patterns_found']} patterns")
        
        # Load the original image
        image_path = os.path.join("data-qr-ratio-finder", image_name)
        if not os.path.exists(image_path):
            print(f"   ❌ Image not found: {image_path}")
            continue
            
        image = cv2.imread(image_path)
        if image is None:
            print(f"   ❌ Failed to load image: {image_path}")
            continue
        
        # Extract patterns from results
        if 'patterns_full' in results:
            patterns = results['patterns_full']
        elif 'pattern_positions' in results and 'pattern_scores' in results:
            # Reconstruct pattern data
            patterns = []
            positions = results['pattern_positions']
            scores = results['pattern_scores']
            sizes = results.get('pattern_sizes', [20] * len(positions))
            
            for i, (pos, score, size) in enumerate(zip(positions, scores, sizes)):
                patterns.append({
                    'position': pos,
                    'score': score,
                    'size': size,
                    'method': 'unknown'
                })
        else:
            print("   ⚠️  No pattern position data available")
            continue
        
        # Find best rectangle (prioritize high-scoring patterns)
        best_rectangle = rectangle_detector.find_best_rectangle(patterns, min_score=0.7)
        
        if best_rectangle:
            print(f"   ✅ Rectangle found! Score: {best_rectangle['combined_score']:.3f}")
            
            # Create grid overlay with pattern information for expansion
            corners = best_rectangle['points']
            rectangle_patterns = best_rectangle['patterns']
            grid_overlay = grid_system.apply_grid_overlay(image, corners, patterns=rectangle_patterns)
            
            # Save overlay image
            overlay_path = os.path.join(output_dir, f"grid_overlay_{image_name}")
            cv2.imwrite(overlay_path, grid_overlay)
            
            # Extract grid values
            try:
                grid_values = grid_system.extract_grid_cells(image, corners, patterns=rectangle_patterns)
                grid_path = os.path.join(output_dir, f"grid_values_{image_name.replace('.png', '.json')}")
                
                with open(grid_path, 'w') as f:
                    json.dump({
                        'grid_size': grid_system.grid_size,
                        'corners': corners,
                        'grid_values': grid_values.tolist()
                    }, f, indent=2)
                    
            except Exception as e:
                print(f"   ⚠️  Grid extraction failed: {e}")
            
            # Extract border cell analysis
            try:
                border_analysis = grid_system.extract_border_cells(image, corners, patterns=rectangle_patterns)
                border_path = os.path.join(output_dir, f"border_cells_{image_name.replace('.png', '.json')}")
                
                # Convert numpy arrays to lists for JSON serialization
                border_data = {
                    'border_cells': {
                        'top': border_analysis['border_cells']['top'],
                        'bottom': border_analysis['border_cells']['bottom'],
                        'left': border_analysis['border_cells']['left'],
                        'right': border_analysis['border_cells']['right'],
                        'corners': border_analysis['border_cells']['corners']
                    },
                    'summary': border_analysis['summary']
                }
                
                with open(border_path, 'w') as f:
                    json.dump(border_data, f, indent=2)
                
                print("   📊 Border cells analysis:")
                print(f"      Top row: {border_analysis['summary']['top_pattern']}")
                print(f"      Bottom row: {border_analysis['summary']['bottom_pattern']}")
                print(f"      Left column: {border_analysis['summary']['left_pattern']}")
                print(f"      Right column: {border_analysis['summary']['right_pattern']}")
                print(f"      Corners: {border_analysis['summary']['corner_pattern']}")
                print(f"      Total border cells: {border_analysis['summary']['total_border_cells']}")
                print(f"      Black border cells: {border_analysis['summary']['black_border_cells']}")
                    
            except Exception as e:
                print(f"   ⚠️  Border cell extraction failed: {e}")
            
            results_summary[image_name] = {
                "patterns_found": results['patterns_found'],
                "rectangle_found": True,
                "rectangle_score": best_rectangle['rectangle_score'],
                "combined_score": best_rectangle['combined_score'],
                "corners": corners,
                "pattern_indices": best_rectangle['pattern_indices'],
                "overlay_saved": overlay_path
            }
        else:
            print("   ❌ No valid rectangle found")
            results_summary[image_name] = {
                "patterns_found": results['patterns_found'],
                "rectangle_found": False,
                "rectangle_score": 0,
                "message": "No valid rectangular arrangement found"
            }
    
    # Save results summary
    summary_output = os.path.join(output_dir, "rectangle_analysis_summary.json")
    with open(summary_output, 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    print(f"\n✅ Rectangle analysis complete. Results saved to: {output_dir}")
    return results_summary

if __name__ == "__main__":
    # Test with sample data
    results_dir = "results/enhanced-strict-qr-results"
    
    print("🔍 QR Rectangle Detector and Grid System")
    print("=" * 50)
    
    # Process the detection results
    summary = process_qr_rectangle_detection(results_dir)
    
    if summary:
        print("\n📋 Processing Summary:")
        for image_name, result in summary.items():
            if result['rectangle_found']:
                print(f"✅ {image_name}: Rectangle found (score: {result['combined_score']:.3f})")
            else:
                print(f"❌ {image_name}: No rectangle found")
