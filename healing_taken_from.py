import re
import matplotlib.pyplot as plt

def HealTakenFromLog(logfile, player, includeSelf):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    heal_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r targeted (.+?)\|r using \|cff57d6ae(.*?)\|r\|r to restore \|cff9be85a(\d+)\|r\|r health\.')
    heal_events = []
    
    for line in lines:
        if heal_pattern.match(line):
            result = heal_pattern.findall(line)
            healer, target, ability, heal = result[0][1], result[0][2], result[0][3], int(result[0][4])
            
            if target == player:  # Only include healing to specified player
                if includeSelf == 0:
                    if healer != target:  # Exclude self-healing
                        heal_events.append((healer, ability, heal))
                elif includeSelf == 1:
                    heal_events.append((healer, ability, heal))

    '''Collect & Calc events'''
    heal_log = {}  # {healer: total_healing}
    ability_log = {}  # {healer: {ability: healing}}

    for healer, ability, heal in heal_events:
        # Track total healing per healer
        if healer not in heal_log:
            heal_log[healer] = heal
            ability_log[healer] = {}
        else:
            heal_log[healer] += heal
            
        # Track healing per ability for each healer
        if ability not in ability_log[healer]:
            ability_log[healer][ability] = heal
        else:
            ability_log[healer][ability] += heal

    # Filter and sort by total healing
    tolerance = sum(heal_log.values()) * 0.01  # 1% tolerance
    heal_log = {k: v for k, v in heal_log.items() if v >= tolerance}
    heal_log = dict(sorted(heal_log.items(), key=lambda x: x[1], reverse=True))

    '''Plot Details'''
    fig, ax = plt.subplots(figsize=(12, 8), facecolor='#c1c1c1')
    plt.grid(axis='x', zorder=0)

    bars = ax.barh(y=list(heal_log.keys()), width=list(heal_log.values()), color='green', zorder=2)
    ax.set_xlabel('Healing Done', fontsize='x-large')
    ax.set_ylabel('Healer', fontsize='x-large')
    ax.invert_yaxis()  # Show highest healing at top
    ax.set_title(f'Healing Received by {player} - {logfile} (1% Tolerance Applied)')

    # Add ability breakdown annotations
    for i, (healer, total_healing) in enumerate(heal_log.items()):
        abilities = ability_log[healer]
        top_abilities = sorted(abilities.items(), key=lambda x: x[1], reverse=True)[:3]
        ability_text = '\n'.join([f"{ability}: {healing:,}" for ability, healing in top_abilities])
        
        ax.text(total_healing * 1.02, i, ability_text, 
                va='center', fontsize=9,
                bbox=dict(facecolor='white', edgecolor='black', alpha=0.7))

    # Format x-axis labels with commas
    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels([f'{int(x):,}' for x in ax.get_xticks()])

    plt.tight_layout()

    return heal_log, fig
