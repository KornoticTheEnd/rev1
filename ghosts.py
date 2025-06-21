import re
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
import pandas as pd
import numpy as np
from collections import defaultdict

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

class GhostAnalyzer:
    def __init__(self):
        self.patterns = {
            'spawn': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r is casting \|cff57d6aeSpawn Ghosts\|r\|r!",
            'debuff': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;Repulsing Darkness\|r attacked (.+?)\|r using \|cff57d6aePenetrating Dark Energy Effect\|r\|r",
            'clear': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r's \|cff57d6aePenetrating Dark Energy\|r\|r debuff cleared",
            'power': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;Black Dragon\|r gained the buff: \|cff57d6aeDevilish Contract\|r\|r"
        }
        self.reset()

    def reset(self):
        self.waves = []
        self.current_wave = None
        self.player_stats = defaultdict(lambda: {'total': 0, 'cleared': 0, 'failed': 0, 'avg_time': 0.0})
        self.boss_power = 0
        self.debuff_events = []

    def parse_timestamp(self, ts_str):
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")

    def analyze_log(self, log_data):
        self.reset()
        
        for line in log_data.splitlines():
            # Check spawn
            if spawn_match := re.search(self.patterns['spawn'], line):
                if self.current_wave:
                    self.waves.append(self.current_wave)
                timestamp = self.parse_timestamp(spawn_match.group(1))
                self.current_wave = {'start': timestamp, 'players': [], 'clears': [], 'times': []}
                
            # Check debuff
            elif debuff_match := re.search(self.patterns['debuff'], line):
                if not self.current_wave:
                    continue
                timestamp = self.parse_timestamp(debuff_match.group(1))
                player = debuff_match.group(2).strip()
                if player not in self.current_wave['players']:
                    self.current_wave['players'].append(player)
                    self.player_stats[player]['total'] += 1
                self.debuff_events.append({'player': player, 'start': timestamp, 'cleared': False})
                
            # Check clear
            elif clear_match := re.search(self.patterns['clear'], line):
                timestamp = self.parse_timestamp(clear_match.group(1))
                player = clear_match.group(2).strip()
                
                # Find matching debuff event
                for event in reversed(self.debuff_events):
                    if event['player'] == player and not event['cleared']:
                        event['cleared'] = True
                        event['clear_time'] = timestamp
                        clear_time = (timestamp - event['start']).total_seconds()
                        
                        if self.current_wave and player in self.current_wave['players']:
                            self.current_wave['clears'].append(player)
                            self.current_wave['times'].append(clear_time)
                            self.player_stats[player]['cleared'] += 1
                            self.player_stats[player]['avg_time'] = (
                                (self.player_stats[player]['avg_time'] * (self.player_stats[player]['cleared'] - 1) + 
                                clear_time) / self.player_stats[player]['cleared']
                            )
                        break
                        
            # Check power gain
            elif power_match := re.search(self.patterns['power'], line):
                self.boss_power += 10  # Each stack is 10%

        # Add final wave
        if self.current_wave:
            self.waves.append(self.current_wave)

        # Calculate final stats
        for player in self.player_stats:
            self.player_stats[player]['failed'] = (
                self.player_stats[player]['total'] - self.player_stats[player]['cleared']
            )

        return self.generate_report()

    def generate_report(self):
        if not self.waves:
            return {
                'success': False,
                'message': 'No ghost waves found in log'
            }

        # Convert player stats to DataFrame
        stats_df = pd.DataFrame([
            {
                'Player': player,
                'Total': stats['total'],
                'Cleared': stats['cleared'],
                'Failed': stats['failed'],
                'Clear Rate': f"{(stats['cleared'] / stats['total'] * 100):.1f}%",
                'Avg Clear Time': f"{stats['avg_time']:.1f}s" if stats['avg_time'] > 0 else "N/A"
            }
            for player, stats in self.player_stats.items()
        ])

        # Sort by clear rate descending
        stats_df = stats_df.sort_values(
            by=['Clear Rate', 'Avg Clear Time'],
            ascending=[False, True]
        )

        # Wave summary
        wave_summary = []
        for i, wave in enumerate(self.waves, 1):
            failed = set(wave['players']) - set(wave['clears'])
            avg_time = sum(wave['times']) / len(wave['times']) if wave['times'] else 0
            wave_summary.append({
                'Wave': i,
                'Players Hit': len(wave['players']),
                'Cleared': len(wave['clears']),
                'Failed': len(failed),
                'Avg Clear Time': f"{avg_time:.1f}s",
                'Failed Players': ', '.join(failed) if failed else 'None'
            })

        return {
            'success': True,
            'player_stats': stats_df,
            'wave_summary': pd.DataFrame(wave_summary),
            'total_waves': len(self.waves),
            'boss_power': self.boss_power,
            'debuff_events': self.debuff_events
        }

