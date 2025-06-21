import re
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
import pandas as pd

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Function to parse log data
def parse_log(log_data, players):
    # Update patterns to include boss cast and power stacks
    ghost_spawn_pattern = r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r is casting \|cff57d6aeSpawn Ghosts\|r\|r!"
    debuff_applied_pattern = r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r was struck by a \|cff57d6aePenetrating Dark Energy\|r\|r debuff!"
    debuff_cleared_pattern = r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r's \|cff57d6aePenetrating Dark Energy\|r\|r debuff cleared."
    power_stack_pattern = r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;Black Dragon\|r gained the buff: \|cff57d6aeDevilish Contract\|r\|r."
    
    waves = []  # Track each wave of ghosts
    current_wave = None
    debuff_data = {}  # Initialize as empty dict
    boss_power_stacks = 0  # Track actual boss power stacks from log

    if not log_data:  # Handle empty log data
        return {}, [], 0

    for line in log_data.splitlines():
        if power_match := re.search(power_stack_pattern, line):
            boss_power_stacks += 1  # Increment when boss gains a power stack
            if current_wave:
                current_wave['power_gained'] = True
        
        if spawn_match := re.search(ghost_spawn_pattern, line):
            # New wave starting
            if current_wave:
                waves.append(current_wave)
            timestamp = datetime.strptime(spawn_match.group(1), "%Y-%m-%d %H:%M:%S")
            current_wave = {
                'spawn_time': timestamp,
                'affected_players': [],
                'failed_players': [],
                'cleared_players': [],
                'power_gained': False
            }

        if apply_match := re.search(debuff_applied_pattern, line):
            timestamp_str, player = apply_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if player not in debuff_data:
                debuff_data[player] = []
            debuff_data[player].append({'applied': timestamp, 'cleared': None})
            if current_wave:
                current_wave['affected_players'].append(player)

        if clear_match := re.search(debuff_cleared_pattern, line):
            timestamp_str, player = clear_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            if player in debuff_data and debuff_data[player]:
                # Find the most recent uncleaned debuff
                for debuff in reversed(debuff_data[player]):
                    if debuff['cleared'] is None:
                        debuff['cleared'] = timestamp
                        if current_wave and player in current_wave['affected_players']:
                            current_wave['cleared_players'].append(player)
                        break

    # Add final wave if exists
    if current_wave:
        waves.append(current_wave)

    # Calculate failed players for each wave
    for wave in waves:
        wave['failed_players'] = [p for p in wave['affected_players'] 
                                if p not in wave['cleared_players']]

    return debuff_data, waves, boss_power_stacks * 10  # Each stack is 10% power

# Function to plot debuff data
def plot_debuff_data(debuff_data, waves=None, boss_power=0):
    if not debuff_data:
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
    plt.xticks(rotation=45)

    # Add wave analysis if available
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

# Example usage
log_file_path = 'path_to_log_file.log'  # Replace with your actual log file path
try:
    with open(log_file_path, 'r', encoding='utf-8') as file:
        log_data = file.read()
    debuff_data, waves, boss_power = parse_log(log_data, [])
    plot_debuff_data(debuff_data, waves, boss_power)
except FileNotFoundError:
    logging.error(f"Log file '{log_file_path}' not found.")
