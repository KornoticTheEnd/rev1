import re
import os
from collections import defaultdict
import matplotlib.pyplot as plt

# Updated regex pattern for the new log format
heal_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.*?)\|r targeted (.*?)\|r using \|cff57d6aeMend\|r\|r to restore \|cff9be85a(\d+)\|r\|r health\.')

# Function to find the log file in the current directory
def find_log_file(file_name):
    current_directory = os.getcwd()
    for file in os.listdir(current_directory):
        if file == file_name:
            return os.path.join(current_directory, file)
    raise FileNotFoundError(f"Log file '{file_name}' not found in directory {current_directory}")

# Function to parse the log file and extract healing data
def parse_heal_log(file_path):
    heal_data = defaultdict(list)  # Store heals for each healer
    mend_counts = defaultdict(int)  # Track how many times each player cast "Mend"

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = heal_pattern.match(line)
            if match:
                timestamp, healer, target, heal_amount = match.groups()
                healer = healer.strip()
                heal_data[healer].append(int(heal_amount))
                mend_counts[healer] += 1  # Increment cast count for the healer
    
    return heal_data, mend_counts

# Function to calculate heal stats
def calculate_heal_stats(heal_data):
    heal_stats = {}
    for healer, heals in heal_data.items():
        total_heal_amount = sum(heals)
        num_casts = len(heals)
        min_heal = min(heals)
        max_heal = max(heals)
        avg_heal = total_heal_amount / num_casts if num_casts > 0 else 0
        heal_stats[healer] = {
            'total_heal_amount': total_heal_amount,
            'num_casts': num_casts,
            'min_heal': min_heal,
            'max_heal': max_heal,
            'avg_heal': avg_heal,
            'heals': heals  # Store individual heals for each healer
        }
    return heal_stats

# Function to plot total healed amount for each healer (ranked)
def plot_total_heals(heal_stats, axes):
    sorted_healers = sorted(heal_stats.items(), key=lambda x: x[1]['total_heal_amount'], reverse=True)
    healers = [healer for healer, _ in sorted_healers]
    total_heals = [stats['total_heal_amount'] for _, stats in sorted_healers]

    bars = axes.barh(healers, total_heals, color='lightgreen')
    axes.set_xlabel('Total Healing Amount (HP)')
    axes.set_ylabel('Healer')
    axes.set_title('Total Healing by Mend')
    axes.invert_yaxis()
    
    if total_heals:
        axes.set_xlim(0, max(total_heals) * 1.3)  # Ensure enough space on the axis, 10% margin
    
    for bar in bars:
        width = bar.get_width()
        axes.text(width, bar.get_y() + bar.get_height() / 2, f'{width:.0f}', va='center')

# Function to plot average healing, min and max healing relative to average for each healer
def plot_min_max_avg_heals(heal_stats, mend_counts, heal_data, axes, tolerance_ratio=0.6, outlier_threshold=2):
    # Calculate tolerance based on the top Mend cast counts
    top_mend_casts = sorted(mend_counts.values(), reverse=True)
    if top_mend_casts:
        mean_tolerance = sum(top_mend_casts[:3]) / len(top_mend_casts[:3])
        tolerance = mean_tolerance * tolerance_ratio
    else:
        tolerance = 0

    healer_stats = []
    high_heals = []
    
    # Calculate the highest average healing tick of other healers for capping
    other_max_heals = sorted([stats['max_heal'] for healer, stats in heal_stats.items() if mend_counts.get(healer, 0) >= tolerance], reverse=True)
    if len(other_max_heals) > 1:
        threshold = other_max_heals[1] * 1.25
    else:
        threshold = max([stats['max_heal'] for stats in heal_stats.values()])  # Fallback to overall max if not enough data

    for healer, stats in heal_stats.items():
        if mend_counts.get(healer, 0) < tolerance:
            continue

        avg_heal = stats['avg_heal']
        max_heal = stats['max_heal']

        # Apply error tolerance: cap max_heal if it exceeds the threshold
        if max_heal > threshold:
            max_heal = threshold  # Cap the max_heal

        min_heal = stats['min_heal'] / avg_heal if avg_heal > 0 else 0
        max_heal_relative = max_heal / avg_heal if avg_heal > 0 else 0
        
        healer_stats.append((healer, avg_heal, max_heal_relative))
        high_heals.append(max_heal)

    # Calculate average values for high heals and average healing tick
    avg_high_heal = sum(high_heals) / len(high_heals) if high_heals else 0
    avg_heal_tick = sum(avg_heal for _, avg_heal, _ in healer_stats) / len(healer_stats) if healer_stats else 0

    # Sort by average healing in descending order
    healer_stats.sort(key=lambda x: x[1], reverse=True)

    # Extract the sorted healer names, avg, and max values
    healers = [healer for healer, _, _ in healer_stats]
    avg_heals = [avg for _, avg, _ in healer_stats]
    max_relative = [max_val for _, _, max_val in healer_stats]

    # Plot the average heal amount as bars
    bars = axes.barh(healers, avg_heals, color='lightgreen', label='Average Healing Tick')

    # Plot high healing values as scatter points and add annotations
    for i, (avg, max_val) in enumerate(zip(avg_heals, max_relative)):
        max_heal_amount = avg * max_val
        
        axes.scatter(max_heal_amount, i, color='blue', label='Max Tick' if i == 0 else "")

        # Annotate the values on the plot
        axes.text(max_heal_amount, i, f'{max_heal_amount:.0f}', va='center', ha='right', color='black', fontsize=10)
        axes.text(avg, i, f'{avg:.0f}', va='center', ha='right', color='black', fontsize=10)

    # Plot the average high healing line
    axes.axvline(x=avg_high_heal, color='blue', linestyle='--', label=f'Avg High Healing: {avg_high_heal:.0f}')
    # Plot the average healing tick line
    axes.axvline(x=avg_heal_tick, color='lightgreen', linestyle='--', label=f'Avg Healing Tick: {avg_heal_tick:.0f}')
    # Plot the tolerance line
    axes.axvline(x=tolerance, color='red', linestyle='--', label=f'Total Ticks Tolerance: {tolerance:.0f}')

    axes.set_xlabel('Healing Amount (HP)')
    axes.set_ylabel('Healer')
    axes.set_title('Life Mend Statistics per Healer: Avg and Max Relative to Avg')
    axes.invert_yaxis()

    # Update legend to reflect only relevant entries
    axes.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

# Function to plot the number of times each player cast Mend (ranked)
def plot_mend_casts(mend_counts, axes, tolerance_ratio=0.6):
    sorted_mend_counts = sorted(mend_counts.items(), key=lambda x: x[1], reverse=True)
    players = [player for player, _ in sorted_mend_counts]
    mend_casts = [count for _, count in sorted_mend_counts]

    # Calculate tolerance based on the top Mend cast counts
    top_mend_casts = sorted(mend_counts.values(), reverse=True)
    if top_mend_casts:
        mean_tolerance = sum(top_mend_casts[:3]) / len(top_mend_casts[:3])
        tolerance = mean_tolerance * tolerance_ratio
    else:
        tolerance = 0

    bars = axes.barh(players, mend_casts, color='orange')

    axes.axvline(x=tolerance, color='red', linestyle='--', label=f'Total Ticks Tolerance: {tolerance:.0f}')
    axes.set_xlabel('Number of Casts')
    axes.set_ylabel('Healer')
    axes.set_title('Number of Mend Casts by Healer')
    axes.invert_yaxis()

    for bar in bars:
        width = bar.get_width()
        axes.text(width, bar.get_y() + bar.get_height() / 2, f'{width:.0f}', va='center')
