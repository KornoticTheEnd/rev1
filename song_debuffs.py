import matplotlib.pyplot as plt
import re
from datetime import datetime

# Constants
DEBUFF_TYPES = [
    'unguarded',
    'lethargy (bloody chantey)',
    'unpleasant sensation (quickstep)'
]

DEBUFF_COLORS = ['#3a5cc3', '#b61233', '#cd8500']
DEBUFF_LABELS = ['Unguarded', 'Lethargy', 'Unpleasant Sensation']

def parse_debuff_data(file_path):
    debuff_data = {}  # {player: {debuff_type: duration}}
    current_debuffs = {}  # {player: {debuff_type: start_time}}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if 'struck by a' not in line or 'debuff!' not in line:
                continue
                
            # Parse timestamp and player
            timestamp_match = re.match(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.*?)\|r was struck', line)
            if not timestamp_match:
                continue
                
            timestamp_str = timestamp_match.group(1)
            player = timestamp_match.group(2)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Parse debuff name
            debuff_match = re.search(r'\|cff57d6ae(.*?)\|r\|r', line)
            if not debuff_match:
                continue
                
            debuff_name = debuff_match.group(1).lower()
            
            # Only process registered debuff types
            normalized_debuff = next((d for d in DEBUFF_TYPES if d in debuff_name.lower()), None)
            if not normalized_debuff:
                continue
                
            # Initialize tracking
            if player not in current_debuffs:
                current_debuffs[player] = {}
                debuff_data[player] = {debuff: 0 for debuff in DEBUFF_TYPES}
                
            # If debuff was already active, add duration
            if normalized_debuff in current_debuffs[player]:
                duration = (timestamp - current_debuffs[player][normalized_debuff]).total_seconds()
                if duration > 5:  # Max debuff duration
                    duration = 5
                debuff_data[player][normalized_debuff] += duration
                
            current_debuffs[player][normalized_debuff] = timestamp
            
    return debuff_data

def plot_debuff_data(file_path):
    debuff_data = parse_debuff_data(file_path)
    
    # Sort players by total debuff duration
    sorted_players = sorted(debuff_data.items(), 
                          key=lambda x: sum(x[1].values()),
                          reverse=True)  # Keep True for highest first
    
    # Create plot
    fig, ax = plt.subplots(figsize=(15, 10))
    bar_height = 0.15
    y_positions = []
    
    # Start plotting from top (highest y value) down
    total_players = min(len(sorted_players), 20)
    max_y = total_players * 0.6
    
    for i, (player, debuffs) in enumerate(sorted_players[:20]):
        base_y = max_y - (i * 0.6)  # Start from top position
        
        for j, (debuff_type, color) in enumerate(zip(DEBUFF_TYPES, DEBUFF_COLORS)):
            duration = debuffs[debuff_type]
            y_pos = base_y + (j * bar_height)
            ax.barh(y_pos, duration, height=bar_height, color=color, 
                   label=DEBUFF_LABELS[j] if i == 0 else "")
            if j == 1:  # Middle position for player label
                y_positions.append(base_y + bar_height)
    
    # Customize plot
    ax.set_yticks(y_positions)
    ax.set_yticklabels([player for player, _ in sorted_players[:20]], fontsize=10)
    ax.set_xlabel('Duration (seconds)', fontsize=12)
    ax.set_title('Song Debuff Duration by Player', fontsize=14, pad=20)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(axis='x', alpha=0.3)
    
    # Remove y-axis inversion
    # plt.gca().invert_yaxis()
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    return fig

def plot_song_debuff_data(file_path):
    return plot_debuff_data(file_path)

if __name__ == "__main__":
    test_file = "path/to/your/logfile.log"
    fig = plot_song_debuff_data(test_file)
    plt.show()
