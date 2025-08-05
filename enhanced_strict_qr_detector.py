#!/usr/bin/env python3
"""
Enhanced Strict QR Finder Pattern Detector with Debug Information
Specifically designed for data-qr-ratio-finder images with detailed 1:1:3:1:1 analysis
"""

import cv2
import numpy as np
import os
from typing import List, Tuple, Dict
import json

class EnhancedStrictQRDetector:
    def __init__(self, ratio_tolerance=0.22):
        """
        Enhanced Strict QR Finder Pattern Detector with optimized settings
        
        Args:
            ratio_tolerance: Tolerance for the 1:1:3:1:1 ratio (0.22 = 22% tolerance)
                           Optimized value providing good balance between precision and recall
        """
        self.ratio_tolerance = ratio_tolerance
        self.min_pattern_size = 8  # Slightly smaller minimum
        self.max_pattern_size = 500
        self.strict_ratio_threshold = 0.6  # More lenient for edge cases
        self.debug_info = []
        
    def reset_debug(self):
        """Reset debug information for new image"""
        self.debug_info = []
    
    def add_debug(self, message, data=None):
        """Add debug information"""
        self.debug_info.append({
            'message': message,
            'data': data
        })
    
    def is_circular_shape(self, contour) -> bool:
        """Detect if a contour is circular - DISABLED for testing"""
        # DISABLED: Anti-circular check removed to test impact on results
        return False
        
        # Original code (disabled):
        # area = cv2.contourArea(contour)
        # perimeter = cv2.arcLength(contour, True)
        # 
        # if perimeter == 0:
        #     return True
        # 
        # circularity = 4 * np.pi * area / (perimeter * perimeter)
        # 
        # # More lenient circle detection - QR finder patterns can appear circular at angles
        # if circularity > 0.92:  
        #     self.add_debug(f"Rejected circular shape: circularity={circularity:.3f}")
        #     return True
        # 
        # return False
    
    def is_square_like(self, contour) -> bool:
        """Check if contour is square-like with debug info"""
        # Get bounding rectangle and contour area
        x, y, w, h = cv2.boundingRect(contour)
        bbox_area = w * h
        contour_area = cv2.contourArea(contour)
        
        if bbox_area == 0:
            self.add_debug("Rejected: zero bbox area")
            return False
        
        # Aspect ratio check (more lenient for corner patterns)
        aspect_ratio = w / h
        if aspect_ratio < 0.4 or aspect_ratio > 2.5:  # More lenient
            self.add_debug(f"Rejected aspect ratio: {aspect_ratio:.3f}")
            return False
        
        # Area fill ratio (more lenient)
        fill_ratio = contour_area / bbox_area
        if fill_ratio < 0.3:  # More lenient for corner patterns
            self.add_debug(f"Rejected fill ratio: {fill_ratio:.3f}")
            return False
        
        # Check corner count (more lenient)
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        corner_count = self.count_corners(approx)
        
        if corner_count < 3 or corner_count > 10:  # More lenient for corner patterns
            self.add_debug(f"Rejected corner count: {corner_count}")
            return False
        
        self.add_debug(f"Passed square test: aspect={aspect_ratio:.3f}, fill={fill_ratio:.3f}, corners={corner_count}")
        return True
    
    def count_corners(self, approx):
        """Count corners in approximated polygon"""
        if len(approx) < 3:
            return 0
        
        corner_count = 0
        for i in range(len(approx)):
            p1 = approx[i-1][0]
            p2 = approx[i][0]
            p3 = approx[(i+1) % len(approx)][0]
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            angle_degrees = np.degrees(angle)
            
            # More lenient angle detection
            if angle_degrees < 135:  
                corner_count += 1
        
        return corner_count
    
    def analyze_strict_qr_pattern_structure(self, binary_image, cx, cy, size) -> Dict:
        """
        Analyze QR pattern structure with detailed debugging
        """
        h, w = binary_image.shape
        
        if cx < 0 or cx >= w or cy < 0 or cy >= h:
            return {'score': 0.0, 'reason': 'center out of bounds'}
        
        radius = min(size // 2, min(cx, cy, w - cx - 1, h - cy - 1))
        if radius < 5:
            return {'score': 0.0, 'reason': 'radius too small'}
        
        # Check concentric structure
        concentric_result = self.check_strict_concentric_structure(binary_image, cx, cy, radius)
        
        # Check symmetry - NEW FEATURE
        symmetry_result = self.analyze_pattern_symmetry(binary_image, cx, cy, radius)
        
        # Check line patterns in multiple directions
        line_results = []
        directions = [
            (1, 0, "horizontal"),
            (0, 1, "vertical"),
            (1, 1, "diagonal"),
            (1, -1, "anti-diagonal"),
        ]
        
        for dx, dy, direction_name in directions:
            line_pixels = []
            
            # Extract line in both directions from center
            max_range = min(radius, 30)
            for i in range(-max_range, max_range + 1):
                x = cx + i * dx
                y = cy + i * dy
                
                if 0 <= x < w and 0 <= y < h:
                    line_pixels.append(binary_image[y, x])
            
            if len(line_pixels) > 10:
                pattern_result = self.analyze_strict_qr_line_pattern(line_pixels, direction_name)
                line_results.append(pattern_result)
        
        # Calculate overall scores
        line_scores = [r['score'] for r in line_results if r['score'] > 0]
        line_pattern_score = np.mean(line_scores) if line_scores else 0.0
        
        # Combine scores with symmetry analysis
        # Updated scoring with strict concentric validation: Concentric (40%) + Line Pattern (40%) + Symmetry (20%)
        # Concentric validation is now much more strict and reliable, so give it higher weight
        final_score = (concentric_result['score'] * 0.40 + 
                      line_pattern_score * 0.40 + 
                      symmetry_result['score'] * 0.20)
        
        return {
            'score': final_score,
            'concentric': concentric_result,
            'symmetry': symmetry_result,
            'line_results': line_results,
            'line_pattern_score': line_pattern_score,
            'symmetry_score': symmetry_result['score'],
            'valid_directions': len(line_scores)
        }
    
    def analyze_strict_qr_line_pattern(self, line_pixels, direction_name) -> Dict:
        """
        Strict analysis for QR finder pattern 1:1:3:1:1 ratio with detailed output
        """
        if len(line_pixels) < 11:
            return {'score': 0.0, 'reason': 'insufficient length', 'direction': direction_name}
        
        # Convert to binary with adaptive threshold
        threshold = np.mean(line_pixels)
        binary_line = [0 if p < threshold else 1 for p in line_pixels]
        
        # Find runs of consecutive values
        runs = []
        current_value = binary_line[0]
        current_length = 1
        
        for i in range(1, len(binary_line)):
            if binary_line[i] == current_value:
                current_length += 1
            else:
                runs.append((current_value, current_length))
                current_value = binary_line[i]
                current_length = 1
        runs.append((current_value, current_length))
        
        result = {
            'direction': direction_name,
            'runs': runs,
            'total_runs': len(runs),
            'line_length': len(line_pixels)
        }
        
        # Need at least 5 runs for QR pattern
        if len(runs) < 5:
            result.update({'score': 0.0, 'reason': f'only {len(runs)} runs, need 5+'})
            return result
        
        # Check for alternating pattern starting with black
        if runs[0][0] != 0:
            result.update({'score': 0.0, 'reason': 'does not start with black'})
            return result
        
        # Check alternating pattern
        expected_pattern = [0, 1, 0, 1, 0]  # black-white-black-white-black
        for i in range(min(5, len(runs))):
            if runs[i][0] != expected_pattern[i]:
                result.update({'score': 0.0, 'reason': f'pattern breaks at position {i}'})
                return result
        
        # Analyze 1:1:3:1:1 ratio
        lengths = [run[1] for run in runs[:5]]
        total_length = sum(lengths)
        ratios = [l / total_length for l in lengths]
        
        # Ideal ratios: [0.125, 0.125, 0.375, 0.125, 0.125] for 1:1:3:1:1
        ideal_ratios = [1/8, 1/8, 3/8, 1/8, 1/8]
        
        # Calculate ratio deviations
        deviations = []
        ratio_matches = 0
        
        for i, (actual, ideal) in enumerate(zip(ratios, ideal_ratios)):
            deviation = abs(actual - ideal)
            deviations.append(deviation)
            
            if deviation < self.ratio_tolerance * 0.5:
                ratio_matches += 1
        
        # Calculate ratio score
        ratio_score = 0.0
        for deviation in deviations:
            if deviation < self.ratio_tolerance * 0.5:
                ratio_score += 1.0
            elif deviation < self.ratio_tolerance:
                ratio_score += 0.7
            elif deviation < self.ratio_tolerance * 1.5:
                ratio_score += 0.3
        
        ratio_score = ratio_score / 5  # Normalize
        
        # Check center dominance
        center_ratio = ratios[2]
        side_ratios = [ratios[0], ratios[1], ratios[3], ratios[4]]
        center_dominant = center_ratio > max(side_ratios) * 1.1
        
        # Check side consistency
        side_variation = np.std(side_ratios)
        side_consistent = side_variation < 0.08
        
        # Final scoring
        final_score = ratio_score
        if center_dominant:
            final_score += 0.2
        if side_consistent:
            final_score += 0.1
        
        result.update({
            'score': min(1.0, final_score),
            'ratios': ratios,
            'ideal_ratios': ideal_ratios,
            'deviations': deviations,
            'ratio_matches': ratio_matches,
            'center_dominant': center_dominant,
            'side_consistent': side_consistent,
            'side_variation': side_variation
        })
        
        return result
    
    def analyze_pattern_symmetry(self, binary_image, cx, cy, radius) -> Dict:
        """
        Analyze pattern symmetry - QR finder patterns should be symmetric both horizontally and vertically
        """
        h, w = binary_image.shape
        
        # Extract square region around the pattern
        size = min(radius * 2, 40)  # Use reasonable size limit
        half_size = size // 2
        
        # Bounds checking
        x1 = max(0, cx - half_size)
        y1 = max(0, cy - half_size)
        x2 = min(w, cx + half_size)
        y2 = min(h, cy + half_size)
        
        if x2 - x1 < 10 or y2 - y1 < 10:
            return {'score': 0.0, 'reason': 'region too small'}
        
        pattern_region = binary_image[y1:y2, x1:x2]
        region_h, region_w = pattern_region.shape
        
        # Calculate horizontal symmetry (left vs right halves)
        mid_w = region_w // 2
        left_half = pattern_region[:, :mid_w]
        right_half = pattern_region[:, mid_w:mid_w + mid_w]  # Ensure same size
        
        # Flip right half horizontally for comparison
        right_half_flipped = np.fliplr(right_half)
        
        # Calculate similarity between left and right halves
        if left_half.shape == right_half_flipped.shape and left_half.size > 0:
            # Calculate pixel-wise difference
            horizontal_diff = np.abs(left_half.astype(float) - right_half_flipped.astype(float))
            horizontal_similarity = 1.0 - (np.mean(horizontal_diff) / 255.0)
        else:
            horizontal_similarity = 0.0
        
        # Calculate vertical symmetry (top vs bottom halves)
        mid_h = region_h // 2
        top_half = pattern_region[:mid_h, :]
        bottom_half = pattern_region[mid_h:mid_h + mid_h, :]  # Ensure same size
        
        # Flip bottom half vertically for comparison
        bottom_half_flipped = np.flipud(bottom_half)
        
        # Calculate similarity between top and bottom halves
        if top_half.shape == bottom_half_flipped.shape and top_half.size > 0:
            # Calculate pixel-wise difference
            vertical_diff = np.abs(top_half.astype(float) - bottom_half_flipped.astype(float))
            vertical_similarity = 1.0 - (np.mean(vertical_diff) / 255.0)
        else:
            vertical_similarity = 0.0
        
        # Combine symmetry scores
        symmetry_score = (horizontal_similarity + vertical_similarity) / 2.0
        
        # QR finder patterns should have high symmetry (>0.8)
        # Apply threshold and scaling
        if symmetry_score > 0.8:
            final_score = 1.0
        elif symmetry_score > 0.7:
            final_score = 0.8
        elif symmetry_score > 0.6:
            final_score = 0.6
        elif symmetry_score > 0.5:
            final_score = 0.4
        else:
            final_score = 0.0
        
        return {
            'score': final_score,
            'horizontal_similarity': horizontal_similarity,
            'vertical_similarity': vertical_similarity,
            'combined_symmetry': symmetry_score,
            'region_size': (region_w, region_h)
        }
    
    def check_strict_concentric_structure(self, binary_image, cx, cy, radius) -> Dict:
        """
        Improved check for QR finder pattern concentric structure with adaptive sizing
        
        Key improvements:
        1. Better radius calculation based on actual pattern size
        2. More flexible thresholds accounting for image quality
        3. Robust sampling with outlier handling
        4. Gradual scoring instead of binary pass/fail
        """
        h, w = binary_image.shape
        
        if cx < 0 or cx >= w or cy < 0 or cy >= h:
            return {'score': 0.0, 'reason': 'center out of bounds'}
        
        # Calculate pattern size from radius (radius is typically half the pattern size)
        estimated_size = radius * 2
        
        # Improved radius calculation based on pattern size
        # QR finder patterns typically have: center (1/7), first ring (1/7), second ring (3/7)
        base_radius = estimated_size // 14  # 1/14 of pattern size for base unit
        
        # Calculate rings based on QR finder pattern proportions
        center_radius = max(2, base_radius)  # Center sampling area
        first_ring_r = max(4, base_radius * 3)  # First light ring
        second_ring_r = max(6, base_radius * 6)  # Second dark ring
        
        # Ensure rings don't exceed image bounds
        max_safe_radius = min(cx, cy, w - cx - 1, h - cy - 1)
        if second_ring_r > max_safe_radius:
            scale_factor = max_safe_radius / second_ring_r
            first_ring_r = int(first_ring_r * scale_factor)
            second_ring_r = int(second_ring_r * scale_factor)
            center_radius = max(2, int(center_radius * scale_factor))
        
        if first_ring_r < 3 or second_ring_r < 5:
            return {'score': 0.0, 'reason': 'pattern too small for reliable ring analysis'}
        
        # Sample center region more robustly - circular sampling
        center_pixels = []
        for dy in range(-center_radius, center_radius + 1):
            for dx in range(-center_radius, center_radius + 1):
                if dx*dx + dy*dy <= center_radius*center_radius:  # Circular sampling
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        center_pixels.append(binary_image[ny, nx])
        
        if len(center_pixels) < 4:
            return {'score': 0.0, 'reason': 'insufficient center samples'}
        
        # Calculate center dark ratio
        center_dark_count = sum(1 for p in center_pixels if p < 127)
        center_dark_ratio = center_dark_count / len(center_pixels)
        
        # More flexible center validation (70% instead of 80%)
        if center_dark_ratio < 0.7:
            return {
                'score': 0.0, 
                'reason': f'center not dark enough: {center_dark_ratio:.1%}',
                'center_dark_ratio': center_dark_ratio,
                'radii_used': {'center': center_radius, 'first': first_ring_r, 'second': second_ring_r}
            }
        
        # Sample rings with robust outlier handling
        ring_info = []
        ring_radii = [first_ring_r, second_ring_r]
        
        for i, r in enumerate(ring_radii):
            # Dense sampling with 5-degree increments for accuracy
            ring_pixels = []
            for angle in range(0, 360, 5):
                x = int(cx + r * np.cos(np.radians(angle)))
                y = int(cy + r * np.sin(np.radians(angle)))
                
                if 0 <= x < w and 0 <= y < h:
                    ring_pixels.append(binary_image[y, x])
            
            if len(ring_pixels) < 30:  # Need sufficient samples
                return {'score': 0.0, 'reason': f'insufficient ring {i+1} samples'}
            
            # Handle outliers by using median-based approach
            ring_pixels_array = np.array(ring_pixels)
            dark_pixels = ring_pixels_array < 127
            dark_ratio = np.mean(dark_pixels)
            
            ring_info.append({
                'radius': r,
                'dark_ratio': dark_ratio,
                'dark_count': int(np.sum(dark_pixels)),
                'total_pixels': len(ring_pixels)
            })
        
        first_ring = ring_info[0]  # Should be light
        second_ring = ring_info[1]  # Should be dark
        
        # More flexible thresholds with gradual scoring
        # First ring should be light (< 50% instead of < 30%)
        first_ring_score = 0.0
        if first_ring['dark_ratio'] <= 0.3:
            first_ring_score = 1.0  # Excellent
        elif first_ring['dark_ratio'] <= 0.4:
            first_ring_score = 0.8  # Good
        elif first_ring['dark_ratio'] <= 0.5:
            first_ring_score = 0.6  # Acceptable
        elif first_ring['dark_ratio'] <= 0.6:
            first_ring_score = 0.3  # Poor but might be valid
        # else 0.0 (too dark)
        
        # Second ring should be dark (> 60% instead of > 70%)
        second_ring_score = 0.0
        if second_ring['dark_ratio'] >= 0.8:
            second_ring_score = 1.0  # Excellent
        elif second_ring['dark_ratio'] >= 0.7:
            second_ring_score = 0.9  # Very good
        elif second_ring['dark_ratio'] >= 0.6:
            second_ring_score = 0.7  # Good
        elif second_ring['dark_ratio'] >= 0.5:
            second_ring_score = 0.4  # Acceptable
        # else 0.0 (too light)
        
        # Center score (normalized, with bonus for very dark centers)
        center_score = center_dark_ratio
        if center_dark_ratio >= 0.9:
            center_score = 1.0
        elif center_dark_ratio >= 0.8:
            center_score = 0.95
        
        # Calculate overall quality with weighted average
        # Give more weight to the critical light ring requirement
        quality_score = (center_score * 0.25 + first_ring_score * 0.50 + second_ring_score * 0.25)
        
        # Lower threshold for acceptance (0.6 instead of 0.85)
        minimum_quality = 0.6
        
        if quality_score < minimum_quality:
            return {
                'score': 0.0,
                'reason': f'insufficient pattern quality: {quality_score:.3f}',
                'center_dark_ratio': center_dark_ratio,
                'rings': ring_info,
                'component_scores': {
                    'center': center_score,
                    'first_ring': first_ring_score,
                    'second_ring': second_ring_score
                },
                'quality_score': quality_score,
                'radii_used': {'center': center_radius, 'first': first_ring_r, 'second': second_ring_r}
            }
        
        return {
            'score': quality_score,
            'center_dark_ratio': center_dark_ratio,
            'rings': ring_info,
            'component_scores': {
                'center': center_score,
                'first_ring': first_ring_score,
                'second_ring': second_ring_score
            },
            'quality_score': quality_score,
            'validation': f'PASS - quality score: {quality_score:.3f}',
            'radii_used': {'center': center_radius, 'first': first_ring_r, 'second': second_ring_r}
        }
    
    def preprocess_image(self, image):
        """Multiple preprocessing methods including OTSU and adaptive thresholding"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply Gaussian blur for noise reduction
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Multiple thresholding methods
        results = {}
        
        # Method 1: Basic OTSU
        _, binary_otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results['otsu'] = binary_otsu
        
        # Method 2: OTSU with light morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary_clean = cv2.morphologyEx(binary_otsu, cv2.MORPH_OPEN, kernel)
        results['otsu_clean'] = binary_clean
        
        # Method 3: OTSU on original (without blur) for sharp edges
        _, binary_otsu_orig = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results['otsu_original'] = binary_otsu_orig
        
        # Method 4: Adaptive Mean thresholding (better for uneven lighting)
        # Apply mild blur to reduce noise before adaptive thresholding
        blurred_adaptive = cv2.GaussianBlur(gray, (3, 3), 0)
        adaptive_mean = cv2.adaptiveThreshold(blurred_adaptive, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 131, 18)
        results['adaptive_mean'] = adaptive_mean
        
        # Method 5: Adaptive Gaussian thresholding 
        adaptive_gaussian = cv2.adaptiveThreshold(blurred_adaptive, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 131, 18)
        results['adaptive_gaussian'] = adaptive_gaussian
        
        # Method 6: Fixed threshold at 127 (middle value)
        _, binary_fixed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        results['fixed_127'] = binary_fixed
        
        return gray, results
    
    def find_qr_patterns_multi_threshold(self, image):
        """
        Find QR patterns using multiple thresholding methods
        """
        gray, binary_results = self.preprocess_image(image)
        
        all_patterns = []
        
        # Try each binary image
        for method_name, binary in binary_results.items():
            self.add_debug(f"Testing with {method_name} thresholding")
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            method_patterns = []
            
            for i, contour in enumerate(contours):
                # Basic size filtering
                area = cv2.contourArea(contour)
                if area < self.min_pattern_size * self.min_pattern_size:
                    continue
                if area > self.max_pattern_size * self.max_pattern_size:
                    continue
                
                self.add_debug(f"  Contour {i}: area={area:.0f}")
                
                # Filter out circular shapes - DISABLED for testing
                if self.is_circular_shape(contour):
                    continue
                
                # Check if square-like
                if not self.is_square_like(contour):
                    continue
                
                # Get center and size
                M = cv2.moments(contour)
                if M["m00"] == 0:
                    continue
                
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Estimate size
                x, y, w, h = cv2.boundingRect(contour)
                size = max(w, h)
                
                self.add_debug(f"  Analyzing pattern at ({cx},{cy}) size={size}")
                
                # Pattern structure analysis
                pattern_result = self.analyze_strict_qr_pattern_structure(binary, cx, cy, size)
                
                if pattern_result['score'] > 0.5:  # Lower threshold to capture more potential patterns
                    pattern = {
                        'center': (cx, cy),
                        'size': size,
                        'contour': contour,
                        'score': pattern_result['score'],
                        'bbox': (x, y, w, h),
                        'method': method_name,
                        'analysis': pattern_result
                    }
                    method_patterns.append(pattern)
                    self.add_debug(f"  ✓ Pattern found: score={pattern_result['score']:.3f}")
                else:
                    self.add_debug(f"  ✗ Pattern rejected: score={pattern_result['score']:.3f}")
            
            all_patterns.extend(method_patterns)
        
        # Remove duplicates (patterns found by multiple methods)
        unique_patterns = self.remove_duplicate_patterns(all_patterns)
        
        # Sort by score
        unique_patterns.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply smart filtering to get top 3-4 QR finder patterns
        filtered_patterns = self.select_best_qr_patterns(unique_patterns)
        
        return filtered_patterns, gray, binary_results
    
    def remove_duplicate_patterns(self, patterns):
        """Remove duplicate patterns found by different methods"""
        if not patterns:
            return []
        
        unique = []
        
        for pattern in patterns:
            is_duplicate = False
            cx1, cy1 = pattern['center']
            
            for existing in unique:
                cx2, cy2 = existing['center']
                distance = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                
                if distance < 20:  # Close enough to be considered duplicate
                    # Keep the one with higher score
                    if pattern['score'] > existing['score']:
                        unique.remove(existing)
                        unique.append(pattern)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(pattern)
        
        return unique
    
    def select_best_qr_patterns(self, patterns):
        """
        Smart filtering to select the best 3-4 QR finder patterns
        Uses multiple criteria beyond just score to identify genuine QR patterns
        """
        if len(patterns) <= 4:
            return patterns
        
        # Calculate additional QR-specific metrics for each pattern
        enhanced_patterns = []
        
        for pattern in patterns:
            analysis = pattern['analysis']
            
            # QR-specific quality metrics
            qr_quality_score = 0.0
            
            # 1. Multiple direction validation (QR patterns should work in multiple directions)
            valid_directions = analysis.get('valid_directions', 0)
            direction_score = min(valid_directions / 4.0, 1.0)  # Prefer patterns valid in multiple directions
            qr_quality_score += direction_score * 0.3
            
            # 2. Line pattern consistency across directions
            line_results = analysis.get('line_results', [])
            if line_results:
                line_scores = [r['score'] for r in line_results if r['score'] > 0]
                if line_scores:
                    line_consistency = 1.0 - np.std(line_scores)  # Lower std = more consistent
                    qr_quality_score += max(0, line_consistency) * 0.2
            
            # 3. Size appropriateness (QR patterns shouldn't be too small or too large)
            size = pattern['size']
            if 15 <= size <= 80:  # Optimal size range for QR finder patterns
                size_score = 1.0
            elif 10 <= size <= 120:  # Acceptable range
                size_score = 0.7
            else:  # Too small or too large
                size_score = 0.3
            qr_quality_score += size_score * 0.2
            
            # 4. Concentric structure quality
            concentric_score = analysis.get('concentric', {}).get('score', 0)
            qr_quality_score += concentric_score * 0.2
            
            # 5. Detection method reliability (some methods are more reliable)
            method = pattern['method']
            if method in ['otsu', 'otsu_original']:
                method_score = 1.0  # OTSU is generally reliable for good contrast
            elif method in ['adaptive_mean', 'adaptive_gaussian']:
                method_score = 0.9  # Adaptive methods good for uneven lighting
            else:
                method_score = 0.7
            qr_quality_score += method_score * 0.1
            
            # Combined score (original score + QR quality metrics)
            combined_score = pattern['score'] * 0.6 + qr_quality_score * 0.4
            
            enhanced_pattern = pattern.copy()
            enhanced_pattern['qr_quality_score'] = qr_quality_score
            enhanced_pattern['combined_score'] = combined_score
            enhanced_pattern['direction_score'] = direction_score
            enhanced_pattern['size_score'] = size_score
            
            enhanced_patterns.append(enhanced_pattern)
        
        # Sort by combined score
        enhanced_patterns.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Apply distance-based filtering to avoid clustering
        final_patterns = []
        min_distance = 50  # Minimum distance between patterns
        
        for pattern in enhanced_patterns:
            cx1, cy1 = pattern['center']
            too_close = False
            
            for existing in final_patterns:
                cx2, cy2 = existing['center']
                distance = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                
                if distance < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                final_patterns.append(pattern)
                
                # Stop when we have 4 good patterns
                if len(final_patterns) >= 4:
                    break
        
        # If we have less than 3 patterns, add more from the original list (with relaxed distance)
        if len(final_patterns) < 3:
            relaxed_distance = 30
            
            for pattern in enhanced_patterns:
                if pattern in final_patterns:
                    continue
                    
                cx1, cy1 = pattern['center']
                too_close = False
                
                for existing in final_patterns:
                    cx2, cy2 = existing['center']
                    distance = np.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)
                    
                    if distance < relaxed_distance:
                        too_close = True
                        break
                
                if not too_close:
                    final_patterns.append(pattern)
                    
                    if len(final_patterns) >= 4:
                        break
        
        return final_patterns

def process_qr_ratio_finder_with_debug():
    """
    Process all images in data-qr-ratio-finder folder with detailed debugging
    """
    print("🔍 ENHANCED STRICT QR FINDER PATTERN DETECTOR")
    print("=" * 60)
    print("Processing data-qr-ratio-finder images with detailed 1:1:3:1:1 analysis")
    
    detector = EnhancedStrictQRDetector(ratio_tolerance=0.22)
    
    input_folder = "data-qr-ratio-finder"
    output_folder = "results/enhanced-strict-qr-results"
    
    # Create output directory
    os.makedirs(output_folder, exist_ok=True)
    
    # Get image files
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        image_files.extend([f for f in os.listdir(input_folder) if f.lower().endswith(ext.replace('*', ''))])
    
    print(f"\nFound {len(image_files)} images to process")
    
    all_results = {}
    
    for i, filename in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processing: {filename}")
        print("=" * 60)
        
        detector.reset_debug()
        
        # Load image
        image_path = os.path.join(input_folder, filename)
        image = cv2.imread(image_path)
        
        if image is None:
            print(f"❌ Failed to load {filename}")
            continue
        
        # Detect patterns
        patterns, gray, binary_results = detector.find_qr_patterns_multi_threshold(image)
        
        print(f"Found {len(patterns)} potential QR patterns")
        
        # Create detailed visualization
        result_image = image.copy()
        
        # Draw all potential patterns with detailed info
        for j, pattern in enumerate(patterns):
            cx, cy = pattern['center']
            size = pattern['size']
            score = pattern['score']
            method = pattern['method']
            analysis = pattern['analysis']
            
            # Color based on score
            if score > 0.8:
                color = (0, 255, 0)  # Green for excellent
            elif score > 0.6:
                color = (0, 200, 200)  # Yellow for good
            else:
                color = (0, 100, 255)  # Orange for acceptable
            
            # Draw pattern
            cv2.circle(result_image, (cx, cy), size//2, color, 2)
            cv2.circle(result_image, (cx, cy), 3, color, -1)  # Center dot
            
            # Label with detailed component scores
            concentric_score = analysis['concentric']['score']
            line_score = analysis['line_pattern_score']
            
            # Main label with overall score
            label = f"P{j+1}: {score:.3f} ({method})"
            cv2.putText(result_image, label, 
                       (cx - 40, cy - size//2 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Component scores below main label
            concentric_label = f"C:{concentric_score:.2f}"
            line_label = f"L:{line_score:.2f}"
            component_label = f"{concentric_label} {line_label}"
            cv2.putText(result_image, component_label, 
                       (cx - 30, cy - size//2 + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            
            # Print detailed analysis
            print(f"\nPattern {j+1} at ({cx},{cy}):")
            print(f"  Overall Score: {score:.3f} (method: {method})")
            print(f"  📊 Component Scores Summary:")
            print(f"    ┌─────────────┬───────┬────────┐")
            print(f"    │ Component   │ Score │ Weight │")
            print(f"    ├─────────────┼───────┼────────┤")
            print(f"    │ Concentric  │ {analysis['concentric']['score']:.3f} │  40%   │")
            print(f"    │ Line Pattern│ {analysis['line_pattern_score']:.3f} │  40%   │")
            print(f"    │ Symmetry    │ {analysis['symmetry']['score']:.3f} │  20%   │")
            print(f"    └─────────────┴───────┴────────┘")
            
            # Show concentric validation details
            concentric_info = analysis['concentric']
            if concentric_info['score'] == 0.0 and 'reason' in concentric_info:
                print(f"  🔴 Concentric REJECTED: {concentric_info['reason']}")
                if 'center_dark_ratio' in concentric_info:
                    print(f"      Center dark ratio: {concentric_info['center_dark_ratio']:.1%}")
                if 'rings' in concentric_info:
                    for i, ring in enumerate(concentric_info['rings']):
                        ring_type = "light" if i == 0 else "dark"
                        print(f"      Ring {i+1} (should be {ring_type}): {ring['dark_ratio']:.1%} dark")
            elif concentric_info['score'] > 0:
                print(f"  ✅ Concentric PASSED: {concentric_info.get('validation', 'Valid structure')}")
                if 'quality_score' in concentric_info:
                    print(f"      Quality score: {concentric_info['quality_score']:.3f}")
            
            print(f"  📏 Line Pattern Details:")
            print(f"      Score: {analysis['line_pattern_score']:.3f}")
            print(f"      Valid directions: {analysis['valid_directions']}/4")
            
            print(f"  🔄 Symmetry Details:")
            print(f"      Score: {analysis['symmetry']['score']:.3f}")
            print(f"      Horizontal: {analysis['symmetry']['horizontal_similarity']:.3f}")
            print(f"      Vertical: {analysis['symmetry']['vertical_similarity']:.3f}")
            
            # Print line analysis details
            for line_result in analysis['line_results']:
                if line_result['score'] > 0:
                    print(f"    {line_result['direction']}: score={line_result['score']:.3f}")
                    if 'ratios' in line_result:
                        ratios_str = " ".join([f"{r:.3f}" for r in line_result['ratios']])
                        print(f"      ratios: [{ratios_str}]")
                        deviations_str = " ".join([f"{d:.3f}" for d in line_result['deviations']])
                        print(f"      deviations: [{deviations_str}]")
        
        # Save results with multiple binary versions
        output_path = os.path.join(output_folder, f"detected_{filename}")
        cv2.imwrite(output_path, result_image)
        
        # Save all binary images for comparison
        for method_name, binary in binary_results.items():
            binary_path = os.path.join(output_folder, f"binary_{method_name}_{filename}")
            cv2.imwrite(binary_path, binary)
        
        # Store results
        image_results = {
            'image_name': filename,
            'patterns_found': len(patterns),
            'patterns': [{
                'center': {'x': p['center'][0], 'y': p['center'][1]},
                'score': p['score'],
                'size': p['size'],
                'method': p['method'],
                'analysis': p['analysis']
            } for p in patterns],
            'summary': {
                'pattern_count': len(patterns),
                'best_score': max([p['score'] for p in patterns]) if patterns else 0,
                'average_score': np.mean([p['score'] for p in patterns]) if patterns else 0,
                'methods_used': list(set([p['method'] for p in patterns]))
            }
        }
        
        all_results[filename] = {
            'patterns_found': len(patterns),
            'pattern_scores': [p['score'] for p in patterns],
            'best_pattern_score': max([p['score'] for p in patterns]) if patterns else 0,
            'debug_info': detector.debug_info,
            'pattern_details': [p['analysis'] for p in patterns],
            'pattern_positions': [p['center'] for p in patterns],
            'pattern_sizes': [p['size'] for p in patterns],
            'patterns_full': [{
                'position': p['center'],
                'score': p['score'],
                'size': p['size'],
                'method': p['method']
            } for p in patterns]
        }
        
        # Save individual JSON result file
        json_filename = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '') + '_results.json'
        json_path = os.path.join(output_folder, json_filename)
        with open(json_path, 'w') as f:
            json.dump(image_results, f, indent=2, default=str)
        
        print(f"✅ Results saved for {filename}")
        
        # Print debug info
        print(f"\nDebug info ({len(detector.debug_info)} messages):")
        for debug_msg in detector.debug_info[-10:]:  # Show last 10 messages
            print(f"  {debug_msg['message']}")
    
    # Save detailed summary
    summary_path = os.path.join(output_folder, "detailed_detection_summary.json")
    with open(summary_path, 'w') as f:
        # Keep the full results for rectangle detection
        json.dump(all_results, f, indent=2, default=str)
    
    # Print summary
    print(f"\n📊 ENHANCED DETECTION SUMMARY")
    print("=" * 40)
    print(f"Total images processed: {len(all_results)}")
    
    successful_detections = sum(1 for r in all_results.values() if r['patterns_found'] > 0)
    print(f"Images with patterns detected: {successful_detections}")
    
    total_patterns = sum(r['patterns_found'] for r in all_results.values())
    print(f"Total QR patterns found: {total_patterns}")
    
    # Best scores
    best_scores = [r['best_pattern_score'] for r in all_results.values() if r['best_pattern_score'] > 0]
    if best_scores:
        print(f"Average best pattern score: {np.mean(best_scores):.3f}")
        print(f"Highest pattern score: {max(best_scores):.3f}")
    
    print(f"\n📁 Results saved in: {output_folder}")
    print("✅ Enhanced processing complete!")

if __name__ == "__main__":
    process_qr_ratio_finder_with_debug()
