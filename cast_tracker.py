import re
from collections import defaultdict
import matplotlib.pyplot as plt

CAST_PATTERNS = {
    'Kraken Scepter': [
        r'<(.+?)(.+?)\|r successfully cast \|cff57d6aeDesolate Sea Sovereign\|r\|r!',
        r'<(.+?)(.+?)\|r successfully cast \|cff57d6aeArcadian Sea Sovereign\|r\|r!'
    ],
    'Kraken Shield': [
        r'<(.+?)(.+?)\|r gained the buff: \|cff57d6aeArcadian Sea Keeper Stealth\|r\|r\.'
    ],
    'Startling Strain': [
        r'<(.+?)(.+?)\|r successfully cast \|cff57d6aeStartling Strain\|r\|r!'
    ],
    'Stillness': [
        r'<(.+?)(.+?)\|r successfully cast \|cff57d6aeStillness\|r\|r!'
    ],
    'Bubble Trap': [
        r'<(.+?)(.+?)\|r successfully cast \|cff57d6aeBubble Trap\|r\|r!'
    ],
    'Banshee Wail': [
        r'<(.+?)(.+?)\|r successfully cast \|cff57d6aeBanshee Wail\|r\|r!'
    ],
    'Halcy Neck': [
        r'<(.+?)(.+?)\|r successfully cast \|cff57d6aeDeliverance Shield\|r\|r!'
    ],
    'Egirl Neck': [
        r'<(.+?)(.+?)\|r successfully cast \|cff57d6aeHands of Salvation\|r\|r!'
    ]
}

class CastTracker:
    def __init__(self, logfile):
        with open(logfile, 'r', encoding='utf-8') as f:
            self.log_lines = [line for line in f.readlines() 
                            if "successfully cast" in line or 
                               "gained the buff: |cff57d6aeArcadian Sea Keeper Stealth" in line]
        
        # Precompile patterns
        self.compiled_patterns = {
            ability: [re.compile(pattern) for pattern in patterns]
            for ability, patterns in CAST_PATTERNS.items()
        }

    def track_casts(self, patterns):
        cast_counts = defaultdict(lambda: defaultdict(int))
        
        # Pattern to extract timestamp and player name
        timestamp_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.*?)\|r')

        for line in self.log_lines:
            # First extract player name without timestamp
            if timestamp_match := timestamp_pattern.match(line):
                player = timestamp_match.group(2).strip()
                
                # Then check for ability patterns
                for ability_name, compiled_patterns in self.compiled_patterns.items():
                    for pattern in compiled_patterns:
                        if pattern.search(line):
                            cast_counts[ability_name][player] += 1
                            break

        return {ability: dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10])
                for ability, counts in cast_counts.items()
                if counts}

def plot_cast_results(cast_data, color='purple'):
    if not cast_data:
        return None
    
    # Ensure minimum height for consistency
    min_height = 4
    height = max(min_height, len(cast_data) * 0.4)
    
    fig, ax = plt.subplots(figsize=(10, height))
    players = list(cast_data.keys())
    counts = list(cast_data.values())
    
    bars = ax.barh(range(len(players)), counts, color=color)
    ax.set_yticks(range(len(players)))
    ax.set_yticklabels(players)
    ax.invert_yaxis()
    ax.set_xlabel('Number of Casts')
    ax.grid(True, alpha=0.3)
    
    # Add count labels
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2, 
                f'{int(width)}', va='center', ha='left', fontsize=10)
    
    plt.tight_layout(pad=1.2)
    return fig
