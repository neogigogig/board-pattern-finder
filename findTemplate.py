#!/usr/bin/env python3
"""
Find Template in Images

This script detects if a template image is present in target images from the data-qr-ratio-finder folder.
It can handle rotations up to ±45 degrees and provides a match score.
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_images(artwork_path, data_folder):
    """Load the artwork and target images."""
    artwork = cv2.imread(str(artwork_path))
    if artwork is None:
        raise FileNotFoundError(f"Could not load artwork image from {artwork_path}")
    
    # Convert to RGB for better feature matching
    artwork = cv2.cvtColor(artwork, cv2.COLOR_BGR2RGB)
    
    # Get all jpeg and png files from data folder
    target_files = []
    target_files.extend(Path(data_folder).glob("*.jpeg"))
    target_files.extend(Path(data_folder).glob("*.jpg"))
    target_files.extend(Path(data_folder).glob("*.png"))
    
    if not target_files:
        raise FileNotFoundError(f"No image files found in {data_folder}")
    
    return artwork, target_files

def find_artwork_in_image(artwork, target_path, min_match_count=10, rotation_range=45):
    """
    Find the artwork in target image using feature matching.
    
    Args:
        artwork: The artwork image to find
        target_path: Path to the target image
        min_match_count: Minimum number of feature matches to consider a detection
        rotation_range: Maximum rotation angle to consider (degrees)
        
    Returns:
        result_dict: Dictionary with match results
    """
    # Load target image
    target_img = cv2.imread(str(target_path))
    if target_img is None:
        return {"success": False, "message": f"Could not load {target_path}"}
    
    target_img = cv2.cvtColor(target_img, cv2.COLOR_BGR2RGB)
    
    # Initialize feature detector (SIFT is good for rotation invariance)
    sift = cv2.SIFT_create()
    
    # Detect features and compute descriptors
    kp1, des1 = sift.detectAndCompute(artwork, None)
    kp2, des2 = sift.detectAndCompute(target_img, None)
    
    # Check if features were found in both images
    if des1 is None or des2 is None:
        return {"success": False, "message": "Could not detect features in one of the images"}
    
    # Feature matching
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    
    # Try to match with FLANN
    try:
        matches = flann.knnMatch(des1, des2, k=2)
    except cv2.error:
        # Fall back to brute force matcher if FLANN fails
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
    
    # Store all good matches as per Lowe's ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)
    
    # Calculate match score based on good matches ratio
    match_score = len(good_matches) / len(kp1) if kp1 else 0
    match_score = min(match_score * 2, 1.0)  # Scale up to a max of 1.0
    
    # If enough matches, find homography
    if len(good_matches) >= min_match_count:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # Find homography
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        # Check if the transformation is valid
        if H is not None:
            # Check for excessive skew or scaling (unrealistic transformations)
            if is_valid_homography(H, rotation_range):
                # Get the corners of the artwork image
                h, w = artwork.shape[:2]
                corners = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                
                # Transform artwork corners to target image space
                transformed_corners = cv2.perspectiveTransform(corners, H)
                
                # Create result image with bounding box - improved visualization
                result_img = target_img.copy()
                
                # Draw a filled semi-transparent polygon to highlight the detected area
                overlay = result_img.copy()
                cv2.fillPoly(overlay, [np.int32(transformed_corners)], (255, 200, 0))  # Orange-yellow fill
                cv2.addWeighted(overlay, 0.3, result_img, 0.7, 0, result_img)  # Blend with 30% opacity
                
                # Draw a thick border around the detected area
                cv2.polylines(result_img, [np.int32(transformed_corners)], True, (0, 255, 0), 5)  # Thicker green border
                
                # Add corner markers
                for point in np.int32(transformed_corners):
                    x, y = point.ravel()
                    cv2.circle(result_img, (x, y), 10, (255, 0, 0), -1)  # Blue circles at corners
                
                # Add score as text on the image
                corners_int = np.int32(transformed_corners)
                if corners_int.size > 0:
                    # Calculate text position relative to the top-left of the bounding box
                    x, y = corners_int.reshape(-1, 2).min(0)
                    text_pos = (x + 20, y + 40)
                    cv2.putText(result_img, f"Score: {match_score:.2f}", text_pos, 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4)  # White text with black outline
                    cv2.putText(result_img, f"Score: {match_score:.2f}", text_pos, 
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)  # Red text
                
                # Create a split view to compare with and without detection highlight
                split_view = create_comparison_view(target_img, result_img)
                
                return {
                    "success": True, 
                    "score": match_score,
                    "matches": len(good_matches),
                    "result_img": result_img,
                    "split_view": split_view,
                    "homography": H
                }
    
    # Not enough matches or invalid transformation
    return {
        "success": False,
        "score": match_score,
        "matches": len(good_matches),
        "message": "Not enough matches found or invalid transformation"
    }

def create_comparison_view(original, detected):
    """Create a side-by-side comparison of original and detected images."""
    # Get dimensions
    h1, w1 = original.shape[:2]
    h2, w2 = detected.shape[:2]
    
    # Create a new image with both side by side
    width = w1 + w2
    height = max(h1, h2)
    comparison = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Copy images
    comparison[:h1, :w1] = original
    comparison[:h2, w1:w1+w2] = detected
    
    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(comparison, "Original", (10, 30), font, 1, (255, 255, 255), 2)
    cv2.putText(comparison, "Detected", (w1 + 10, 30), font, 1, (255, 255, 255), 2)
    
    # Add dividing line
    cv2.line(comparison, (w1, 0), (w1, height), (255, 255, 255), 2)
    
    return comparison

def is_valid_homography(H, max_angle=45):
    """Check if the homography represents a valid transformation within rotation constraints."""
    # Decompose the homography matrix
    try:
        _, Rs, _, _ = cv2.decomposeHomographyMat(H, np.eye(3))
        
        # Check rotation angles in each solution
        for R in Rs:
            # Convert rotation matrix to Euler angles
            euler_angles = rotation_matrix_to_euler_angles(R) * 180 / np.pi
            
            # Check if rotation is within acceptable range
            if all(abs(angle) <= max_angle for angle in euler_angles):
                return True
                
        return False
    except Exception as e:
        # If decomposition fails, be conservative
        print(f"Homography decomposition failed: {e}")
        return False

def rotation_matrix_to_euler_angles(R):
    """Convert rotation matrix to Euler angles in radians."""
    sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])
    singular = sy < 1e-6
    
    if not singular:
        x = np.arctan2(R[2, 1], R[2, 2])
        y = np.arctan2(-R[2, 0], sy)
        z = np.arctan2(R[1, 0], R[0, 0])
    else:
        x = np.arctan2(-R[1, 2], R[1, 1])
        y = np.arctan2(-R[2, 0], sy)
        z = 0
        
    return np.array([x, y, z])

def visualize_results(results, output_folder="results"):
    """Save and display results."""
    os.makedirs(output_folder, exist_ok=True)
    
    success_count = 0
    for i, (path, result) in enumerate(results.items()):
        if result['success']:
            success_count += 1
            
            # Save enhanced visualization images
            plt.imsave(os.path.join(output_folder, f"detected_{path.stem}.jpg"), 
                       result['result_img'])
            
            # Save comparison view
            plt.imsave(os.path.join(output_folder, f"comparison_{path.stem}.jpg"), 
                       result['split_view'])
    
    # Create and save summary bar chart
    plt.figure(figsize=(12, 8))
    paths = list(results.keys())
    scores = [results[p]['score'] for p in paths]
    success = [results[p]['success'] for p in paths]
    
    # Sort by score
    sorted_indices = np.argsort(scores)[::-1]  # Descending order
    sorted_paths = [paths[i].stem for i in sorted_indices]
    sorted_scores = [scores[i] for i in sorted_indices]
    sorted_success = [success[i] for i in sorted_indices]
    
    # Plot bar chart
    bars = plt.bar(range(len(sorted_paths)), sorted_scores, color=['green' if s else 'red' for s in sorted_success])
    plt.xticks(range(len(sorted_paths)), sorted_paths, rotation=45, ha='right')
    plt.ylabel('Match Score')
    plt.title(f'Artwork Detection Results - {success_count}/{len(results)} images')
    plt.tight_layout()
    
    # Add score values on top of bars
    for bar, score in zip(bars, sorted_scores):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                 f'{score:.2f}', ha='center', va='bottom')
    
    plt.savefig(os.path.join(output_folder, "summary.jpg"), dpi=300)
    
    # Create an HTML report with all results for easier viewing
    create_html_report(results, output_folder)
    
    return os.path.join(output_folder, "summary.jpg")

def create_html_report(results, output_folder):
    """Create an HTML report with all detection results for easier viewing."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Artwork Detection Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .result-container { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
            .result-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
            .score { font-size: 24px; font-weight: bold; }
            .success { color: green; }
            .failure { color: red; }
            img { max-width: 100%; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
            h1, h2 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Artwork Detection Results</h1>
    """
    
    # Sort results by score
    paths = list(results.keys())
    sorted_paths = sorted(paths, key=lambda p: results[p]['score'], reverse=True)
    
    for path in sorted_paths:
        result = results[path]
        score = result['score']
        success = result['success']
        status_class = "success" if success else "failure"
        status_text = "DETECTED" if success else "NOT DETECTED"
        
        html_content += f"""
        <div class="result-container">
            <div class="result-header">
                <h2>{path.name}</h2>
                <div class="score {status_class}">{status_text} (Score: {score:.2f})</div>
            </div>
        """
        
        if success:
            comparison_path = f"comparison_{path.stem}.jpg"
            html_content += f"""
            <img src="{comparison_path}" alt="Comparison view">
            """
        else:
            html_content += f"<p>No artwork detected in this image.</p>"
        
        html_content += "</div>"
    
    html_content += """
        <div>
            <h2>Summary</h2>
            <img src="summary.jpg" alt="Summary Chart">
        </div>
    </body>
    </html>
    """
    
    # Write HTML report
    with open(os.path.join(output_folder, "report.html"), "w") as f:
        f.write(html_content)

def main():
    script_dir = Path(__file__).parent.absolute()
    artwork_path = script_dir / "data-qr-ratio-finder" / "template-to-match" / "image.png"
    data_folder = script_dir / "data-qr-ratio-finder"
    output_folder = script_dir / "results"
    
    # Load images
    try:
        artwork, target_files = load_images(artwork_path, data_folder)
        print(f"Loaded artwork image from {artwork_path}")
        print(f"Found {len(target_files)} images to analyze")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    # Process each target image
    results = {}
    for target_path in target_files:
        print(f"Processing {target_path.name}...")
        result = find_artwork_in_image(artwork, target_path)
        results[target_path] = result
        
        status = "✅ Found" if result["success"] else "❌ Not found"
        score = f"{result['score']:.2f}"
        print(f"  {status} with score: {score}")
    
    # Create visualization of results
    summary_path = visualize_results(results, output_folder)
    
    print("\nSummary of results:")
    print("-" * 60)
    success_count = sum(1 for r in results.values() if r['success'])
    print(f"Artwork found in {success_count} out of {len(results)} images.")
    print(f"Results saved to: {output_folder}")
    print(f"Summary chart: {output_folder}/summary.jpg")
    print(f"Detailed HTML report: {output_folder}/report.html")
    
    # Open the HTML report if on a system with a browser
    report_path = os.path.join(output_folder, "report.html")
    if os.path.exists(report_path):
        print(f"\nTip: Open {report_path} in a web browser to view detailed results.")

if __name__ == "__main__":
    main()
