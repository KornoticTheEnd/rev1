import matplotlib.pyplot as plt
import re
from datetime import datetime

# Constants
BUFF_TYPES = [
    'bloody chantey (rank 2)',
    'bulwark ballad (rank 2)', 
    'quickstep (rank 5)'
]

BUFF_COLORS = ['#3a5cc3', '#b61233', '#cd8500']
BUFF_LABELS = ['Bloody Chantey', 'Bulwark Ballad', 'Quickstep']

def parse_buff_data(file_path):
    buff_data = {}  # {player: {buff_type: duration}}
    current_buffs = {}  # {player: {buff_type: start_time}}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if 'gained the buff:' not in line:
                continue
                
            # Parse timestamp and player
            timestamp_match = re.match(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.*?)\|r gained the buff:', line)
            if not timestamp_match:
                continue
                
            timestamp_str = timestamp_match.group(1)
            player = timestamp_match.group(2)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            
            # Parse buff name
            buff_match = re.search(r'\|cff57d6ae(.*?)\|r\|r', line)
            if not buff_match:
                continue
                
            buff_name = buff_match.group(1).lower()
            
            # Only process registered buff types
            normalized_buff = next((b for b in BUFF_TYPES if b in buff_name.lower()), None)
            if not normalized_buff:
                continue
                
            # Initialize tracking
            if player not in current_buffs:
                current_buffs[player] = {}
                buff_data[player] = {buff: 0 for buff in BUFF_TYPES}
                
            # If buff was already active, add duration
            if normalized_buff in current_buffs[player]:
                duration = (timestamp - current_buffs[player][normalized_buff]).total_seconds()
                if duration > 5:  # Max buff duration
                    duration = 5
                buff_data[player][normalized_buff] += duration
                
            current_buffs[player][normalized_buff] = timestamp
            
    return buff_data

def plot_buff_data(file_path, ax=None):
    buff_data = parse_buff_data(file_path)
    
    # Sort players by total buff duration
    sorted_players = sorted(buff_data.items(), 
                          key=lambda x: sum(x[1].values()),
                          reverse=True)
    
    # Create plot
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    bar_height = 0.2
    y_positions = []
    
    for i, (player, buffs) in enumerate(sorted_players[:20]):  # Top 20 players
        base_y = i * 0.8
        
        for j, (buff_type, color) in enumerate(zip(BUFF_TYPES, BUFF_COLORS)):
            duration = buffs[buff_type]
            y_pos = base_y + (j * bar_height)
            ax.barh(y_pos, duration, height=bar_height, color=color, 
                   label=BUFF_LABELS[j] if i == 0 else "")
            if j == 1:  # Middle position for label
                y_positions.append(y_pos)
    
    # Customize plot
    ax.set_yticks(y_positions)
    ax.set_yticklabels([player for player, _ in sorted_players[:20]])
    ax.set_xlabel('Duration (seconds)')
    ax.set_title('Song Buff Duration by Player')
    ax.legend(loc='upper right')
    plt.grid(axis='x', alpha=0.3)
    
    # Add y-axis inversion
    plt.gca().invert_yaxis()
    
    plt.tight_layout()
    
    return ax.figure

def plot_song_buff_data(file_path, ax=None):
    return plot_buff_data(file_path, ax)