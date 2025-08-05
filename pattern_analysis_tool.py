#!/usr/bin/env python3
"""
QR Pattern Analysis Tool
Analyzes why a specific pattern was detected as a QR finder pattern
"""

import json
import sys
from pathlib import Path

def analyze_pattern_detection(image_name, pattern_center):
    """Analyze why a specific pattern was detected"""
    
    results_file = f"results/enhanced-strict-qr-results/{image_name}_results.json"
    
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Results file not found: {results_file}")
        return
    
    # Find the target pattern
    target_pattern = None
    for pattern in data['patterns']:
        center = pattern['center']
        if abs(center['x'] - pattern_center[0]) < 5 and abs(center['y'] - pattern_center[1]) < 5:
            target_pattern = pattern
            break
    
    if not target_pattern:
        print(f"❌ Pattern not found at {pattern_center}")
        return
    
    print(f"🔍 PATTERN DETECTION ANALYSIS")
    print(f"Image: {image_name}")
    print(f"Pattern Location: ({target_pattern['center']['x']}, {target_pattern['center']['y']})")
    print("=" * 60)
    
    analysis = target_pattern['analysis']
    
    print(f"📊 OVERALL ASSESSMENT:")
    print(f"   Final Score: {target_pattern['score']:.3f}")
    print(f"   Size: {target_pattern['size']}px")
    print(f"   Detection Method: {target_pattern['method']}")
    print(f"   Status: {'✅ DETECTED' if target_pattern['score'] > 0.5 else '❌ REJECTED'}")
    
    print(f"\n🎯 COMPONENT SCORES:")
    print(f"   Line Pattern: {analysis['line_pattern_score']:.3f}")
    print(f"   Symmetry: {analysis['symmetry_score']:.3f}")
    print(f"   Concentric: {analysis['concentric']['score']:.3f}")
    
    # Calculate component weights (from our scoring system)
    line_weight = 0.60  # 60% weight
    symmetry_weight = 0.25  # 25% weight  
    concentric_weight = 0.15  # 15% weight
    
    print(f"\n⚖️  WEIGHTED CONTRIBUTION:")
    line_contrib = analysis['line_pattern_score'] * line_weight
    symmetry_contrib = analysis['symmetry_score'] * symmetry_weight
    concentric_contrib = analysis['concentric']['score'] * concentric_weight
    
    print(f"   Line Pattern: {analysis['line_pattern_score']:.3f} × {line_weight} = {line_contrib:.3f}")
    print(f"   Symmetry: {analysis['symmetry_score']:.3f} × {symmetry_weight} = {symmetry_contrib:.3f}")
    print(f"   Concentric: {analysis['concentric']['score']:.3f} × {concentric_weight} = {concentric_contrib:.3f}")
    print(f"   Total: {line_contrib + symmetry_contrib + concentric_contrib:.3f}")
    
    print(f"\n📏 LINE PATTERN ANALYSIS (Primary Factor - 60% weight):")
    print(f"   Score: {analysis['line_pattern_score']:.3f} ({'✅ PASSED' if analysis['line_pattern_score'] >= 0.5 else '❌ FAILED'})")
    
    # Analyze line results
    valid_directions = 0
    for line_result in analysis['line_results']:
        direction = line_result['direction']
        score = line_result.get('score', 0)
        if score > 0:
            valid_directions += 1
            runs = line_result['runs']
            print(f"   {direction}: Score {score:.3f}, Runs: {runs}")
            
            if 'ratios' in line_result:
                ratios = line_result['ratios']
                ideal = [0.125, 0.125, 0.375, 0.125, 0.125]
                print(f"     Actual Ratios: {[f'{r:.3f}' for r in ratios]}")
                print(f"     Ideal Ratios:  {[f'{r:.3f}' for r in ideal]}")
                
                # Calculate how close to ideal 1:1:3:1:1 pattern
                deviations = [abs(actual - ideal[i]) for i, actual in enumerate(ratios)]
                avg_deviation = sum(deviations) / len(deviations)
                print(f"     Average Deviation: {avg_deviation:.3f}")
    
    print(f"   Valid Directions: {valid_directions}/4")
    
    print(f"\n🔄 SYMMETRY ANALYSIS (25% weight):")
    symmetry = analysis['symmetry']
    print(f"   Score: {symmetry['score']:.3f} ({'✅ PASSED' if symmetry['score'] >= 0.5 else '❌ FAILED'})")
    print(f"   Horizontal Similarity: {symmetry['horizontal_similarity']:.3f}")
    print(f"   Vertical Similarity: {symmetry['vertical_similarity']:.3f}")
    print(f"   Combined Symmetry: {symmetry['combined_symmetry']:.3f}")
    
    print(f"\n⭕ CONCENTRIC ANALYSIS (15% weight):")
    concentric = analysis['concentric']
    print(f"   Score: {concentric['score']:.3f} ({'✅ PASSED' if concentric['score'] >= 0.5 else '❌ FAILED'})")
    print(f"   Center Dark: {concentric['center_dark']}")
    print(f"   Ring Count: {concentric['ring_count']}")
    
    print(f"   Ring Pattern:")
    for i, ring in enumerate(concentric['rings']):
        radius = ring['radius']
        ring_type = ring['type']
        dark_count = ring['dark_count']
        light_count = ring['light_count']
        print(f"     Ring {i+1} (r={radius}): {ring_type} ({dark_count}D/{light_count}L)")
    
    print(f"\n🏆 DETECTION DECISION:")
    threshold = 0.5
    passed = target_pattern['score'] >= threshold
    print(f"   Threshold: {threshold}")
    print(f"   Final Score: {target_pattern['score']:.3f}")
    print(f"   Result: {'✅ DETECTED as QR Finder Pattern' if passed else '❌ REJECTED'}")
    
    if passed:
        print(f"\n🔍 WHY IT QUALIFIED:")
        reasons = []
        if analysis['line_pattern_score'] >= 0.8:
            reasons.append(f"✅ Excellent line pattern score ({analysis['line_pattern_score']:.3f})")
        elif analysis['line_pattern_score'] >= 0.5:
            reasons.append(f"✅ Good line pattern score ({analysis['line_pattern_score']:.3f})")
            
        if analysis['symmetry_score'] >= 0.8:
            reasons.append(f"✅ High symmetry ({analysis['symmetry_score']:.3f})")
        elif analysis['symmetry_score'] >= 0.5:
            reasons.append(f"✅ Adequate symmetry ({analysis['symmetry_score']:.3f})")
        else:
            reasons.append(f"⚠️  Low symmetry ({analysis['symmetry_score']:.3f}) but compensated by other factors")
            
        if analysis['concentric']['score'] >= 0.5:
            reasons.append(f"✅ Valid concentric structure ({analysis['concentric']['score']:.3f})")
        else:
            reasons.append(f"⚠️  Weak concentric structure ({analysis['concentric']['score']:.3f}) but compensated")
            
        for reason in reasons:
            print(f"   {reason}")
    
    print(f"\n📝 SUMMARY:")
    print(f"   This pattern was detected because it achieved a {target_pattern['score']:.3f} score,")
    print(f"   primarily due to its {analysis['line_pattern_score']:.3f} line pattern score (60% weight).")
    if analysis['line_pattern_score'] == 1.0:
        print(f"   The perfect line pattern score indicates it closely matches the 1:1:3:1:1 QR ratio.")
    if analysis['symmetry_score'] < 0.8:
        print(f"   Lower symmetry score ({analysis['symmetry_score']:.3f}) suggests some geometric irregularity.")
    if analysis['concentric']['score'] < 0.8:
        print(f"   Moderate concentric score ({analysis['concentric']['score']:.3f}) indicates partial ring structure.")

def main():
    # Analyze the 4th pattern in image copy 9
    analyze_pattern_detection("image copy 9", (470, 415))

if __name__ == "__main__":
    main()
