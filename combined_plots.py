import matplotlib.pyplot as plt
from damage_log import DamageLog
from healing_log import HealingLog
from damage_taken_log import DmgRecLog
from healing_received import HealRecLog
from healing_pots import PotsLog
from combo_tracker import ComboTracker, plot_combo_results
from cast_tracker import CastTracker, plot_cast_results
from song_buff import plot_song_buff_data
from song_debuffs import plot_song_debuff_data
from mend import parse_heal_log, calculate_heal_stats, plot_total_heals, plot_min_max_avg_heals, plot_mend_casts

def generate_all_plots(logfile, includePvE, includeSelf):
    # Create a 4x3 grid of subplots
    fig = plt.figure(figsize=(30, 40))
    
    # General plots
    plots = [
        (1, "Damage", lambda: DamageLog(logfile, (0, 24), includePvE)[0], 'red'),
        (2, "Healing", lambda: HealingLog(logfile, (0, 24), includeSelf)[0], 'green'),
        (3, "Damage Taken", lambda: DmgRecLog(logfile, 25, includePvE)[0], 'blue'),
        (4, "Healing Received", lambda: HealRecLog(logfile, "", 25, includeSelf)[0], 'lightgreen'),
        (5, "Healing from Pots", lambda: PotsLog(logfile, 25)[0], 'purple')
    ]
    
    for i, (pos, title, data_func, color) in enumerate(plots, 1):
        ax = fig.add_subplot(4, 3, pos)
        try:
            data = data_func()
            if data:
                ax.grid(axis='x', zorder=0)
                ax.barh(y=list(data.keys()), 
                       width=list(data.values()), 
                       color=color, 
                       zorder=2)
                ax.set_xlabel('Amount')
                ax.set_title(title)
                ax.invert_yaxis()
                # Format x-axis labels
                xticks = ax.get_xticks()
                ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])
        except Exception as e:
            print(f"Error plotting {title}: {e}")
            ax.set_visible(False)

    # Add Combo tracking
    tracker = ComboTracker(logfile)
    
    # Discord Combo
    ax = fig.add_subplot(4, 3, 7)
    discord_data = tracker.track_discord_combo()
    if discord_data:
        ax.grid(axis='x', zorder=0)
        ax.barh(y=list(discord_data.keys()),
                width=list(discord_data.values()),
                color='purple')
        ax.set_xlabel('Count')
        ax.set_title('Discord Combo Success')
        ax.invert_yaxis()

    # Distress Combo
    ax = fig.add_subplot(4, 3, 8)
    distress_data = tracker.track_distress_combo()
    if distress_data:
        ax.grid(axis='x', zorder=0)
        ax.barh(y=list(distress_data.keys()),
                width=list(distress_data.values()),
                color='blue')
        ax.set_xlabel('Count')
        ax.set_title('Distress Combo Success')
        ax.invert_yaxis()

    # Mend Analysis
    heal_data, mend_counts = parse_heal_log(logfile)
    heal_stats = calculate_heal_stats(heal_data)
    
    ax = fig.add_subplot(4, 3, 9)
    plot_mend_casts(mend_counts, ax)

    ax = fig.add_subplot(4, 3, 10)
    plot_total_heals(heal_stats, ax)

    ax = fig.add_subplot(4, 3, 11)
    plot_min_max_avg_heals(heal_stats, mend_counts, heal_data, ax)

    # Song buff/debuff tracking
    ax = fig.add_subplot(4, 3, 12)
    try:
        plot_song_buff_data(logfile, ax)
        ax.set_title('Song Buff Duration')
    except Exception as e:
        print(f"Error plotting song buffs: {e}")
        ax.set_visible(False)

    plt.tight_layout(pad=3.0)
    return fig
