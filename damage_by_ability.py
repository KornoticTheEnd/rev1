import re
import matplotlib.pyplot as plt

def DmgAbiLog(logfile, player, includePvE):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()

    '''Extract Elements'''
    dmg_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r attacked (.+?)\|r using \|cff57d6ae(.*?)\|r\|r and caused \|cffc13d36-(\d+)\|r\|r \|cffc13d36Health\|r\|r \(\|cffc13d36(.+?)\|r\|r\)!')
    dmg_events = []

    excluded_entities = ['Kraken', 'Black Dragon', 'Flame Field', 'Jola the Cursed', 'Glenn', 'Meina', 'Crewman', 'Charybdis']
    highest_hits = {}
    damage_by_ability = {}
    crit_count = {}
    total_count = {}

    for line in lines:
        if dmg_pattern.match(line):
            result = dmg_pattern.findall(line)
            attacker, receiver, ability, damage, crit_type = result[0][1], result[0][2], result[0][3], int(result[0][4]), result[0][5]

            if attacker == player:
                if includePvE == 0:
                    if receiver.count(' ') == 0 and receiver not in excluded_entities:
                        dmg_events.append((ability, damage, crit_type))
                        if ability not in highest_hits or damage > highest_hits[ability]:
                            highest_hits[ability] = damage
                        if ability not in damage_by_ability:
                            damage_by_ability[ability] = []
                        damage_by_ability[ability].append(damage)

                        if 'Critical' in crit_type:
                            crit_count[ability] = crit_count.get(ability, 0) + 1
                        total_count[ability] = total_count.get(ability, 0) + 1
                elif includePvE == 1:
                    dmg_events.append((ability, damage, crit_type))
                    if ability not in highest_hits or damage > highest_hits[ability]:
                        highest_hits[ability] = damage
                    if ability not in damage_by_ability:
                        damage_by_ability[ability] = []
                    damage_by_ability[ability].append(damage)

                    if 'Critical' in crit_type:
                        crit_count[ability] = crit_count.get(ability, 0) + 1
                    total_count[ability] = total_count.get(ability, 0) + 1

    '''Collect & Calc events'''
    taken_log = {}
    crit_log = {}
    total_damage = 0
    total_crit_damage = 0

    for ability, damage, crit_type in dmg_events:
        taken_log[ability] = taken_log.get(ability, 0) + damage
        total_damage += damage
        if 'Critical' in crit_type:
            crit_log[ability] = crit_log.get(ability, 0) + damage
            total_crit_damage += damage

    tolerance = total_damage * 0.01
    taken_log = {k: v for k, v in taken_log.items() if v >= tolerance}
    taken_log = dict(sorted(taken_log.items(), key=lambda x: x[1], reverse=True))

    abilities = list(taken_log.keys())
    total_damage = list(taken_log.values())
    crit_damage = [crit_log.get(abi, 0) for abi in abilities]

    '''Plot Details'''
    fig, ax = plt.subplots(figsize=(12, 8), facecolor='#c1c1c1')
    ax.grid(axis='x', zorder=0)

    ax.barh(y=abilities, width=total_damage, color='blue', label='Total Damage', zorder=2)
    ax.barh(y=abilities, width=crit_damage, color='red', label='Critical Damage', zorder=3)

    ax.set_xlabel('Damage Done', fontsize='x-large')
    ax.set_ylabel('Ability', fontsize='x-large')
    ax.invert_yaxis()
    ax.set_title(f'Damage Done by {player} - {logfile} (1% Tolerance Applied)')

    for idx, ability in enumerate(abilities):
        total_crit = crit_log.get(ability, 0)
        crit_percentage = (total_crit / total_damage[idx]) * 100 if total_damage[idx] > 0 else 0
        if crit_percentage > 0:
            crit_chance = (crit_count.get(ability, 0) / total_count.get(ability, 1)) * 100
            crit_info = f'Crit Damage: {crit_percentage:.1f}%\nCrit Chance: {crit_chance:.1f}%'
            avg_damage = sum(damage_by_ability[ability]) / len(damage_by_ability[ability])
            avg_damage = round(avg_damage, 1)
            highest_hit = highest_hits.get(ability, 0)
            avg_info = f'High: {highest_hit}  Ave: {avg_damage}'

            ax.text(crit_damage[idx] * 1.05, idx, f'{crit_info}\n{avg_info}', va='center', ha='left', fontsize=9,
                    color='black', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3', alpha=0.7))

    plt.subplots_adjust(right=0.85)
    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # Ensure x-axis labels show correct values
    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels([f'{int(x):,}' for x in ax.get_xticks()], fontsize=10)

    return taken_log, fig
