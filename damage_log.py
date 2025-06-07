import matplotlib.pyplot as plt
import re

def DamageLog(logfile, top_x, includePvE):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    dmg_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r attacked (.+?)\|r using \|cff57d6ae(.*?)\|r\|r and caused \|cffc13d36-(\d+)\|r\|r \|cffc13d36Health\|r\|r \(\|cffc13d36(.+?)\|r\|r\)!') 
    dmg_events = []

    excluded_entities = ['Red Dragon', 'Black Dragon', 'Kraken', 'Flame Field', 'Jola the Cursed', 'Glenn', 'Meina', 'Crewman', 'Charybdis', 'Anthalon', 'Bloodspire']
    excluded_abilities = ['Corrosive Acid', "Black Dragon's Breath", "Red Dragon's Breath", "Clinging Flame", 
                         "Roar Aftershock", "Clinging Flame Explosion", "Boulder Rain", "Guided Missiles", 
                         "Earthquake", "Shoot Acid"]

    for line in lines:
        if dmg_pattern.match(line):
            result = dmg_pattern.findall(line)
            ability_used = result[0][3]
            if includePvE == 0:
                if result[0][2].count(' ') == 0 \
                and result[0][1].count(' ') == 0 \
                and not any(ele in excluded_entities for ele in result[0]) \
                and ability_used not in excluded_abilities:
                    dmg_events.append(result[0])
            elif includePvE == 1:
                if not any(ele in result[0][1] for ele in excluded_entities) \
                and ability_used not in excluded_abilities:
                    dmg_events.append(result[0])

    '''Collect & Calc events'''
    dmg_log = {}
    for event in dmg_events:
        caster   = event[1]
        damage   = int(event[4])

        if caster not in dmg_log:
            dmg_log[caster] = damage
        else:
            dmg_log[caster] += damage

    dmg_log = dict(sorted(dmg_log.items(), key=lambda x:x[1], reverse=False)[-25:])

    '''Plot Details'''
    dmg_plot = plt.figure(figsize=(12,8), facecolor='#c1c1c1')
    ax = plt.gca()
    ax.grid(axis='x', zorder=0)
    ax.barh(width=list(dmg_log.values()), y=list(dmg_log.keys()), color='red', zorder=2)
    ax.set_xlabel('Damage', fontsize='x-large')
    ax.set_ylabel('Entity', fontsize='x-large')
    ax.set_title(logfile[:-4])
    
    # Fix tick labels
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])

    return dmg_log, dmg_plot
