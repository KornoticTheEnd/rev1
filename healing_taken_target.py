import re
import matplotlib.pyplot as plt

def HealReceivedByPlayer(logfile, player, includePvE):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    heal_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r targeted (.+?)\|r using \|cff57d6ae(.*?)\|r\|r to restore \|cff9be85a(\d+)\|r\|r health\.')
    heal_events = []

    excluded_entities = ['Kraken', 'Black Dragon', 'Flame Field', 'Jola the Cursed', 'Glenn', 'Meina', 'Crewman', 'Charybdis']

    for line in lines:
        if heal_pattern.match(line):
            result = heal_pattern.findall(line)
            if result[0][3] not in excluded_entities:
                if includePvE == 0:
                    if result[0][2] == player and result[0][1].count(' ') == 0:
                        heal_events.append(result[0])
                elif includePvE == 1:
                    if result[0][2] == player:
                        heal_events.append(result[0])

    '''Collect & Calc events'''
    heal_log = {}
    for event in heal_events:
        ability = event[3]
        heal = int(event[4])

        if ability in heal_log:
            heal_log[ability] += heal
        else:
            heal_log[ability] = heal

    heal_log = dict(sorted(heal_log.items(), key=lambda x: x[1], reverse=False)[-15:])

    '''Plot Details'''
    heal_plot = plt.figure(figsize=(12,8), facecolor='#c1c1c1')
    plt.grid(axis='x', zorder=0)
    plt.barh(width=list(heal_log.values()), y=list(heal_log.keys()), color='green', zorder=2)
    
    if len(heal_log) > 20:
        plt.ylim(top=20)

    plt.xlabel('Healing', fontsize='x-large')
    plt.ylabel('Ability', fontsize='x-large')
    plt.title(f'Healing Taken by {player}')
    
    current_values = plt.gca().get_xticks()
    plt.gca().set_xticklabels(['{:,.0f}'.format(x) for x in current_values])

    return heal_log, heal_plot
