import re
import matplotlib.pyplot as plt

def DmgTakenByPlayer(logfile, player, includePvE):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    dmg_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r attacked (.+?)\|r using \|cff57d6ae(.*?)\|r\|r and caused \|cffc13d36-(\d+)\|r\|r \|cffc13d36Health\|r\|r \(\|cffc13d36(.+?)\|r\|r\)!')
    dmg_events = []

    excluded_entities = ['Kraken', 'Black Dragon', 'Flame Field', 'Jola the Cursed', 'Glenn', 'Meina', 'Crewman', 'Charybdis', 'Anthalon', 'Bloodspire']
    excluded_abilities = ['Corrosive Acid', "Black Dragon's Breath", "Red Dragon's Breath", "Clinging Flame", 
                         "Roar Aftershock", "Clinging Flame Explosion", "Boulder Rain", "Guided Missiles", 
                         "Earthquake", "Shoot Acid"]
    highest_hits = {}
    
    for line in lines:
        if dmg_pattern.match(line):
            result = dmg_pattern.findall(line)
            attacker, receiver, ability, damage, crit_type = result[0][1], result[0][2], result[0][3], int(result[0][4]), result[0][5]
            
            if receiver == player:
                if includePvE == 0:
                    if attacker.count(' ') == 0 and attacker not in excluded_entities and ability not in excluded_abilities:
                        dmg_events.append((ability, damage, crit_type))
                        if ability not in highest_hits or damage > highest_hits[ability]:
                            highest_hits[ability] = damage
                elif includePvE == 1:
                    dmg_events.append((ability, damage, crit_type))
                    if ability not in highest_hits or damage > highest_hits[ability]:
                        highest_hits[ability] = damage
    
    '''Collect & Calc events'''
    taken_log = {}
    crit_log = {}
    total_damage = 0
    
    for ability, damage, crit_type in dmg_events:
        taken_log[ability] = taken_log.get(ability, 0) + damage
        total_damage += damage
        if 'Critical' in crit_type:
            crit_log[ability] = crit_log.get(ability, 0) + damage
    
    # Apply tolerance filter (1% of total damage)
    tolerance = total_damage * 0.01
    taken_log = {k: v for k, v in taken_log.items() if v >= tolerance}
    taken_log = dict(sorted(taken_log.items(), key=lambda x: x[1], reverse=True))
    
    abilities = list(taken_log.keys())
    total_damage = list(taken_log.values())
    crit_damage = [crit_log.get(abi, 0) for abi in abilities]
    
    '''Plot Details'''
    taken_plot = plt.figure(figsize=(12,8), facecolor='#c1c1c1')
    plt.grid(axis='x', zorder=0)
    plt.barh(y=abilities, width=total_damage, color='blue', label='Total Damage', zorder=2)
    plt.barh(y=abilities, width=crit_damage, color='red', label='Critical Damage', zorder=3)
    plt.xlabel('Damage Taken', fontsize='x-large')
    plt.ylabel('Ability', fontsize='x-large')
    plt.gca().invert_yaxis()  # Flip the plot to have highest at the top
    plt.title(f'Damage Taken by {player} - {logfile} (1% Tolerance Applied)')
    plt.legend()
    
    # Annotate highest individual hits on the plot
    for ability in abilities:
        highest_hit = highest_hits.get(ability, 0)
        if highest_hit:
            ypos = abilities.index(ability)
            plt.text(taken_log[ability] * 1.02, ypos, f'Highest: {highest_hit}', va='center', ha='left', fontsize=10, color='black', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))
    
    current_values = plt.gca().get_xticks()
    plt.gca().set_xticklabels(['{:,.0f}'.format(x) for x in current_values])
    
    print("Highest Individual Hits:")
    for ability, damage in highest_hits.items():
        print(f"{ability}: {damage}")
    
    return taken_log, taken_plot
