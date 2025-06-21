import streamlit as st
import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# Import functions from script files
from damage_log import DamageLog
from damage_by_ability import DmgAbiLog
from damage_percentile import DmgAbiLog as DmgPercentileLog
from healing_log import HealingLog
from healing_by_target import HealAbiLog
from healing_received import HealRecLog
from healing_taken_target import HealReceivedByPlayer
from healing_percentile import HealAbiLog as HealPercentileLog
from damage_taken_log import DmgRecLog
from damage_taken_target import DmgTakenByPlayer
from healing_pots import PotsLog
from mend import parse_heal_log, calculate_heal_stats, plot_total_heals, plot_min_max_avg_heals, plot_mend_casts
from ghosts import GhostAnalyzer
from song_buff import plot_song_buff_data
from song_debuffs import plot_song_debuff_data
from damage_taken_from import DmgTakenFromLog
from healing_taken_from import HealTakenFromLog
from combo_tracker import ComboTracker, plot_combo_results
from cast_tracker import CastTracker, CAST_PATTERNS, plot_cast_results
from combined_analysis import generate_combined_analysis

# Add this helper function at the top of the file with other imports
def plot_data(ax, data, title, color):
    ax.grid(axis='x', zorder=0)
    ax.barh(y=list(reversed(list(data.keys()))), 
           width=list(reversed(list(data.values()))), 
           color=color)
    ax.set_xlabel(title)
    ax.set_ylabel('Entity')
    ax.set_title(title)
    xticks = ax.get_xticks()
    ax.set_xticklabels(['{:,.0f}'.format(x) for x in xticks])

# Set page config to wide mode
st.set_page_config(layout="wide")

# Load environment variables (optional for local dev)
if os.path.exists('.env.txt'):
    load_dotenv(dotenv_path='.env.txt')

# NOTE: On Streamlit Cloud, set environment variables (USERNAME1, PASSWORD1, etc.) via the web UI, not .env.txt

# Title
st.title("Log Analysis Dashboard")

# Authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Define users and passwords (support up to 10 users)
users = {
    os.getenv('USERNAME1'): os.getenv('PASSWORD1'),
    os.getenv('USERNAME2'): os.getenv('PASSWORD2'),
    os.getenv('USERNAME3'): os.getenv('PASSWORD3'),
    os.getenv('USERNAME4'): os.getenv('PASSWORD4'),
    os.getenv('USERNAME5'): os.getenv('PASSWORD5'),
    os.getenv('USERNAME6'): os.getenv('PASSWORD6'),
    os.getenv('USERNAME7'): os.getenv('PASSWORD7'),
    os.getenv('USERNAME8'): os.getenv('PASSWORD8'),
    os.getenv('USERNAME9'): os.getenv('PASSWORD9'),
    os.getenv('USERNAME10'): os.getenv('PASSWORD10'),
}

def authenticate(username, password):
    return users.get(username) == password

if not st.session_state.authenticated:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state.authenticated = True
            st.rerun()  # Changed from experimental_rerun() to rerun()
        else:
            st.error("Invalid username or password")
            
