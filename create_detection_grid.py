#!/usr/bin/env python3
"""
QR Detection Results Grid Generator
Creates a visual grid showing all detected QR patterns from the enhanced detector
"""

import cv2
import numpy as np
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec

class QRDetectionGridGenerator:
    def __init__(self, results_dir="results/enhanced-strict-qr-results", data_dir="data-qr-ratio-finder"):
        self.results_dir = Path(results_dir)
        self.data_dir = Path(data_dir)
        self.grid_output_dir = Path("results/detection-grid")
        self.grid_output_dir.mkdir(parents=True, exist_ok=True)
        
    def load_detection_results(self):
        """Load all detection results from JSON files"""
        results = {}
        
        if not self.results_dir.exists():
            print(f"❌ Results directory not found: {self.results_dir}")
            return results
            
        for json_file in self.results_dir.glob("*_results.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    image_name = json_file.stem.replace('_results', '')
                    results[image_name] = data
                    print(f"✅ Loaded results for: {image_name}")
            except Exception as e:
                print(f"❌ Error loading {json_file}: {e}")
                
        return results
    
    def create_individual_detection_image(self, image_name, detection_data):
        """Create annotated image showing detected patterns"""
        # Load original image
        image_path = self.data_dir / f"{image_name}.png"
        if not image_path.exists():
            # Try other extensions
            for ext in ['.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                alt_path = self.data_dir / f"{image_name}{ext}"
                if alt_path.exists():
                    image_path = alt_path
                    break
        
        if not image_path.exists():
            print(f"❌ Image not found: {image_name}")
            return None
            
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"❌ Could not load image: {image_path}")
            return None
            
        # Convert BGR to RGB for matplotlib
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        ax.imshow(image_rgb)
        ax.set_title(f"{image_name}\n{len(detection_data.get('patterns', []))} patterns detected", 
                    fontsize=12, fontweight='bold')
        ax.axis('off')
        
        # Colors for different patterns
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'yellow']
        
        # Draw detected patterns
        patterns = detection_data.get('patterns', [])
        for i, pattern in enumerate(patterns):
            center = pattern.get('center', {})
            cx, cy = center.get('x', 0), center.get('y', 0)
            size = pattern.get('size', 20)
            score = pattern.get('score', 0)
            
            color = colors[i % len(colors)]
            
            # Draw bounding box
            bbox = patches.Rectangle((cx - size//2, cy - size//2), size, size, 
                                   linewidth=2, edgecolor=color, facecolor='none')
            ax.add_patch(bbox)
            
            # Draw center point
            ax.plot(cx, cy, 'o', color=color, markersize=8, markeredgecolor='white', markeredgewidth=1)
            
            # Add pattern number and score
            ax.text(cx, cy - size//2 - 10, f"{i+1}", color=color, fontsize=14, 
                   fontweight='bold', ha='center', va='bottom',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            
            # Add score below
            ax.text(cx, cy + size//2 + 5, f"{score:.3f}", color=color, fontsize=10, 
                   fontweight='bold', ha='center', va='top',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        # Add summary info
        total_score = sum(p.get('score', 0) for p in patterns)
        avg_score = total_score / len(patterns) if patterns else 0
        
        info_text = f"Patterns: {len(patterns)}\nAvg Score: {avg_score:.3f}"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", 
               facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        return fig
    
    def create_summary_grid(self, all_results):
        """Create a grid showing all detection results"""
        n_images = len(all_results)
        if n_images == 0:
            print("❌ No results to display")
            return None
            
        # Calculate grid dimensions
        cols = min(4, n_images)  # Max 4 columns
        rows = (n_images + cols - 1) // cols
        
        # Create large figure
        fig = plt.figure(figsize=(5 * cols, 4 * rows))
        fig.suptitle('🔍 QR Finder Pattern Detection Results - Enhanced with Symmetry Analysis', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        # Create grid
        gs = GridSpec(rows, cols, figure=fig, hspace=0.3, wspace=0.2)
        
        # Process each image
        for idx, (image_name, detection_data) in enumerate(sorted(all_results.items())):
            row = idx // cols
            col = idx % cols
            
            ax = fig.add_subplot(gs[row, col])
            
            # Load and display image
            image_path = self.data_dir / f"{image_name}.png"
            if not image_path.exists():
                # Try other extensions
                for ext in ['.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                    alt_path = self.data_dir / f"{image_name}{ext}"
                    if alt_path.exists():
                        image_path = alt_path
                        break
            
            if image_path.exists():
                image = cv2.imread(str(image_path))
                if image is not None:
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    ax.imshow(image_rgb)
                    
                    # Draw patterns
                    patterns = detection_data.get('patterns', [])
                    colors = ['red', 'blue', 'green', 'orange']
                    
                    for i, pattern in enumerate(patterns):
                        center = pattern.get('center', {})
                        cx, cy = center.get('x', 0), center.get('y', 0)
                        size = pattern.get('size', 20)
                        score = pattern.get('score', 0)
                        
                        color = colors[i % len(colors)]
                        
                        # Draw bounding box
                        bbox = patches.Rectangle((cx - size//2, cy - size//2), size, size, 
                                               linewidth=2, edgecolor=color, facecolor='none')
                        ax.add_patch(bbox)
                        
                        # Draw center with number
                        ax.plot(cx, cy, 'o', color=color, markersize=6, 
                               markeredgecolor='white', markeredgewidth=1)
                        ax.text(cx, cy, f"{i+1}", color='white', fontsize=8, 
                               fontweight='bold', ha='center', va='center')
            
            # Title with stats
            patterns = detection_data.get('patterns', [])
            avg_score = np.mean([p.get('score', 0) for p in patterns]) if patterns else 0
            symmetry_scores = []
            for p in patterns:
                analysis = p.get('analysis', {})
                symmetry = analysis.get('symmetry', {})
                if 'score' in symmetry:
                    symmetry_scores.append(symmetry['score'])
            
            avg_symmetry = np.mean(symmetry_scores) if symmetry_scores else 0
            
            title = f"{image_name}\n{len(patterns)} patterns"
            if patterns:
                title += f"\nScore: {avg_score:.3f}"
                if symmetry_scores:
                    title += f"\nSym: {avg_symmetry:.3f}"
            
            ax.set_title(title, fontsize=9, fontweight='bold')
            ax.axis('off')
        
        plt.tight_layout()
        return fig
    
    def create_statistics_summary(self, all_results):
        """Create detailed statistics visualization"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('📊 QR Detection Statistics - Enhanced with Symmetry Analysis', 
                    fontsize=16, fontweight='bold')
        
        # Collect all data
        image_names = []
        pattern_counts = []
        avg_scores = []
        max_scores = []
        symmetry_scores = []
        line_scores = []
        concentric_scores = []
        
        for image_name, data in sorted(all_results.items()):
            patterns = data.get('patterns', [])
            image_names.append(image_name.replace('image copy ', 'img'))
            pattern_counts.append(len(patterns))
            
            if patterns:
                scores = [p.get('score', 0) for p in patterns]
                avg_scores.append(np.mean(scores))
                max_scores.append(max(scores))
                
                # Extract detailed scores
                for p in patterns:
                    analysis = p.get('analysis', {})
                    
                    # Symmetry scores
                    symmetry = analysis.get('symmetry', {})
                    if 'score' in symmetry:
                        symmetry_scores.append(symmetry['score'])
                    
                    # Line pattern scores
                    line_score = analysis.get('line_pattern_score', 0)
                    if line_score > 0:
                        line_scores.append(line_score)
                    
                    # Concentric scores
                    concentric = analysis.get('concentric', {})
                    if 'score' in concentric:
                        concentric_scores.append(concentric['score'])
            else:
                avg_scores.append(0)
                max_scores.append(0)
        
        # 1. Pattern counts per image
        ax1.bar(range(len(image_names)), pattern_counts, color='skyblue', alpha=0.7)
        ax1.set_title('Patterns Detected per Image', fontweight='bold')
        ax1.set_xlabel('Images')
        ax1.set_ylabel('Number of Patterns')
        ax1.set_xticks(range(len(image_names)))
        ax1.set_xticklabels(image_names, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Add count labels on bars
        for i, count in enumerate(pattern_counts):
            ax1.text(i, count + 0.1, str(count), ha='center', va='bottom', fontweight='bold')
        
        # 2. Score distribution
        ax2.hist([avg_scores, max_scores], bins=15, alpha=0.7, 
                label=['Average Scores', 'Max Scores'], color=['orange', 'red'])
        ax2.set_title('Score Distribution', fontweight='bold')
        ax2.set_xlabel('Score')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Component score comparison
        component_names = ['Symmetry', 'Line Pattern', 'Concentric']
        component_scores = [symmetry_scores, line_scores, concentric_scores]
        component_colors = ['green', 'blue', 'purple']
        
        bp = ax3.boxplot(component_scores, labels=component_names, patch_artist=True)
        for patch, color in zip(bp['boxes'], component_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax3.set_title('Component Score Analysis', fontweight='bold')
        ax3.set_ylabel('Score')
        ax3.grid(True, alpha=0.3)
        
        # 4. Overall statistics table
        ax4.axis('off')
        
        # Calculate statistics
        total_patterns = sum(pattern_counts)
        images_with_patterns = sum(1 for count in pattern_counts if count > 0)
        overall_avg_score = np.mean([s for s in avg_scores if s > 0])
        overall_max_score = max(max_scores) if max_scores else 0
        
        avg_symmetry = np.mean(symmetry_scores) if symmetry_scores else 0
        avg_line = np.mean(line_scores) if line_scores else 0
        avg_concentric = np.mean(concentric_scores) if concentric_scores else 0
        
        stats_text = f"""
🔍 ENHANCED QR DETECTION SUMMARY
{'='*40}

📊 Overall Statistics:
• Total Images Processed: {len(all_results)}
• Images with Patterns: {images_with_patterns}
• Total Patterns Found: {total_patterns}
• Average Patterns per Image: {total_patterns/len(all_results):.1f}

📈 Score Analysis:
• Overall Average Score: {overall_avg_score:.3f}
• Highest Pattern Score: {overall_max_score:.3f}

🔧 Component Scores:
• Average Symmetry Score: {avg_symmetry:.3f}
• Average Line Pattern Score: {avg_line:.3f}
• Average Concentric Score: {avg_concentric:.3f}

✨ NEW FEATURES:
• Symmetry Analysis: 25% weight
• Enhanced Line Patterns: 60% weight  
• Concentric Structure: 15% weight

🎯 Quality Indicators:
• High Symmetry Patterns: {sum(1 for s in symmetry_scores if s >= 0.8)}
• Perfect Line Patterns: {sum(1 for s in line_scores if s >= 1.0)}
        """
        
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        return fig
    
    def generate_all_grids(self):
        """Generate all visualization grids"""
        print("🔍 Loading detection results...")
        all_results = self.load_detection_results()
        
        if not all_results:
            print("❌ No detection results found!")
            return
        
        print(f"✅ Loaded results for {len(all_results)} images")
        
        # 1. Create summary grid
        print("📊 Creating summary grid...")
        summary_fig = self.create_summary_grid(all_results)
        if summary_fig:
            summary_path = self.grid_output_dir / "qr_detection_summary_grid.png"
            summary_fig.savefig(summary_path, dpi=300, bbox_inches='tight')
            print(f"✅ Summary grid saved: {summary_path}")
            plt.close(summary_fig)
        
        # 2. Create individual detection images
        print("🖼️  Creating individual detection images...")
        for image_name, detection_data in all_results.items():
            fig = self.create_individual_detection_image(image_name, detection_data)
            if fig:
                individual_path = self.grid_output_dir / f"{image_name}_detailed.png"
                fig.savefig(individual_path, dpi=300, bbox_inches='tight')
                print(f"✅ Individual image saved: {individual_path}")
                plt.close(fig)
        
        # 3. Create statistics summary
        print("📈 Creating statistics summary...")
        stats_fig = self.create_statistics_summary(all_results)
        if stats_fig:
            stats_path = self.grid_output_dir / "qr_detection_statistics.png"
            stats_fig.savefig(stats_path, dpi=300, bbox_inches='tight')
            print(f"✅ Statistics summary saved: {stats_path}")
            plt.close(stats_fig)
        
        print(f"\n🎉 All grids generated successfully!")
        print(f"📁 Output directory: {self.grid_output_dir}")
        
        # List all generated files
        generated_files = list(self.grid_output_dir.glob("*.png"))
        print(f"\n📋 Generated Files:")
        for file_path in sorted(generated_files):
            file_size = file_path.stat().st_size / 1024  # KB
            print(f"   • {file_path.name} ({file_size:.1f} KB)")

def main():
    print("🔍 QR Detection Grid Generator")
    print("=" * 50)
    
    generator = QRDetectionGridGenerator()
    generator.generate_all_grids()

if __name__ == "__main__":
    main()
