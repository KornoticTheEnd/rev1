import re
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Function to parse log data
def parse_log(log_data, players):
    debuff_applied_pattern = r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.*?)\|r was struck by a \|cff57d6aePenetrating Dark Energy\|r\|r debuff!"
    debuff_cleared_pattern = r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.*?)\|r's \|cff57d6aePenetrating Dark Energy\|r\|r debuff cleared."
    
    debuff_data = {}
    
    for line in log_data.splitlines():
        apply_match = re.search(debuff_applied_pattern, line)
        clear_match = re.search(debuff_cleared_pattern, line)

        if apply_match:
            timestamp_str, player = apply_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            player = player.strip()
            logging.info(f"Debuff applied: {timestamp} to {player}")

            if player not in debuff_data:
                debuff_data[player] = []
            debuff_data[player].append({'applied': timestamp, 'cleared': None})

        if clear_match:
            timestamp_str, player = clear_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            player = player.strip()
            logging.info(f"Debuff cleared: {timestamp} for {player}")

            if player in debuff_data:
                for entry in debuff_data[player]:
                    if entry['cleared'] is None:
                        entry['cleared'] = timestamp
                        break

    return debuff_data

# Function to plot debuff data
def plot_debuff_data(debuff_data):
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

    for player, applied, cleared in plot_data:
        y_value = players_hit.index(player)  # Use sorted player names

        if cleared:
            color = 'lightgreen' if player in cleared_under_37_seconds else 'salmon'
            ax.plot([applied, cleared], [y_value, y_value], color=color, marker='o', markersize=5)
        else:
            ax.scatter(applied, y_value, color='red', marker='x', s=70)  # Smaller marker to fit

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

    st.pyplot(fig)

# Example usage
log_file_path = 'path_to_log_file.log'  # Replace with your actual log file path
try:
    with open(log_file_path, 'r', encoding='utf-8') as file:
        log_data = file.read()
    debuff_data = parse_log(log_data, [])
    plot_debuff_data(debuff_data)
except FileNotFoundError:
    logging.error(f"Log file '{log_file_path}' not found.")
