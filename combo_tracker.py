import re
from datetime import datetime
import matplotlib.pyplot as plt

class ComboTracker:
    def __init__(self, logfile):
        with open(logfile, 'r', encoding='utf-8') as f:
            self.log_lines = f.readlines()  # Store as lines instead of full string
        
        # Precompile regex patterns
        self.timestamp_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
        self.retribution_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r gained the buff: \|cff57d6aeRetribution\|r\|r\.')
        self.toughen_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r gained the buff: \|cff57d6aeToughened \(Rank 4\)\|r\|r\.')
        self.bull_rush_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r gained the buff: \|cff57d6aeBull Rush: Aggro Boost\|r\|r\.')
        self.distress_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r was struck by a \|cff57d6aeDistressed\|r\|r debuff!')
        self.discord_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r attacked (.+?)\|r using \|cff57d6aeCritical Discord\|r\|r')
        self.dissonance_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r was struck by a \|cff57d6aeDissonance\|r\|r debuff!')
        self.mocking_howl_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r successfully cast \|cff57d6aeMocking Howl\|r\|r!')

    def track_distress_combo(self):
        active_buffs = {}
        success_count = {}
        
        for line in self.log_lines:
            timestamp = self.timestamp_pattern.search(line)
            if not timestamp:
                continue
                
            current_time = datetime.strptime(timestamp.group(1), '%Y-%m-%d %H:%M:%S')
            
            if match := self.retribution_pattern.search(line):
                player = match.group(2).strip()
                if player not in active_buffs:
                    active_buffs[player] = {}
                active_buffs[player]['retribution'] = current_time
            
            elif match := self.toughen_pattern.search(line):
                player = match.group(2).strip()
                if player not in active_buffs:
                    active_buffs[player] = {}
                active_buffs[player]['toughen'] = current_time
            
            elif match := self.bull_rush_pattern.search(line):
                player = match.group(2).strip()
                if player not in active_buffs:
                    active_buffs[player] = {}
                active_buffs[player]['bull_rush'] = current_time
            
            elif match := self.mocking_howl_pattern.search(line):
                player = match.group(2).strip()
                if player in active_buffs:
                    buffs = active_buffs[player]
                    if len(buffs) >= 3:  # Has all required buffs
                        ret_active = (current_time - buffs.get('retribution', current_time)).total_seconds() <= 59
                        tough_active = (current_time - buffs.get('toughen', current_time)).total_seconds() <= 9
                        bull_active = (current_time - buffs.get('bull_rush', current_time)).total_seconds() <= 5
                        
                        if ret_active and tough_active and bull_active:
                            success_count[player] = success_count.get(player, 0) + 1
                
                if player in active_buffs:
                    active_buffs[player] = {}
        
        return dict(sorted(success_count.items(), key=lambda x: x[1], reverse=True)[:10])

    def track_discord_combo(self):
        active_discord = {}
        success_count = {}
        
        for line in self.log_lines:
            timestamp = self.timestamp_pattern.search(line)
            if not timestamp:
                continue
            
            current_time = datetime.strptime(timestamp.group(1), '%Y-%m-%d %H:%M:%S')
            
            if match := self.discord_pattern.search(line):
                player = match.group(2).strip()
                target = match.group(3).strip()
                active_discord[target] = {'player': player, 'time': current_time}
            
            elif match := self.dissonance_pattern.search(line):
                target = match.group(2).strip()
                if target in active_discord:
                    discord_data = active_discord[target]
                    if (current_time - discord_data['time']).total_seconds() <= 3:
                        player = discord_data['player']
                        success_count[player] = success_count.get(player, 0) + 1
        
        return dict(sorted(success_count.items(), key=lambda x: x[1], reverse=True)[:10])

def plot_combo_results(combo_data, title, color='blue'):
    if not combo_data:
        return None
        
    # Ensure minimum height for consistency
    min_height = 4
    height = max(min_height, len(combo_data) * 0.4)
    
    fig, ax = plt.subplots(figsize=(12, height))
    players = list(combo_data.keys())
    counts = list(combo_data.values())
    
    ax.barh(range(len(players)), counts, color=color)
    ax.set_yticks(range(len(players)))
    ax.set_yticklabels(players)
    ax.invert_yaxis()
    ax.set_xlabel('Successful Combos')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    return fig
