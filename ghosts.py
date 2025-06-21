import re
import logging
from datetime import datetime
import pandas as pd
from collections import defaultdict

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

class GhostAnalyzer:
    def __init__(self):
        self.patterns = {            
            'spawn': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;Black Dragon\|r is casting \|cff57d6aePenetrating Dark Energy\|r\|r!",
            'debuff': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r was struck by a \|cff57d6aePenetrating Dark Energy\|r\|r debuff!",
            'clear': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r's \|cff57d6aePenetrating Dark Energy\|r\|r debuff cleared",
            'power': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;Black Dragon\|r gained the buff: \|cff57d6aeDevilish Contract\|r\|r"
        }
        self.reset()

    def reset(self):
        self.waves = []
        self.current_wave = None
        self.player_stats = defaultdict(lambda: {'total': 0, 'cleared': 0, 'failed': 0, 'avg_time': 0.0})
        self.boss_power = 0
        self.debuff_events = []

    def parse_timestamp(self, ts_str):
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        
    def analyze_log(self, log_data):
        self.reset()
        
        logging.info("Starting ghost analysis...")
        logging.info(f"Total lines in log: {len(log_data.splitlines())}")
        line_count = 0
        pattern_matches = {'spawn': 0, 'debuff': 0, 'clear': 0, 'power': 0}
        # Log example patterns we're looking for
        logging.info("Ghost patterns to match:")
        for pattern_name, pattern in self.patterns.items():
            logging.info(f"{pattern_name}: {pattern}")
        
        for line in log_data.splitlines():
            line_count += 1
            # Log sample lines periodically for debugging
            if line_count % 1000 == 0:
                logging.info(f"Sample line {line_count}: {line[:200]}")
            # Try to match each pattern and log results
            for pattern_name, pattern in self.patterns.items():
                if re.search(pattern, line):
                    logging.info(f"Found {pattern_name} match in line {line_count}: {line[:200]}")
            
            # Check spawn
            if spawn_match := re.search(self.patterns['spawn'], line):
                pattern_matches['spawn'] += 1
                if self.current_wave:
                    self.waves.append(self.current_wave)
                timestamp = self.parse_timestamp(spawn_match.group(1))
                self.current_wave = {'start': timestamp, 'players': [], 'clears': [], 'times': []}
                logging.info(f"Found ghost spawn at {timestamp}")
                  # Check debuff
            elif debuff_match := re.search(self.patterns['debuff'], line):
                pattern_matches['debuff'] += 1
                if not self.current_wave:
                    continue
                timestamp = self.parse_timestamp(debuff_match.group(1))
                player = debuff_match.group(2).strip()
                if player not in self.current_wave['players']:
                    self.current_wave['players'].append(player)
                    self.player_stats[player]['total'] += 1
                self.debuff_events.append({'player': player, 'start': timestamp, 'cleared': False})
                logging.info(f"Found ghost debuff on {player} at {timestamp}")
                
            # Check clear
            elif clear_match := re.search(self.patterns['clear'], line):
                pattern_matches['clear'] += 1
                timestamp = self.parse_timestamp(clear_match.group(1))
                player = clear_match.group(2).strip()
                logging.info(f"Found ghost clear for {player} at {timestamp}")
                
                # Find matching debuff event
                for event in reversed(self.debuff_events):
                    if event['player'] == player and not event['cleared']:
                        event['cleared'] = True
                        event['clear_time'] = timestamp
                        clear_time = (timestamp - event['start']).total_seconds()
                        
                        if self.current_wave and player in self.current_wave['players']:
                            self.current_wave['clears'].append(player)
                            self.current_wave['times'].append(clear_time)
                            self.player_stats[player]['cleared'] += 1
                            self.player_stats[player]['avg_time'] = (
                                (self.player_stats[player]['avg_time'] * (self.player_stats[player]['cleared'] - 1) + 
                                clear_time) / self.player_stats[player]['cleared']
                            )
                        break
                        
            # Check power gain
            elif power_match := re.search(self.patterns['power'], line):
                pattern_matches['power'] += 1
                self.boss_power += 10  # Each stack is 10%
                logging.info(f"Found boss power gain at line {line_count}")
                
        # Add final wave
        if self.current_wave:
            self.waves.append(self.current_wave)

        # Calculate final stats
        for player in self.player_stats:
            self.player_stats[player]['failed'] = (
                self.player_stats[player]['total'] - self.player_stats[player]['cleared']
            )

        logging.info("Ghost analysis complete")
        logging.info(f"Pattern matches: {pattern_matches}")
        logging.info(f"Total waves found: {len(self.waves)}")
        logging.info(f"Total players affected: {len(self.player_stats)}")
        logging.info(f"Final boss power: {self.boss_power}%")

        return self.generate_report()

    def generate_report(self):
        if not self.waves:
            return {
                'success': False,
                'message': 'No ghost waves found in log'
            }

        # Convert player stats to DataFrame
        stats_df = pd.DataFrame([
            {
                'Player': player,
                'Total': stats['total'],
                'Cleared': stats['cleared'],
                'Failed': stats['failed'],
                'Clear Rate': f"{(stats['cleared'] / stats['total'] * 100):.1f}%",
                'Avg Clear Time': f"{stats['avg_time']:.1f}s" if stats['avg_time'] > 0 else "N/A"
            }
            for player, stats in self.player_stats.items()
        ])

        # Sort by clear rate descending
        stats_df = stats_df.sort_values(
            by=['Clear Rate', 'Avg Clear Time'],
            ascending=[False, True]
        )

        # Wave summary
        wave_summary = []
        for i, wave in enumerate(self.waves, 1):
            failed = set(wave['players']) - set(wave['clears'])
            avg_time = sum(wave['times']) / len(wave['times']) if wave['times'] else 0
            wave_summary.append({
                'Wave': i,
                'Players Hit': len(wave['players']),
                'Cleared': len(wave['clears']),
                'Failed': len(failed),
                'Avg Clear Time': f"{avg_time:.1f}s",
                'Failed Players': ', '.join(failed) if failed else 'None'
            })

        return {
            'success': True,
            'player_stats': stats_df,
            'wave_summary': pd.DataFrame(wave_summary),
            'total_waves': len(self.waves),
            'boss_power': self.boss_power,
            'debuff_events': self.debuff_events
        }
if __name__ == "__main__":
    # This allows the module to be imported without running UI code
    pass
