import matplotlib.pyplot as plt
from damage_by_ability import DmgAbiLog
from damage_taken_target import DmgTakenByPlayer
from healing_by_target import HealAbiLog
from healing_taken_target import HealReceivedByPlayer
from damage_taken_from import DmgTakenFromLog
from healing_taken_from import HealTakenFromLog

def generate_player_plots(logfile, player_name, includePvE, includeSelf):
    """Generate all player-specific plots in one figure"""
    
    # Create a 3x2 grid of subplots
    fig = plt.figure(figsize=(30, 40))
    
    # Define plots with their parameters
    plots = [
        (1, "Damage By Ability", lambda: DmgAbiLog(logfile, player_name, includePvE)[0], 'red'),
        (2, "Healing By Target", lambda: HealAbiLog(logfile, includeSelf, player_name)[0], 'green'),
        (3, "Damage Taken By Target", lambda: DmgTakenByPlayer(logfile, player_name, includePvE)[0], 'blue'),
        (4, "Healing Taken By Target", lambda: HealReceivedByPlayer(logfile, player_name, includePvE)[0], 'lightgreen'),
        (5, "Damage Taken From", lambda: DmgTakenFromLog(logfile, player_name, includePvE)[0], 'orange'),
        (6, "Healing Taken From", lambda: HealTakenFromLog(logfile, player_name, includeSelf)[0], 'purple')
    ]
    
    # Generate each plot
    for i, (pos, title, data_func, color) in enumerate(plots, 1):
        ax = fig.add_subplot(3, 2, pos)
        try:
            data = data_func()
            if data:
                ax.grid(axis='x', zorder=0)
                ax.barh(y=list(data.keys()), 
                       width=list(data.values()), 
                       color=color, 
                       zorder=2)
                ax.set_xlabel('Amount')
                ax.set_title(f"{title} - {player_name}")
                ax.invert_yaxis()
                # Format x-axis labels
                xticks = ax.get_xticks()
                ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])
        except Exception as e:
            print(f"Error plotting {title}: {e}")
            ax.set_visible(False)

    plt.tight_layout(pad=3.0)
    return fig
