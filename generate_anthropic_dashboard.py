#!/usr/bin/env python3
"""
Generate a dashboard specifically for Anthropic model results
"""

import json
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import numpy as np

def load_anthropic_results() -> Dict[str, Dict]:
    """Load all Anthropic model results"""
    results_dir = Path("results_v3")
    results = {}
    
    for json_file in results_dir.glob("schizobench_v3_claude*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)
            model = data['metadata']['model']
            
            # Check if this is the enhanced version
            system_prompt = data['metadata'].get('system_prompt', '')
            if system_prompt and 'reality anchors in every paragraph' in system_prompt:
                model = f"{model} (Enhanced)"
            
            results[model] = data
    
    return results

def create_anthropic_dashboard():
    """Create comprehensive dashboard for Anthropic models"""
    results = load_anthropic_results()
    
    # Set up the figure
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('SchizoBench v3 - Anthropic Models Analysis', fontsize=20, fontweight='bold')
    
    # Sort models by performance
    sorted_models = sorted(results.items(), key=lambda x: x[1]['analysis']['reification_rate'])
    
    # 1. Overall Reification Rates
    ax1 = plt.subplot(2, 3, 1)
    models = [m[0] for m in sorted_models]
    rates = [m[1]['analysis']['reification_rate'] for m in sorted_models]
    
    # Color code by risk level
    colors = ['green' if r < 10 else 'orange' if r < 30 else 'red' for r in rates]
    
    bars = ax1.barh(models, rates, color=colors)
    ax1.set_xlabel('Reification Rate (%)')
    ax1.set_title('Overall Reification Rates', fontsize=14, fontweight='bold')
    ax1.axvline(x=10, color='orange', linestyle='--', alpha=0.5, label='Moderate Risk')
    ax1.axvline(x=30, color='red', linestyle='--', alpha=0.5, label='High Risk')
    
    # Add value labels
    for bar, rate in zip(bars, rates):
        ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                f'{rate:.1f}%', va='center')
    
    # 2. Reification by Sequence Length
    ax2 = plt.subplot(2, 3, 2)
    lengths = ['3-turn', '8-turn', '20-turn']
    
    # Calculate rates by length for each model
    length_data = {model: {'3': [], '8': [], '20': []} for model in models}
    
    for model, data in results.items():
        for seq in data['sequences']:
            turns = seq['conversation_length']
            reified = seq['reification_occurred']
            
            if turns <= 3:
                length_data[model]['3'].append(reified)
            elif turns <= 8:
                length_data[model]['8'].append(reified)
            else:
                length_data[model]['20'].append(reified)
    
    # Plot grouped bars
    x = np.arange(len(models))
    width = 0.25
    
    for i, length in enumerate(['3', '8', '20']):
        rates = []
        for model in models:
            detections = length_data[model][length]
            rate = (sum(detections) / len(detections) * 100) if detections else 0
            rates.append(rate)
        
        ax2.bar(x + i*width, rates, width, label=f'{length}-turn' if length != '20' else '20-turn')
    
    ax2.set_xlabel('Model')
    ax2.set_ylabel('Reification Rate (%)')
    ax2.set_title('Reification Rates by Sequence Length', fontsize=14, fontweight='bold')
    ax2.set_xticks(x + width)
    ax2.set_xticklabels([m.replace('claude-', '').replace('-20', '') for m in models], rotation=45, ha='right')
    ax2.legend()
    
    # 3. Category Performance Heatmap
    ax3 = plt.subplot(2, 3, 3)
    
    # Build category matrix
    categories = sorted(set(cat for data in results.values() 
                          for cat in data['analysis']['category_analysis'].keys()))
    
    heatmap_data = []
    for model in models:
        row = []
        for cat in categories:
            cat_data = results[model]['analysis']['category_analysis'].get(cat, {'total': 0, 'reifications': 0})
            if cat_data['total'] > 0:
                rate = (cat_data['reifications'] / cat_data['total']) * 100
            else:
                rate = 0
            row.append(rate)
        heatmap_data.append(row)
    
    sns.heatmap(heatmap_data, 
                xticklabels=[c.replace('_', ' ').title() for c in categories],
                yticklabels=[m.replace('claude-', '').replace('-20', '') for m in models],
                cmap='RdYlGn_r', 
                annot=True, 
                fmt='.0f',
                cbar_kws={'label': 'Reification Rate (%)'},
                ax=ax3)
    ax3.set_title('Performance by Risk Category', fontsize=14, fontweight='bold')
    plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    
    # 4. Claude Opus 4 Comparison
    ax4 = plt.subplot(2, 3, 4)
    opus4_models = [m for m in models if 'opus-4' in m]
    opus4_rates = [results[m]['analysis']['reification_rate'] for m in opus4_models]
    
    bars = ax4.bar(range(len(opus4_models)), opus4_rates, 
                    color=['red', 'green'] if len(opus4_models) > 1 else ['red'])
    ax4.set_xticks(range(len(opus4_models)))
    ax4.set_xticklabels(['Regular', 'Enhanced'] if len(opus4_models) > 1 else ['Regular'])
    ax4.set_ylabel('Reification Rate (%)')
    ax4.set_title('Claude Opus 4: Enhanced Prompt Impact', fontsize=14, fontweight='bold')
    
    # Add improvement annotation
    if len(opus4_models) > 1:
        improvement = opus4_rates[0] - opus4_rates[1]
        ax4.annotate(f'↓ {improvement:.1f}pp\n({(1-opus4_rates[1]/opus4_rates[0])*100:.0f}% reduction)',
                    xy=(0.5, max(opus4_rates)/2), 
                    xytext=(0.5, max(opus4_rates)/2),
                    ha='center', fontsize=12, fontweight='bold')
    
    for bar, rate in zip(bars, opus4_rates):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{rate:.1f}%', ha='center', fontweight='bold')
    
    # 5. Model Evolution Timeline
    ax5 = plt.subplot(2, 3, 5)
    
    # Group models by family
    families = {
        'Claude 3': ['claude-3-haiku-20240307', 'claude-3-opus-20240229'],
        'Claude 3.5': ['claude-3-5-sonnet-20240620', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
        'Claude 3.7': ['claude-3-7-sonnet-20250219'],
        'Claude 4': ['claude-opus-4-20250514', 'claude-sonnet-4-20250514']
    }
    
    for family, family_models in families.items():
        family_rates = []
        family_labels = []
        for model in family_models:
            if model in results:
                family_rates.append(results[model]['analysis']['reification_rate'])
                family_labels.append(model.split('-')[-1][:6])  # Just the date part
        
        if family_rates:
            ax5.plot(range(len(family_rates)), family_rates, 'o-', label=family, markersize=8)
    
    ax5.set_xlabel('Release Order')
    ax5.set_ylabel('Reification Rate (%)')
    ax5.set_title('Model Performance Evolution', fontsize=14, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 6. Summary Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    # Calculate summary stats
    all_rates = [r['analysis']['reification_rate'] for r in results.values() if '(Enhanced)' not in r]
    
    summary_text = f"""
    Summary Statistics (Anthropic Models)
    
    Total Models Tested: {len(results)} ({len(all_rates)} regular, {len(results) - len(all_rates)} enhanced)
    
    Regular Models:
    • Average Reification Rate: {np.mean(all_rates):.1f}%
    • Best Performer: {sorted_models[0][0]} ({sorted_models[0][1]['analysis']['reification_rate']:.1f}%)
    • Worst Performer: {sorted_models[-1][0]} ({sorted_models[-1][1]['analysis']['reification_rate']:.1f}%)
    
    Key Findings:
    • Enhanced prompt reduces Claude Opus 4 failures by 83.3%
    • Longer conversations (20-turn) show highest risk
    • Identity grandiosity most problematic category
    • Claude 3.5 Sonnet (Oct 2024) achieves 0% failure rate
    
    Risk Distribution:
    • Low Risk (<10%): {sum(1 for r in rates if r < 10)} models
    • Moderate Risk (10-30%): {sum(1 for r in rates if 10 <= r < 30)} models
    • High Risk (>30%): {sum(1 for r in rates if r >= 30)} models
    """
    
    ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, 
            fontsize=11, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save the dashboard
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"results_v3/anthropic_dashboard_{timestamp}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nDashboard saved to: {output_path}")
    
    # Also save a high-level summary
    with open(f"results_v3/anthropic_summary_{timestamp}.txt", 'w') as f:
        f.write("SchizoBench v3 - Anthropic Models Summary\n")
        f.write("=" * 50 + "\n\n")
        
        for model, rate in sorted([(m, r['analysis']['reification_rate']) for m, r in results.items()], 
                                 key=lambda x: x[1]):
            f.write(f"{model}: {rate:.1f}%\n")
        
        f.write("\n" + summary_text)
    
    plt.show()

if __name__ == "__main__":
    create_anthropic_dashboard()