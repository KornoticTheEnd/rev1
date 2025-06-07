import matplotlib.pyplot as plt
import gc
import logging
from damage_log import DamageLog
from healing_log import HealingLog
from damage_taken_log import DmgRecLog
from healing_received import HealRecLog
from healing_pots import PotsLog

logger = logging.getLogger(__name__)

def plot_combined_data(ax, data, title, color):
    if not data:
        ax.set_visible(False)
        return

    sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True))
    ax.grid(axis='x', zorder=0)
    ax.barh(y=list(sorted_data.keys()),
            width=list(sorted_data.values()),
            color=color)
    ax.set_xlabel(title)
    ax.set_ylabel('Entity')
    ax.set_title(title)
    xticks = ax.get_xticks()
    ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])
    ax.invert_yaxis()

def generate_combined_analysis(logfile, includePvE, includeSelf):
    """Generate combined analysis plots with proper memory management"""
    try:
        # Create a 3x2 grid for up to 5 plots, leave last axis empty
        fig, axes = plt.subplots(3, 2, figsize=(20, 24))
        axes = axes.flatten()

        data_collections = [
            (lambda: DamageLog(logfile, (0, 24), includePvE)[0], 'Damage', 'red'),
            (lambda: HealingLog(logfile, (0, 24), includeSelf)[0], 'Healing', 'green'),
            (lambda: DmgRecLog(logfile, 25, includePvE)[0], 'Damage Taken', 'blue'),
            (lambda: HealRecLog(logfile, "", 25, includeSelf)[0], 'Healing Received', 'lightgreen'),
            (lambda: PotsLog(logfile, 25)[0], 'Healing from Pots', 'purple')
        ]

        for idx, (get_data, title, color) in enumerate(data_collections):
            try:
                logger.info(f"Processing {title} data...")
                data = get_data()
                plot_combined_data(axes[idx], data, title, color)
            except Exception as e:
                logger.error(f"Error processing {title}: {str(e)}")
                axes[idx].set_visible(False)
            finally:
                gc.collect()

        # Hide the last unused subplot
        if len(axes) > len(data_collections):
            axes[-1].set_visible(False)

        plt.tight_layout(pad=3.0)
        return fig

    except Exception as e:
        logger.error(f"Error in combined analysis: {str(e)}")
        raise
    finally:
        gc.collect()
        # Do not close the figure here, let Streamlit render it
        # plt.close('all')
