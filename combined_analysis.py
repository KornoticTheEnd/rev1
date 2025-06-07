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
        return
        
    sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True))
    ax.grid(axis='x', zorder=0)
    ax.barh(y=list(sorted_data.keys()), 
            width=list(sorted_data.values()), 
            color=color)
    ax.set_xlabel(title)
    ax.set_ylabel('Entity')
    ax.set_title(title)
    
    # Format numbers with commas
    xticks = ax.get_xticks()
    ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])
    
    # Invert y-axis to show highest values at top
    ax.invert_yaxis()

def generate_combined_analysis(logfile, includePvE, includeSelf):
    """Generate combined analysis plots with proper memory management"""
    try:
        # Create figure with specific size
        fig = plt.figure(figsize=(20, 24))
        
        # Define data collections with consistent filtering
        data_collections = [
            (lambda: DamageLog(logfile, (0, 24), includePvE)[0], 'Damage', 'red', 321),
            (lambda: HealingLog(logfile, (0, 24), includeSelf)[0], 'Healing', 'green', 322),
            (lambda: DmgRecLog(logfile, 25, includePvE)[0], 'Damage Taken', 'blue', 323),
            (lambda: HealRecLog(logfile, "", 25, includeSelf)[0], 'Healing Received', 'lightgreen', 324),
            (lambda: PotsLog(logfile, 25)[0], 'Healing from Pots', 'purple', 325)
        ]

        # Process each dataset
        for get_data, title, color, position in data_collections:
            try:
                logger.info(f"Processing {title} data...")
                data = get_data()
                
                if data:
                    ax = plt.subplot(position)
                    plot_combined_data(ax, data, title, color)
                    
            except Exception as e:
                logger.error(f"Error processing {title}: {str(e)}")
                continue
            finally:
                gc.collect()

        plt.tight_layout(pad=3.0)
        return fig
        
    except Exception as e:
        logger.error(f"Error in combined analysis: {str(e)}")
        raise
    finally:
        gc.collect()
        plt.close('all')