def main():
    st.title("Ghost Mechanic Analysis")
    
    uploaded_file = st.file_uploader("Upload log file", type=['txt'])
    
    if uploaded_file:
        log_data = uploaded_file.getvalue().decode('utf-8')
        analyzer = GhostAnalyzer()
        result = analyzer.analyze_log(log_data)
        
        if result['success']:
            # Summary metrics
            st.header("Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Waves", result['total_waves'])
            with col2:
                total_players = len(result['player_stats'])
                st.metric("Players Affected", total_players)
            with col3:
                st.metric("Boss Power", f"{result['boss_power']}%")
                if result['boss_power'] >= 150:
                    st.error("⚠️ Boss Enraged!")
            
            # Player Performance Table
            st.header("Player Performance")
            st.dataframe(result['player_stats'])
            
            # Wave Breakdown
            st.header("Wave Analysis")
            st.dataframe(result['wave_summary'])
            
            # Visualization
            st.header("Clear Time Distribution")
            fig, ax = plt.subplots(figsize=(10, 6))
            
            clear_times = [
                (event['clear_time'] - event['start']).total_seconds()
                for event in result['debuff_events']
                if event['cleared']
            ]
            
            if clear_times:
                ax.hist(clear_times, bins=20, color='skyblue', edgecolor='black')
                ax.axvline(x=37, color='red', linestyle='--', label='Fail threshold (37s)')
                ax.set_xlabel('Clear Time (seconds)')
                ax.set_ylabel('Count')
                ax.set_title('Distribution of Ghost Clear Times')
                ax.legend()
                
                st.pyplot(fig)
            
        else:
            st.error(result['message'])
            st.info("Make sure your log file contains ghost mechanics data")

if __name__ == "__main__":
    main()
    debuff_cleared_pattern = r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r's \|cff57d6aePenetrating Dark Energy\|r\|r debuff cleared."
    power_stack_pattern = r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;Black Dragon\|r gained the buff: \|cff57d6aeDevilish Contract\|r\|r."
    
    waves = []  # Track each wave of ghosts
    current_wave = None
    debuff_data = {}  # Initialize as empty dict
    boss_power_stacks = 0  # Track actual boss power stacks from log
    
    # Add counters for debugging
    spawn_count = 0
    debuff_count = 0
    clear_count = 0
    power_count = 0

        if apply_match := re.search(debuff_applied_pattern, line):
            debuff_count += 1
            timestamp_str, target = apply_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            player = target.strip()
            if player not in debuff_data:
                debuff_data[player] = []
            debuff_data[player].append({'applied': timestamp, 'cleared': None})
            if current_wave:
                current_wave['affected_players'].append(player)

        if clear_match := re.search(debuff_cleared_pattern, line):
            clear_count += 1
            timestamp_str, player = clear_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if player in debuff_data and debuff_data[player]:
                for debuff in reversed(debuff_data[player]):
                    if debuff['cleared'] is None:
                        debuff['cleared'] = timestamp
                        if current_wave and player in current_wave['affected_players']:
                            current_wave['cleared_players'].append(player)
                        break
    
    # Log debug information
    logging.info(f"Found {spawn_count} ghost spawns, {debuff_count} debuffs applied, {clear_count} debuffs cleared, {power_count} power stacks")

    # Add final wave if exists
    if current_wave:
        waves.append(current_wave)

    # Calculate failed players for each wave
    for wave in waves:
        wave['failed_players'] = [p for p in wave['affected_players'] if p not in wave['cleared_players']]

    return debuff_data, waves, boss_power_stacks * 10  # Each stack is 10% power

