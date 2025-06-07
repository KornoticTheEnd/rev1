import re
import matplotlib.pyplot as plt

def PotsLog(logfile, top_x=25):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    heal_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.*?)\|r targeted (.*?)\|r using \|cff57d6ae(Minor Healing Potion|Healing Potion|Grimoire|Ginseng)\|r\|r to restore \|cff9be85a(\d+)\|r\|r health\.')
    heal_events = []

    for line in lines:
        if heal_pattern.match(line):
            result = heal_pattern.findall(line)
            if result[0][1].strip() == result[0][2].strip():  # Self-targeted only
                heal_events.append(result[0])

    '''Collect & Calc events'''
    pots_log = {}
    for event in heal_events:
        receiver = event[1].strip()
        heal = int(event[4])

        if receiver not in pots_log:
            pots_log[receiver] = heal
        else:
            pots_log[receiver] += heal

    pots_log = dict(sorted(pots_log.items(), key=lambda x: x[1], reverse=True)[:top_x])

    '''Plot Details'''
    pots_plot = plt.figure(figsize=(12, 8), facecolor='#c1c1c1')
    ax = plt.gca()
    ax.grid(axis='x', zorder=0)
    ax.barh(y=range(len(pots_log)), width=list(pots_log.values()), color='green', zorder=2)
    ax.set_yticks(range(len(pots_log)))
    ax.set_yticklabels(list(pots_log.keys()))
    ax.invert_yaxis()
    ax.set_xlabel('Healing from Pots', fontsize='x-large')
    ax.set_ylabel('Entity', fontsize='x-large')
    ax.set_title(f'Healing from Pots - {logfile[:-4]}')
    
    # Fix tick labels
    xticks = ax.get_xticks()
    ax.set_xticks(xticks)
    ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])

    return pots_log, pots_plot
