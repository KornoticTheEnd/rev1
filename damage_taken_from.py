import re
import matplotlib.pyplot as plt

def DmgTakenFromLog(logfile, player, includePvE):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    dmg_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r attacked (.+?)\|r using \|cff57d6ae(.*?)\|r\|r and caused \|cffc13d36-(\d+)\|r\|r \|cffc13d36Health\|r\|r \(\|cffc13d36(.+?)\|r\|r\)!')
    dmg_events = []
    
    excluded_entities = ['Kraken', 'Black Dragon', 'Flame Field', 'Jola the Cursed', 'Glenn', 'Meina', 'Crewman', 'Charybdis', 'Anthalon', 'Bloodspire']
    excluded_abilities = ['Corrosive Acid', "Black Dragon's Breath", "Red Dragon's Breath", "Clinging Flame", 
                         "Roar Aftershock", "Clinging Flame Explosion", "Boulder Rain", "Guided Missiles", 
                         "Earthquake", "Shoot Acid"]

    for line in lines:
        if dmg_pattern.match(line):
            result = dmg_pattern.findall(line)
            attacker, receiver, ability, damage = result[0][1], result[0][2], result[0][3], int(result[0][4])
            
            if receiver == player:  # Only include damage to specified player
                if includePvE == 0:
                    if attacker.count(' ') == 0 and attacker not in excluded_entities and ability not in excluded_abilities:
                        dmg_events.append((attacker, ability, damage))
                elif includePvE == 1:
                    if attacker not in excluded_entities:
                        dmg_events.append((attacker, ability, damage))

    '''Collect & Calc events'''
    dmg_log = {}  # {attacker: total_damage}
    ability_log = {}  # {attacker: {ability: damage}}

    for attacker, ability, damage in dmg_events:
        # Track total damage per attacker
        if attacker not in dmg_log:
            dmg_log[attacker] = damage
            ability_log[attacker] = {}
        else:
            dmg_log[attacker] += damage
            
        # Track damage per ability for each attacker
        if ability not in ability_log[attacker]:
            ability_log[attacker][ability] = damage
        else:
            ability_log[attacker][ability] += damage

    # Filter and sort by total damage
    tolerance = sum(dmg_log.values()) * 0.01  # 1% tolerance
    dmg_log = {k: v for k, v in dmg_log.items() if v >= tolerance}
    dmg_log = dict(sorted(dmg_log.items(), key=lambda x: x[1], reverse=True)[:10])  # Take only top 10

    '''Plot Details'''
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#c1c1c1')  # Reduced height since fewer entries
    plt.grid(axis='x', zorder=0)

    bars = ax.barh(y=list(dmg_log.keys()), width=list(dmg_log.values()), color='red', zorder=2)
    ax.set_xlabel('Damage Done', fontsize='x-large')
    ax.set_ylabel('Attacker', fontsize='x-large')
    ax.invert_yaxis()  # Show highest damage at top
    ax.set_title(f'Damage Taken by {player} - {logfile} (1% Tolerance Applied)')

    # Add ability breakdown annotations
    for i, (attacker, total_damage) in enumerate(dmg_log.items()):
        abilities = ability_log[attacker]
        top_abilities = sorted(abilities.items(), key=lambda x: x[1], reverse=True)[:3]
        ability_text = '\n'.join([f"{ability}: {damage:,}" for ability, damage in top_abilities])
        
        ax.text(total_damage * 1.02, i, ability_text, 
                va='center', fontsize=9,
                bbox=dict(facecolor='white', edgecolor='black', alpha=0.7))

    # Format x-axis labels with commas
    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels([f'{int(x):,}' for x in ax.get_xticks()])

    plt.tight_layout()

    return dmg_log, fig