# Function to plot debuff data
def plot_debuff_data(debuff_data, waves=None, boss_power=0):
    if not isinstance(debuff_data, dict) or not debuff_data:
        st.warning("No ghost debuff data found in the log file.")
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get list of players hit by debuffs
    players_hit = sorted(debuff_data.keys())  # Sort players alphabetically
    plot_data = []

    # Process data for plotting
    for player in players_hit:
        for debuff in debuff_data[player]:
            applied = debuff['applied']
            cleared = debuff['cleared']
            if cleared:
                duration = (cleared - applied).total_seconds()
                color = '#32CD32' if duration <= 37 else '#FF4C4C'  # Green if cleared in time, red if not
            else:
                duration = None
                color = '#FF4C4C'  # Red for uncleared debuffs
            plot_data.append((player, applied, cleared, duration, color))

    # Plot data points
    for player in players_hit:
        y_value = players_hit.index(player)
        for debuff in debuff_data[player]:
            if debuff['cleared']:
                duration = (debuff['cleared'] - debuff['applied']).total_seconds()
                color = '#32CD32' if duration <= 37 else '#FF4C4C'
                ax.plot([debuff['applied'], debuff['cleared']], [y_value, y_value], 
                       color=color, marker='o', linewidth=2)
                # Add duration text
                ax.text(debuff['cleared'], y_value, f' {duration:.1f}s', 
                       va='center', ha='left', fontsize=8)
            else:
                ax.scatter(debuff['applied'], y_value, color='#FF4C4C', marker='x')

    # Customize plot
    ax.set_yticks(range(len(players_hit)))
    ax.set_yticklabels(players_hit)
    ax.set_xlabel('Time')
    ax.set_title('Ghost Debuff Timeline')
    ax.grid(True, alpha=0.3)

    # Format x-axis with timestamps
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)    # Add wave analysis if available
    if waves:
        total_affected = sum(len(w['affected_players']) for w in waves)
        total_cleared = sum(len(w['cleared_players']) for w in waves)
        total_failed = sum(len(w['failed_players']) for w in waves)
        
        st.write("### Wave Analysis")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Waves", len(waves))
        col2.metric("Players Affected", total_affected)
        col3.metric("Successfully Cleared", total_cleared)
        col4.metric("Failed to Clear", total_failed)
        
        if boss_power >= 150:  # 15 stacks
            st.error(f"⚠️ Boss Enraged! Power: {boss_power}%")
        elif boss_power > 0:
            st.warning(f"🔥 Boss Power: {boss_power}%")
            
    plt.tight_layout()
    return fig

# Main Streamlit app
def main():
    st.title("Ghost Mechanic Analysis")
    
    uploaded_file = st.file_uploader("Upload log file", type=['txt'])
    
    if uploaded_file:
        log_data = uploaded_file.getvalue().decode('utf-8')
        analyzer = GhostAnalyzer()
        result = analyzer.analyze_log(log_data)
        
        if result['success']:
            # Summary metrics
            st.header("Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Waves", result['total_waves'])
            with col2:
                total_players = len(result['player_stats'])
                st.metric("Players Affected", total_players)
            with col3:
                st.metric("Boss Power", f"{result['boss_power']}%")
                if result['boss_power'] >= 150:
                    st.error("⚠️ Boss Enraged!")
            
            # Player Performance Table
            st.header("Player Performance")
            st.dataframe(result['player_stats'])
            
            # Wave Breakdown
            st.header("Wave Analysis")
            st.dataframe(result['wave_summary'])
            
            # Visualization
            st.header("Clear Time Distribution")
            fig, ax = plt.subplots(figsize=(10, 6))
            
            clear_times = [
                (event['clear_time'] - event['start']).total_seconds()
                for event in result['debuff_events']
                if event['cleared']
            ]
            
            if clear_times:
                ax.hist(clear_times, bins=20, color='skyblue', edgecolor='black')
                ax.axvline(x=37, color='red', linestyle='--', label='Fail threshold (37s)')
                ax.set_xlabel('Clear Time (seconds)')
                ax.set_ylabel('Count')
                ax.set_title('Distribution of Ghost Clear Times')
                ax.legend()
                st.pyplot(fig)  # Pass the figure explicitly
        else:
            st.error(result['message'])
            st.info("Make sure your log file contains ghost mechanics data")
            
if __name__ == "__main__":
    main()
