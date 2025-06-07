import re
import pandas as pd
import xlsxwriter
import matplotlib.pyplot as plt

def DmgAbiLog(logfile, players, includePvE, excel_filename, graph_filename):
    with open(logfile, encoding='utf-8') as f:
        lines = f.readlines()

    '''Extract Elements'''
    dmg_pattern = re.compile(r'<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(.+?)\|r attacked (.+?)\|r using \|cff57d6ae(.*?)\|r\|r and caused \|cffc13d36-(\d+)\|r\|r \|cffc13d36Health\|r\|r \(\|cffc13d36(.+?)\|r\|r\)!')
    dmg_events = []

    for line in lines:
        if dmg_pattern.match(line):
            result = dmg_pattern.findall(line)
            if includePvE == 0:
                if result[0][2].count(' ') == 0 \
                and result[0][1].count(' ') == 0 \
                and not any(ele in ['Kraken'] for ele in result[0]):
                    if not players:
                        dmg_events.append(result[0])
                    else:
                        if result[0][1] in players:
                            dmg_events.append(result[0])

            elif includePvE == 1:
                if not any(ele in result[0][1] for ele in ['Black Dragon', 'Kraken', 'Flame Field', 'Jola the Cursed']):
                    if not players:
                        dmg_events.append(result[0])
                    else:
                        if result[0][1] in players:
                            dmg_events.append(result[0])

    '''Collect & Calc events'''
    abi_logs = {player: {} for player in players}
    total_damage = {player: 0 for player in players}
    abilities_set = set()

    for event in dmg_events:
        player = event[1]
        ability = event[3]
        damage = int(event[4])

        if ability in abi_logs[player]:
            abi_logs[player][ability] += damage
        else:
            abi_logs[player][ability] = damage

        total_damage[player] += damage
        abilities_set.add(ability)

    abilities_list = list(abilities_set)

    # Create a Pandas DataFrame with separate columns for each player
    data = {'Ability': abilities_list}

    for player in players:
        damage = [abi_logs[player].get(ability, 0) for ability in abilities_list]
        percentage = [int((d / total_damage[player]) * 100) if total_damage[player] > 0 else 0 for d in damage]
        data[player] = damage
        data[player + ' (%)'] = percentage

    df = pd.DataFrame(data)

    # Filter out results below 2% percentual damage
    df = df[df[players[0] + ' (%)'] >= 2]

    # Sort the DataFrame by highest percentage for each ability
    df = df.sort_values(by=[players[0] + ' (%)'], ascending=False)

    # Save the data to an Excel file with alternating row colors
    writer = pd.ExcelWriter(excel_filename, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')

    workbook = writer.book
    worksheet = writer.sheets['Sheet1']

    # Define alternating row colors
    white_format = workbook.add_format({'bg_color': 'white'})
    gray_format = workbook.add_format({'bg_color': 'gray'})

    # Apply alternating row colors
    for i in range(1, len(df) + 1):
        worksheet.set_row(i, cell_format=white_format if i % 2 == 0 else gray_format)

    workbook.close()  # Close the workbook and save the Excel file

    # Create a grouped bar chart from the filtered data
    plt.figure(figsize=(12, 8))
    width = 0.125
    x = range(len(df))

    for i, player in enumerate(players):
        plt.bar([pos + i * width for pos in x], df[player + ' (%)'], width=width, label=player)

    plt.xlabel('Ability')
    plt.ylabel('Percentage Damage')
    plt.title('Ability Percentile Comparison')
    plt.legend()
    plt.xticks([pos + width for pos in x], df['Ability'], rotation=90)
    plt.tight_layout()

    # Save the chart as an image file
    plt.savefig(graph_filename, bbox_inches='tight')
    plt.show()