else:
    # Sidebar
    st.sidebar.title("Controls")

    # Single file uploader
    uploaded_file = st.sidebar.file_uploader("Choose a log file", type=['log'])

    if uploaded_file is not None:
        # Read file content directly into memory
        file_content = uploaded_file.read()
        
        # Use the uploaded file's name as a relative path
        save_path = uploaded_file.name

        # Analysis type selector with Combined Analysis and Combos & Casts at the top
        analysis_type = st.sidebar.selectbox(
            "Select Analysis Type",
            ["All Plots Combined", "All Player Plots", "Combined Analysis", "Combos & Casts", 
             "Damage Log", "Damage By Ability", "Damage Percentile Comparison", "Healing Log", 
             "Healing Done By Target", "Healing Received From Healers", "Healing Taken By Target",
             "Healing Taken From Who", "Healing Percentile Comparison",
             "Damage Taken Log", "Damage Taken By Target", "Damage Taken From Who",
             "Healing From Pots", "Ghosts", "Mend", "Song Buffs", "Song Debuffs"]
        )

        # Remove Healing Received From Healers from player name requirement
        if analysis_type in ["All Player Plots", "Damage By Ability", "Healing Done By Target",
                            "Healing Taken By Target", "Damage Taken By Target",
                            "Damage Taken From Who", "Healing Taken From Who"]:
            player_name = st.sidebar.text_input("Enter player name")

        # Multi-player input for percentile comparisons
        if analysis_type in ["Damage Percentile Comparison", "Healing Percentile Comparison"]:
            players = st.sidebar.text_area("Enter player names (one per line)")
            players = [p.strip() for p in players.split('\n') if p.strip()]

        # Common options
        includePvE = st.sidebar.checkbox("Include PvE")
        includeSelf = st.sidebar.checkbox("Include Self")

        # Generate button
        if st.sidebar.button("Generate Plot"):
            # Save uploaded file to a temporary file in the current directory
            with open("temp.log", "wb") as f:
                f.write(file_content)
            
            temp_path = "temp.log"
            
            # Clear any existing plots
            plt.clf()

            # Execute selected analysis
            try:
                if analysis_type == "All Plots Combined":
                    from combined_plots import generate_all_plots
                    with st.spinner('Generating all plots... This may take a while...'):
                        fig = generate_all_plots(temp_path, includePvE, includeSelf)
                        st.pyplot(fig)
                        
                elif analysis_type == "All Player Plots":
                    if not player_name:
                        st.error("Please enter a player name in the sidebar")
                    else:
                        from player_plots import generate_player_plots
                        with st.spinner('Generating player plots... This may take a while...'):
                            fig = generate_player_plots(temp_path, player_name, includePvE, includeSelf)
                            st.pyplot(fig)
                
                elif analysis_type == "Combined Analysis":
                    if not file_content:
                        st.error("No file content found")
                    else:    
                        with st.spinner('Processing combined log data...'):
                            try:
                                fig = generate_combined_analysis(temp_path, includePvE, includeSelf)
                                st.pyplot(fig)
                            except Exception as e:
                                st.error(f"Error generating combined analysis: {str(e)}")
                                
                elif analysis_type == "Damage Log":
                    dmg_log, plot = DamageLog(temp_path, (0, 24), includePvE)
                    st.pyplot(plot)
                
                elif analysis_type == "Damage By Ability":
                    if player_name:
                        dmg_log, plot = DmgAbiLog(temp_path, player_name, includePvE)
                        st.pyplot(plot)
                
                elif analysis_type == "Damage Percentile Comparison":
                    if players:
                        excel_filename = os.path.join("output", "damage_percentile.xlsx")
                        graph_filename = os.path.join("output", "damage_percentile.png")
                        DmgPercentileLog(temp_path, players, includePvE, excel_filename, graph_filename)
                        st.image(graph_filename)
                
                elif analysis_type == "Healing Log":
                    heal_log, plot = HealingLog(temp_path, (0, 24), includeSelf)
                    st.pyplot(plot)
                
                elif analysis_type == "Healing Done By Target":
                    if player_name:
                        heal_log, plot = HealAbiLog(temp_path, includeSelf, player_name)
                        st.pyplot(plot)
                
                elif analysis_type == "Healing Received From Healers":
                    heal_log, plot = HealRecLog(temp_path, "", 25, includeSelf)
                    st.pyplot(plot)
                
                elif analysis_type == "Healing Taken By Target":
                    if player_name:
                        heal_log, plot = HealReceivedByPlayer(temp_path, player_name, includePvE)
                        st.pyplot(plot)
                
                elif analysis_type == "Healing Percentile Comparison":
                    if players:
                        heal_df = HealPercentileLog(temp_path, players, includeSelf)
                        if heal_df is not None:
                            st.dataframe(heal_df)

                elif analysis_type == "Damage Taken Log":
                    dmg_log, plot = DmgRecLog(temp_path, 25, includePvE)
                    st.pyplot(plot)
                
                elif analysis_type == "Damage Taken By Target":
                    if player_name:
                        dmg_log, plot = DmgTakenByPlayer(temp_path, player_name, includePvE)
                        st.pyplot(plot)
                        
                elif analysis_type == "Damage Taken From Who":
                    if player_name:
                        dmg_log, plot = DmgTakenFromLog(temp_path, player_name, includePvE)
                        st.pyplot(plot)
                        
                elif analysis_type == "Healing From Pots":
                    pots_log, plot = PotsLog(temp_path, 25)
                    st.pyplot(plot)
                    
                elif analysis_type == "Ghosts":
                    try:
                        analyzer = GhostAnalyzer()
                        with open(temp_path, 'r', encoding='utf-8') as f:
                            log_data = f.read()
                        result = analyzer.analyze_log(log_data)
                        
                        if result['success']:
                            # Summary metrics
                            st.header("Summary")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Waves", result['total_waves'])
                            with col2:
                                total_players = len(result['player_stats'])
                                st.metric("Players Affected", total_players)
                            with col3:
                                st.metric("Boss Power", f"{result['boss_power']}%")
                                if result['boss_power'] >= 150:
                                    st.error("⚠️ Boss Enraged!")
                            
                            # Player Performance Table
                            st.header("Player Performance")
                            st.dataframe(result['player_stats'])
                            
                            # Wave Breakdown
                            st.header("Wave Analysis")
                            st.dataframe(result['wave_summary'])
                            
                            # Visualization
                            st.header("Clear Time Distribution")
                            fig, ax = plt.subplots(figsize=(10, 6))
                            
                            clear_times = [
                                (event['clear_time'] - event['start']).total_seconds()
                                for event in result['debuff_events']
                                if event['cleared']
                            ]
                            
                            if clear_times:
                                ax.hist(clear_times, bins=20, color='skyblue', edgecolor='black')
                                ax.axvline(x=37, color='red', linestyle='--', label='Fail threshold (37s)')
                                ax.set_xlabel('Clear Time (seconds)')
                                ax.set_ylabel('Count')
                                ax.set_title('Distribution of Ghost Clear Times')
                                ax.legend()
                                st.pyplot(fig)
                        else:
                            st.error(result['message'])
                            st.info("Make sure your log file contains ghost mechanics data")
                    except Exception as e:
                        st.error(f"Error analyzing ghost data: {str(e)}")
                        st.header("Summary")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Waves", result['total_waves'])
                        with col2:
                            total_players = len(result['player_stats'])
                            st.metric("Players Affected", total_players)
                        with col3:
                            st.metric("Boss Power", f"{result['boss_power']}%")
                            if result['boss_power'] >= 150:
                                st.error("⚠️ Boss Enraged!")
                        
                        # Player Performance Table
                        st.header("Player Performance")
                        st.dataframe(result['player_stats'])
                        
                        # Wave Breakdown
                        st.header("Wave Analysis")
                        st.dataframe(result['wave_summary'])
                        
                        # Visualization
                        st.header("Clear Time Distribution")
                        fig, ax = plt.subplots(figsize=(10, 6))
                        
                        clear_times = [
                            (event['clear_time'] - event['start']).total_seconds()
                            for event in result['debuff_events']
                            if event['cleared']
                        ]
                        
                        if clear_times:
                            ax.hist(clear_times, bins=20, color='skyblue', edgecolor='black')
                            ax.axvline(x=37, color='red', linestyle='--', label='Fail threshold (37s)')
                            ax.set_xlabel('Clear Time (seconds)')
                            ax.set_ylabel('Count')
                            ax.set_title('Distribution of Ghost Clear Times')
                            ax.legend()
                            
                            st.pyplot(fig)
                    else:
                        st.error(result['message'])
                        st.info("Make sure your log file contains ghost mechanics data")
                
                elif analysis_type == "Mend":
                    heal_data, mend_counts = parse_heal_log(temp_path)
                    heal_stats = calculate_heal_stats(heal_data)
                    fig, axes = plt.subplots(1, 3, figsize=(18, 7.5))
                    plot_total_heals(heal_stats, axes[0])
                    plot_min_max_avg_heals(heal_stats, mend_counts, heal_data, axes[1])
                    plot_mend_casts(mend_counts, axes[2])
                    plt.tight_layout()
                    st.pyplot(fig)
                
                elif analysis_type == "Song Buffs":
                    fig = plot_song_buff_data(temp_path)
                    st.pyplot(fig)
                
                elif analysis_type == "Song Debuffs":
                    fig = plot_song_debuff_data(temp_path)
                    st.pyplot(fig)

                elif analysis_type == "Healing Taken From Who":
                    if player_name:
                        heal_log, plot = HealTakenFromLog(temp_path, player_name, includeSelf)
                        st.pyplot(plot)

                elif analysis_type == "Combos & Casts":
                    # Add custom CSS to control container heights
                    st.markdown("""
                        <style>
                            .fixed-height {
                                height: 1px;
                                margin-bottom: 2rem;
                            }
                            .stPlotContainer {
                                margin-bottom: 2rem;
                            }
                        </style>
                    """, unsafe_allow_html=True)

                    with st.spinner('Processing log data...'):
                        st.warning("Cast tracking may take a while to process large log files...")
                        col1, col2 = st.columns(2)

                        # Process combos
                        tracker = ComboTracker(temp_path)
                        
                        # Process both columns in fixed-height containers
                        with col1:
                            with st.container():
                                st.markdown('<div class="fixed-height">', unsafe_allow_html=True)
                                st.subheader("Distress Combo")
                                distress_data = tracker.track_distress_combo()
                                if distress_data:
                                    fig = plot_combo_results(distress_data, 'Distress Combo Success', 'blue')
                                    st.pyplot(fig)
                                    plt.close(fig)
                                else:
                                    st.info("No Distress combo data found")
                                st.markdown('</div>', unsafe_allow_html=True)

                        with col2:
                            with st.container():
                                st.markdown('<div class="fixed-height">', unsafe_allow_html=True)
                                st.subheader("Discord Combo")
                                discord_data = tracker.track_discord_combo()
                                if discord_data:
                                    fig = plot_combo_results(discord_data, 'Discord Combo Success', 'purple')
                                    st.pyplot(fig)
                                    plt.close(fig)
                                else:
                                    st.info("No Discord combo data found")
                                st.markdown('</div>', unsafe_allow_html=True)

                        # Process casts in a new row
                        st.subheader("Cast Usage")
                        cast_container = st.container()
                        with cast_container:
                            with st.spinner('Processing cast data...'):
                                cast_counter = CastTracker(temp_path)
                                all_cast_data = cast_counter.track_casts(CAST_PATTERNS)
                                
                                if all_cast_data:
                                    all_cast_data = {k: v for k, v in all_cast_data.items() if v}
                                    if all_cast_data:
                                        abilities = list(all_cast_data.keys())
                                        mid_point = (len(abilities) + 1) // 2
                                        
                                        cast_col1, cast_col2 = st.columns(2)
                                        
                                        with cast_col1:
                                            for ability in abilities[:mid_point]:
                                                with st.container():
                                                    st.markdown('<div class="fixed-height">', unsafe_allow_html=True)
                                                    st.write(f"### {ability}")
                                                    fig = plot_cast_results(all_cast_data[ability], color='green')
                                                    if fig:
                                                        st.pyplot(fig)
                                                        plt.close(fig)
                                                    st.markdown('</div>', unsafe_allow_html=True)
                                        
                                        with cast_col2:
                                            for ability in abilities[mid_point:]:
                                                with st.container():
                                                    st.markdown('<div class="fixed-height">', unsafe_allow_html=True)
                                                    st.write(f"### {ability}")
                                                    fig = plot_cast_results(all_cast_data[ability], color='green')
                                                    if fig:
                                                        st.pyplot(fig)
                                                        plt.close(fig)
                                                    st.markdown('</div>', unsafe_allow_html=True)
                                    else:
                                        st.info("No cast data found")
            
            finally:
                # Clean up temporary file
                if os.path.exists("temp.log"):
                    os.remove("temp.log")