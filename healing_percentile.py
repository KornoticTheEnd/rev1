import re
import pandas as pd
import matplotlib.pyplot as plt

def HealAbiLog(logfile, players, includeSelf):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()
        
    '''Extract Elements'''
    heal_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r targeted (.+?)\|r using \|cff57d6ae(.*?)\|r\|r to restore \|cff9be85a(\d+)\|r\|r health\.')
    heal_events = []

    for line in lines:
        if heal_pattern.match(line):
            result = heal_pattern.findall(line)
            if includeSelf == 1:
                if not players or result[0][1] in players:
                    heal_events.append(result[0])
            elif includeSelf == 0:
                if result[0][1] != result[0][2] and (not players or result[0][1] in players):
                    heal_events.append(result[0])

    '''Collect & Calc events'''
    heal_logs = {player: {} for player in players}
    total_healing = {player: 0 for player in players}
    abilities_set = set()

    for event in heal_events:
        player = event[1]
        ability = event[3]
        healing = int(event[4])

        if player in players:
            heal_logs[player][ability] = heal_logs[player].get(ability, 0) + healing
            total_healing[player] += healing
            abilities_set.add(ability)

    abilities_list = list(abilities_set)

    # Create DataFrame
    data = {'Ability': abilities_list}
    for player in players:
        healing = [heal_logs[player].get(ability, 0) for ability in abilities_list]
        percentage = [int((h / total_healing[player]) * 100) if total_healing[player] > 0 else 0 for h in healing]
        data[player] = healing
        data[player + ' (%)'] = percentage

    df = pd.DataFrame(data)

    # Filter out rows with <1% healing for all players
    percentage_cols = [player + ' (%)' for player in players]
    df = df[df[percentage_cols].sum(axis=1) > 0]

    # Sort DataFrame by the first player's healing percentage
    if not df.empty:
        df = df.sort_values(by=players[0] + ' (%)', ascending=False)
    else:
        print("No significant healing data found after filtering.")
        return None

    '''Plot the Data'''
    if not df.empty:
        plt.figure(figsize=(15, 6))
        width = 0.12
        x = range(len(df))

        for i, player in enumerate(players):
            plt.bar([pos + i * width for pos in x], df[player + ' (%)'], width=width, label=player)

        plt.xlabel('Ability')
        plt.ylabel('Percentage Healing')
        plt.title('Ability Healing Comparison')
        plt.legend()
        plt.xticks([pos + (len(players) / 2 - 0.5) * width for pos in x], df['Ability'], rotation=45)
        plt.tight_layout()
        plt.show()
    else:
        print("No data available for plotting.")

    return df
