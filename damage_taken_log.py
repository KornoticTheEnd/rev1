import re
import matplotlib.pyplot as plt

def DmgRecLog(logfile, top_x, includePvE):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    dmg_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r attacked (.+?)\|r using \|cff57d6ae(.*?)\|r\|r and caused \|cffc13d36-(\d+)\|r\|r \|cffc13d36Health\|r\|r \(\|cffc13d36(.+?)\|r\|r\)!')
    dmg_events = []

    excluded_entities = ['Black Dragon', 'Kraken', 'Flame Field', 'Jola the Cursed', 'Glenn', 'Meina', 'Crewman', 'Charybdis', 'Anthalon', 'Bloodspire', 'Nightmare Warrior','Nightmare Archer','Scarlet Incubus']
    excluded_abilities = ['Corrosive Acid', "Black Dragon's Breath", "Red Dragon's Breath", "Clinging Flame", 
                         "Roar Aftershock", "Clinging Flame Explosion", "Boulder Rain", "Guided Missiles", 
                         "Earthquake", "Twisted Dance", "Anthalon's Sacrifice", "Crimson Mist", "Crimson Explosion", "Twisted Spear"]
    
    for line in lines:
        if dmg_pattern.match(line):
            result = dmg_pattern.findall(line)
            attacker = result[0][1].strip()
            receiver = result[0][2].strip()
            ability = result[0][3]

            # More strict PvE filtering
            if includePvE == 0:
                # Only include player-vs-player damage
                if (attacker.count(' ') == 0 and receiver.count(' ') == 0 and
                    attacker not in excluded_entities and
                    ability not in excluded_abilities):
                    dmg_events.append(result[0])
            else:
                # Include all damage except from excluded entities
                if attacker not in excluded_entities and ability not in excluded_abilities:
                    dmg_events.append(result[0])

    '''Collect & Calc events'''
    drec_log = {}
    for event in dmg_events:
        receiver = event[2]
        damage = int(event[4])

        if receiver not in drec_log:
            drec_log[receiver] = damage
        else:
            drec_log[receiver] += damage

    drec_log = dict(sorted(drec_log.items(), key=lambda x: x[1], reverse=False)[-top_x:])

    '''Plot Details'''
    drec_plot = plt.figure(figsize=(12, 8), facecolor='#c1c1c1')
    ax = plt.gca()
    ax.grid(axis='x', zorder=0)
    ax.barh(width=list(drec_log.values()), y=list(drec_log.keys()), color='blue', zorder=2)
    ax.set_xlabel('Damage Received', fontsize='x-large')
    ax.set_ylabel('Entity', fontsize='x-large')
    ax.set_title('Damage Taken by Players')
    
    # Fix tick labels
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])

    return drec_log, drec_plot
