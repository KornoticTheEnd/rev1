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
    debuff_data = {}
    boss_power_stacks = 0  # Track actual boss power stacks from log
    
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
                'cleared_players': []
            }

        if apply_match := re.search(debuff_applied_pattern, line):
            timestamp_str, player = apply_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            player = player.strip()

            if current_wave and (timestamp - current_wave['spawn_time']).total_seconds() <= 5:
                # Add to current wave if within 5s of spawn
                current_wave['affected_players'].append(player)

            if player not in debuff_data:
                debuff_data[player] = []
            debuff_data[player].append({'applied': timestamp, 'cleared': None, 'wave': len(waves)})

        if clear_match := re.search(debuff_cleared_pattern, line):
            timestamp_str, player = clear_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            player = player.strip()

            # Update debuff data
            if player in debuff_data:
                for entry in debuff_data[player]:
                    if entry['cleared'] is None:
                        entry['cleared'] = timestamp
                        if current_wave and player in current_wave['affected_players']:
                            current_wave['cleared_players'].append(player)
                        break

    # Add final wave if exists
    if current_wave:
        waves.append(current_wave)

    # Update wave stats to include actual power gains
    for wave in waves:
        wave['power_gained'] = wave.get('power_gained', False)

    return debuff_data, waves, boss_power_stacks * 10  # Each stack is 10% power

# Function to plot debuff data
def plot_debuff_data(debuff_data, waves=None, boss_power=0):
    cleared_under_37_seconds = set()
    failed_to_clear = set()
    players_hit = sorted(debuff_data.keys())  # Sort players alphabetically

    plot_data = []

    for player, events in debuff_data.items():
        for event in events:
            applied_time = event['applied']
            cleared_time = event['cleared']

            if cleared_time:
                duration = (cleared_time - applied_time).total_seconds()
                logging.info(f"{player} cleared in {duration:.1f} seconds")
                if duration <= 37:
                    cleared_under_37_seconds.add(player)
                else:
                    failed_to_clear.add(player)
            else:
                logging.info(f"{player} did not clear the debuff")
                failed_to_clear.add(player)

            plot_data.append((player, applied_time, cleared_time))

    # Debugging summary
    logging.info(f"\n===== Summary =====")
    logging.info(f"📌 Players hit by debuff: {len(players_hit)}")
    logging.info(f"✅ Cleared under 37s: {len(cleared_under_37_seconds)}")
    logging.info(f"❌ Failed to clear: {len(failed_to_clear)}\n")

    # Moderate dynamic figure height
    fig_height = min(12, max(6, len(players_hit) * 0.3))  # Controlled growth
    fig, ax = plt.subplots(figsize=(12, fig_height))

    # Alternating background shading for clarity
    for i in range(len(players_hit)):
        if i % 2 == 0:
            ax.axhspan(i - 0.5, i + 0.5, facecolor='#f0f0f0', alpha=0.5)  # Light gray bands

    # Update status indicators
    success_emoji = "✅"
    fail_emoji = "❌"
    for player in cleared_under_37_seconds:
        logging.info(f"{success_emoji} {player} cleared successfully")
    for player in failed_to_clear:
        logging.info(f"{fail_emoji} {player} failed to clear")

    # Add status column to plot
    for player, applied, cleared in plot_data:
        y_value = players_hit.index(player)
        status = success_emoji if player in cleared_under_37_seconds else fail_emoji
        ax.text(-0.5, y_value, status, transform=ax.get_yaxis_transform(), 
                ha='right', va='center')

    # Make the plot colors more distinct
    for player, applied, cleared in plot_data:
        y_value = players_hit.index(player)
        if cleared:
            color = '#32CD32' if player in cleared_under_37_seconds else '#FF4C4C'  # Brighter green/red
            ax.plot([applied, cleared], [y_value, y_value], color=color, marker='o', 
                   markersize=5, linewidth=2, alpha=0.8)
        else:
            ax.scatter(applied, y_value, color='#FF4C4C', marker='x', s=100)

    # Add time duration annotations
    for player, applied, cleared in plot_data:
        if cleared:
            y_value = players_hit.index(player)
            duration = (cleared - applied).total_seconds()
            ax.text(cleared, y_value, f' {duration:.1f}s', 
                   va='center', ha='left', fontsize=8)

    # Formatting the X-axis to show readable timestamps
    ax.set_xlabel("Time")
    ax.set_ylabel("Players")
    ax.set_title("Debuff Duration for Penetrating Dark Energy")
    ax.set_yticks(range(len(players_hit)))
    ax.set_yticklabels(players_hit)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))

    # Add legend (moved to bottom left)
    ax.scatter([], [], color='lightgreen', label="Cleared <37s", s=70)
    ax.scatter([], [], color='salmon', label="Cleared >37s", s=70)
    ax.scatter([], [], color='red', marker='x', label="Never Cleared", s=70)
    ax.legend(loc="lower left", fontsize=9, frameon=True)

    # Add wave analysis
    if waves:
        wave_data = pd.DataFrame([{
            'Wave': i+1,
            'Affected': len(w['affected_players']),
            'Cleared': len(w['cleared_players']),
            'Failed': len(w['failed_players']),
            'Clear Rate': f"{(len(w['cleared_players'])/len(w['affected_players'])*100):.1f}%"
        } for i, w in enumerate(waves)])

        # Add wave summary table
        st.subheader("Wave Analysis")
        st.dataframe(wave_data)

        # Show boss power warning with stack count
        power_stacks = boss_power // 10
        if power_stacks >= 15:
            st.error(f"⚠️ Boss Enraged! Power Stacks: {power_stacks} ({boss_power}% increased power)")
        elif power_stacks > 0:
            st.warning(f"🔥 Boss Power Stacks: {power_stacks} ({boss_power}% increased power)")

        # Calculate and show overall stats
        total_affected = sum(len(w['affected_players']) for w in waves)
        total_cleared = sum(len(w['cleared_players']) for w in waves)
        overall_clear_rate = (total_cleared / total_affected * 100) if total_affected > 0 else 0

        st.subheader("Overall Performance")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Players Affected", total_affected)
        col2.metric("Successfully Cleared", total_cleared)
        col3.metric("Overall Clear Rate", f"{overall_clear_rate:.1f}%")

    st.pyplot(fig)

# Example usage
log_file_path = 'path_to_log_file.log'  # Replace with your actual log file path
try:
    with open(log_file_path, 'r', encoding='utf-8') as file:
        log_data = file.read()
    debuff_data, waves, boss_power = parse_log(log_data, [])
    plot_debuff_data(debuff_data, waves, boss_power)
except FileNotFoundError:
    logging.error(f"Log file '{log_file_path}' not found.")
