import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Pattern
import pandas as pd
from collections import defaultdict

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(message)s')


class GhostAnalyzer:
    """
    Analyzes game logs to track Penetrating Dark Energy mechanics from the Black Dragon encounter.
    Tracks when debuffs are applied to players and if/when they are cleared.
    """
    
    def __init__(self):
        """Initialize the analyzer with regex patterns and empty state."""        # Define raw regex patterns
        self.patterns_raw = {            
            'spawn': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;Black Dragon\|r is casting \|cff57d6aePenetrating Dark Energy\|r\|r!",
            'debuff': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r was struck by a \|cff57d6aePenetrating Dark Energy\|r\|r debuff!",
            'clear': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;(.+?)\|r's \|cff57d6aePenetrating Dark Energy\|r\|r debuff cleared",
            'power': r"<(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|ic23895;Black Dragon\|r gained the buff: \|cff57d6aeDevilish Contract\|r\|r"
        }
        
        # Compile patterns for better performance
        self.patterns: Dict[str, Pattern] = {
            name: re.compile(pattern) for name, pattern in self.patterns_raw.items()
        }
        
        self.reset()
    
    def reset(self) -> None:
        """Reset the analyzer state for a new analysis."""
        self.waves: List[Dict[str, Any]] = []
        self.current_wave: Optional[Dict[str, Any]] = None
        self.player_stats = defaultdict(lambda: {'total': 0, 'cleared': 0, 'failed': 0, 'avg_time': 0.0})
        self.boss_power: int = 0
        self.debuff_events: List[Dict[str, Any]] = []
        # Track active debuffs by player for faster lookups
        self.active_debuffs: Dict[str, Dict[str, Any]] = {}

    def parse_timestamp(self, ts_str: str) -> datetime:
        """Parse a timestamp string into a datetime object.
        
        Args:
            ts_str: String timestamp in format 'YYYY-MM-DD HH:MM:SS'
            
        Returns:
            datetime object
        """
        try:
            return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logging.error(f"Failed to parse timestamp '{ts_str}': {e}")
            # Return current time as fallback
            return datetime.now()
        
    def analyze_log(self, log_data: str) -> Dict[str, Any]:
        """Analyze a log file for ghost mechanics.
        
        Args:
            log_data: The full log content as a string
            
        Returns:
            Dictionary containing analysis results
        """
        self.reset()
        
        logging.info("Starting ghost analysis...")
        lines = log_data.splitlines()
        total_lines = len(lines)
        logging.info(f"Total lines in log: {total_lines}")
        line_count = 0
        pattern_matches = {'spawn': 0, 'debuff': 0, 'clear': 0, 'power': 0}
        
        # Log example patterns we're looking for
        logging.info("Ghost patterns to match:")
        for pattern_name, pattern in self.patterns_raw.items():
            logging.info(f"{pattern_name}: {pattern}")
        
        # Process the log line by line
        for line in lines:
            line_count += 1
            
            # Log sample lines periodically for debugging
            if line_count % 1000 == 0:
                logging.info(f"Processing line {line_count}/{total_lines} ({line_count/total_lines*100:.1f}%)")
                logging.info(f"Sample line: {line[:200]}")
            
            # Check for pattern matches one by one to avoid redundant regex searches
            # Check spawn
            if spawn_match := self.patterns['spawn'].search(line):
                pattern_matches['spawn'] += 1
                if self.current_wave:
                    self.waves.append(self.current_wave)
                timestamp = self.parse_timestamp(spawn_match.group(1))
                self.current_wave = {'start': timestamp, 'players': [], 'clears': [], 'times': []}
                logging.info(f"Found ghost spawn at {timestamp}")
                continue  # Skip other checks for this line
                    # Check debuff
            elif debuff_match := self.patterns['debuff'].search(line):
                pattern_matches['debuff'] += 1
                if not self.current_wave:
                    continue
                timestamp = self.parse_timestamp(debuff_match.group(1))
                player = debuff_match.group(2).strip()
                
                # Skip non-player entities (mounts, pets, etc.)
                if "Mount" in player or "Companion" in player:
                    logging.info(f"Skipping non-player entity: {player}")
                    continue
                
                # Only track new debuffs for this player in the current wave
                if player not in self.current_wave['players']:
                    self.current_wave['players'].append(player)
                    self.player_stats[player]['total'] += 1
                
                # Create debuff event and add to tracking
                event = {'player': player, 'start': timestamp, 'cleared': False}
                self.debuff_events.append(event)
                self.active_debuffs[player] = event
                logging.info(f"Found ghost debuff on {player} at {timestamp}")
                continue
                
            # Check clear
            elif clear_match := self.patterns['clear'].search(line):
                pattern_matches['clear'] += 1
                timestamp = self.parse_timestamp(clear_match.group(1))
                player = clear_match.group(2).strip()
                logging.info(f"Found ghost clear for {player} at {timestamp}")
                
                # Check if player has an active debuff (much faster than iterating all events)
                if player in self.active_debuffs:
                    event = self.active_debuffs[player]
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
                    # Remove from active debuffs
                    del self.active_debuffs[player]
                continue
                        
            # Check power gain
            elif power_match := self.patterns['power'].search(line):
                pattern_matches['power'] += 1
                self.boss_power += 10  # Each stack is 10%
                logging.info(f"Found boss power gain at {self.parse_timestamp(power_match.group(1))}")
                
        # Add final wave
        if self.current_wave:
            self.waves.append(self.current_wave)        # Calculate final stats
        for player in self.player_stats:
            self.player_stats[player]['failed'] = (
                self.player_stats[player]['total'] - self.player_stats[player]['cleared']
            )
            
        logging.info("Ghost analysis complete")
        logging.info(f"Pattern matches: {pattern_matches}")
        logging.info(f"Total waves found: {len(self.waves)}")
        logging.info(f"Total players affected: {len(self.player_stats)}")
        logging.info(f"Final boss power: {self.boss_power}%")
        logging.info(f"Active uncleared debuffs: {len(self.active_debuffs)}")

        return self.generate_report()
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate a final report from the analysis results.
        
        Returns:
            Dictionary containing:
                - success: Whether the analysis found any waves
                - player_stats: DataFrame with player performance stats
                - wave_summary: DataFrame with wave-by-wave stats
                - total_waves: Number of waves found
                - boss_power: Final boss power percentage
                - debuff_events: Raw event data for all debuffs
        """
        if not self.waves:
            return {
                'success': False,
                'message': 'No ghost waves found in log'
            }        # Convert player stats to DataFrame with error handling
        player_data = []
        for player, stats in self.player_stats.items():
            try:
                clear_rate = f"{(stats['cleared'] / max(stats['total'], 1) * 100):.1f}%" if stats['total'] > 0 else "N/A"
                avg_time = f"{stats['avg_time']:.1f}s" if stats['avg_time'] > 0 else "N/A"
                
                player_data.append({
                    'Player': player,
                    'Total': stats['total'],
                    'Cleared': stats['cleared'],
                    'Failed': stats['failed'],
                    'Clear Rate': clear_rate,
                    'Avg Clear Time': avg_time
                })
            except Exception as e:
                logging.error(f"Error processing player {player}: {e}")
                continue
                
        # Create DataFrame from collected data
        stats_df = pd.DataFrame(player_data) if player_data else pd.DataFrame()

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
    def stream_log_analysis(self, log_file: str, chunk_size: int = 10000) -> Dict[str, Any]:
        """Process a large log file in chunks to conserve memory.
        
        This method is useful for very large log files that would consume too
        much memory if loaded entirely. It reads and processes the file in chunks.
        
        Args:
            log_file: Path to the log file
            chunk_size: Number of lines to process at once
            
        Returns:
            Same dictionary as analyze_log
        """
        self.reset()
        logging.info(f"Starting streaming ghost analysis of {log_file}...")
        
        pattern_matches = {'spawn': 0, 'debuff': 0, 'clear': 0, 'power': 0}
        line_count = 0
        
        try:
            # First pass to count total lines (optional, can be removed to save time)
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                total_lines = sum(1 for _ in f)
                logging.info(f"Total lines in log: {total_lines}")
                
            # Second pass to actually process data
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines_buffer = []
                
                for line in f:
                    lines_buffer.append(line)
                    line_count += 1
                    
                    # Process in chunks to conserve memory
                    if len(lines_buffer) >= chunk_size:
                        chunk_data = ''.join(lines_buffer)
                        self._process_log_chunk(chunk_data, pattern_matches, line_count - chunk_size + 1)
                        lines_buffer = []
                        logging.info(f"Processed {line_count}/{total_lines} lines ({line_count/total_lines*100:.1f}%)")
                
                # Process remaining lines
                if lines_buffer:
                    chunk_data = ''.join(lines_buffer)
                    self._process_log_chunk(chunk_data, pattern_matches, line_count - len(lines_buffer) + 1)
        
        except Exception as e:
            logging.error(f"Error processing log file: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
        # Calculate final stats same as in analyze_log
        if self.current_wave:
            self.waves.append(self.current_wave)
            
        for player in self.player_stats:
            self.player_stats[player]['failed'] = (
                self.player_stats[player]['total'] - self.player_stats[player]['cleared']
            )
            
        logging.info("Ghost analysis complete")
        logging.info(f"Pattern matches: {pattern_matches}")
        logging.info(f"Total waves found: {len(self.waves)}")
        logging.info(f"Total players affected: {len(self.player_stats)}")
        logging.info(f"Final boss power: {self.boss_power}%")
        logging.info(f"Active uncleared debuffs: {len(self.active_debuffs)}")

        return self.generate_report()
        
    def _process_log_chunk(self, chunk_data: str, pattern_matches: Dict[str, int], start_line: int) -> None:
        """Internal method to process a chunk of log data.
        
        Args:
            chunk_data: String containing a chunk of the log file
            pattern_matches: Dictionary to update with pattern match counts
            start_line: The line number where this chunk begins
        """
        for i, line in enumerate(chunk_data.splitlines()):
            line_num = start_line + i
            
            # Check spawn
            if spawn_match := self.patterns['spawn'].search(line):
                pattern_matches['spawn'] += 1
                if self.current_wave:
                    self.waves.append(self.current_wave)
                timestamp = self.parse_timestamp(spawn_match.group(1))
                self.current_wave = {'start': timestamp, 'players': [], 'clears': [], 'times': []}
                continue
                    # Check debuff
            elif debuff_match := self.patterns['debuff'].search(line):
                pattern_matches['debuff'] += 1
                if not self.current_wave:
                    continue
                timestamp = self.parse_timestamp(debuff_match.group(1))
                player = debuff_match.group(2).strip()
                
                # Skip non-player entities (mounts, pets, etc.)
                if "Mount" in player or "Companion" in player:
                    continue
                
                # Only track new debuffs for this player in the current wave
                if player not in self.current_wave['players']:
                    self.current_wave['players'].append(player)
                    self.player_stats[player]['total'] += 1
                
                # Create debuff event and add to tracking
                event = {'player': player, 'start': timestamp, 'cleared': False}
                self.debuff_events.append(event)
                self.active_debuffs[player] = event
                continue
                
            # Check clear
            elif clear_match := self.patterns['clear'].search(line):
                pattern_matches['clear'] += 1
                timestamp = self.parse_timestamp(clear_match.group(1))
                player = clear_match.group(2).strip()
                
                # Check if player has an active debuff
                if player in self.active_debuffs:
                    event = self.active_debuffs[player]
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
                    # Remove from active debuffs
                    del self.active_debuffs[player]
                continue
                        
            # Check power gain
            elif power_match := self.patterns['power'].search(line):
                pattern_matches['power'] += 1
                self.boss_power += 10  # Each stack is 10%


if __name__ == "__main__":
    # This allows the module to be imported without running UI code
    pass
