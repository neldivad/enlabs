import streamlit as st 
from streamlit import session_state as state
import json
import musicpy as mp

from utils.app_utils.midi_audio import play_audio, export_to_midi_as_bytes, download_midi_no_refresh
from utils.plotting import plot_chords
from utils.constants import RHYTHM_VARIANTS
from utils.generators.rhythm_generator import generate_rhythm_for_chord




STANDARD_NOTES = list(mp.database.standard2.keys())
CHORD_TYPES = list(mp.database.chord_function_dict.keys())



def main():
    state['r_select_chord'] = state.get('r_select_chord', {})
    state['r_select_rhythm'] = state.get('r_select_rhythm', {})

    st.title('Rhythm Generator')
    with st.sidebar:
        with st.expander('Show cache'):
            st.write(state['r_select_chord'])
            st.write(state['r_select_rhythm'])

    with st.expander('Select the chord or note', expanded=True):
        chord_form_part()


    if state['r_select_chord'] != {}:
        with st.expander('Rhythm for the chord', expanded=True):
            rhythm_chord_part()


        with st.expander('JSON data for rhythm chord', expanded=False):
            json_data = state['r_select_chord']
            st.text_area(label='JSON', value=json.dumps(json_data, indent=4))



def chord_form_part():
    rhythm_name_map = {rhythm['name']: rhythm for rhythm in RHYTHM_VARIANTS} # {'name': 'quarter', 'rhythm': 'b b b b', 'bars': 1} >> {'quarter': {'name': 'quarter', 'rhythm': 'b b b b', 'bars': 1}}

    selected_ts = st.selectbox('Select Time Signature', options=['3/4', '4/4'], index=1, help='Warning: Changing time signature may cause errors. Currently only supports 4/4')

    c1,c2,c3 = st.columns([1,1,1])
    with c1:
        selected_key = st.selectbox('Select Key', STANDARD_NOTES)
    with c2:
        selected_chord = st.selectbox('Select Chord', [None] + CHORD_TYPES)
    with c3: 
        selected_inversion = st.selectbox('Select Inversion', [None, 1,2])

    with c1:
        selected_rhythm = st.selectbox('Select rhythm', rhythm_name_map, index=2, help="Check JSON to view the beat. No support for custom rhythm for now.") 
    with c2: 
        selected_bars = st.number_input('Select number of bars', min_value=0, max_value=8, value=None, help="Tries to fit the rhythm within a range of selected bar")
    with c3:
        selected_accent = st.selectbox('Accented', options=[True, False], help="Replaces all rests and sustains with beats and lowers velocity if true.")

    submit_button = st.button(label='Generate rhythm for chord')

    if submit_button:
        if selected_bars in ['None', None, '', 0]:    
            state['r_select_chord']['bars'] = rhythm_name_map[selected_rhythm]['bars']
        else:
            state['r_select_chord']['bars'] = selected_bars
        state['r_select_chord']['key'] = selected_key
        state['r_select_chord']['chord'] = selected_chord
        state['r_select_chord']['inversion'] = selected_inversion
        state['r_select_chord']['rhythm_name'] = selected_rhythm
        state['r_select_chord']['rhythm'] = rhythm_name_map[selected_rhythm]['rhythm']
        state['r_select_chord']['accented'] = selected_accent
        state['r_select_chord']['time_signature'] = selected_ts
        st.rerun()


        

def rhythm_chord_part():
    if state['r_select_chord']['chord'] in [None, '']:
        cstr = f"{state['r_select_chord']['key']}"
        chord_obj = mp.chord(cstr)
    else:
        cstr = f"{state['r_select_chord']['key']}{state['r_select_chord']['chord']}"
        chord_obj = mp.C(cstr)

    rstr = state['r_select_chord']['rhythm']
    bars = state['r_select_chord']['bars']
    accent = state['r_select_chord']['accented']

    chd = generate_rhythm_for_chord(chord=chord_obj, rhythm=rstr, bars=bars, accent=accent)
    if st.button('Play'):
        audio = play_audio(chd)
        if audio is not None:
            st.audio(audio)
        
        # Generate MIDI bytes
        midi_fname = f'untitled.mid'
        midi_bytes = export_to_midi_as_bytes(chd)
        download_midi_no_refresh(midi_fname, midi_bytes)


    fig = plot_chords(chd, end_time=None, height=300)
    st.plotly_chart(fig, use_container_width=True)
