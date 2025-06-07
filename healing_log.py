import re
import matplotlib.pyplot as plt

def HealingLog(logfile, top_x, includeSelf):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    heal_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r targeted (.+?)\|r using \|cff57d6ae(.*?)\|r\|r to restore \|cff9be85a(\d+)\|r\|r health\.')
    heal_events = []

    for line in lines:
        if heal_pattern.match(line):
            result = heal_pattern.findall(line)
            if includeSelf == 1:
                heal_events.append(result[0])
            elif includeSelf == 0:
                if result[0][1] != result[0][2]:
                    heal_events.append(result[0])

    '''Collect & Calc events'''
    heal_log = {}
    for event in heal_events:
        caster = event[1]
        heal = int(event[4])

        if caster not in heal_log:
            heal_log[caster] = heal
        else:
            heal_log[caster] += heal

    heal_log = dict(sorted(heal_log.items(), key=lambda x: x[1], reverse=False)[-20:])

    '''Plot Details'''
    heal_plot = plt.figure(figsize=(12, 18), facecolor='#c1c1c1')
    ax = plt.gca()
    ax.grid(axis='x', zorder=0)
    ax.barh(width=list(heal_log.values()), y=list(heal_log.keys()), color='green', zorder=2)
    ax.set_xlabel('Healing', fontsize='x-large')
    ax.set_ylabel('Entity', fontsize='x-large')
    ax.set_title(logfile[:-4])
    
    # Fix tick labels
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])

    return heal_log, heal_plot
