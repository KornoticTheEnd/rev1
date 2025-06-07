import re
import matplotlib.pyplot as plt

def HealRecLog(logfile, player="", top_x=25, SelfOnly=0):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    heal_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r targeted (.+?)\|r using \|cff57d6ae(.*?)\|r\|r to restore \|cff9be85a(\d+)\|r\|r health\.')
    heal_events = []

    for line in lines:
        if heal_pattern.match(line):
            result = heal_pattern.findall(line)
            if SelfOnly == 0:
                if result[0][1] != result[0][2]:  # Exclude self heals
                    heal_events.append(result[0])
            else:
                heal_events.append(result[0])

    '''Collect & Calc events'''
    heal_log = {}
    for event in heal_events:
        target = event[2].strip()  # Use target instead of caster
        heal = int(event[4])

        if target not in heal_log:
            heal_log[target] = heal
        else:
            heal_log[target] += heal

    heal_log = dict(sorted(heal_log.items(), key=lambda x: x[1], reverse=True)[:top_x])  # Sort highest to lowest

    '''Plot Details'''
    heal_plot = plt.figure(figsize=(12, 8), facecolor='#c1c1c1')
    ax = plt.gca()
    ax.grid(axis='x', zorder=0)
    ax.barh(y=list(reversed(list(heal_log.keys()))), 
            width=list(reversed(list(heal_log.values()))), 
            color='green', zorder=2)
    ax.set_xlabel('Healing Received', fontsize='x-large')
    ax.set_ylabel('Player', fontsize='x-large')
    ax.set_title('Healing Received by Players')
    
    # Fix tick labels
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])

    return heal_log, heal_plot
