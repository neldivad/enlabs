import streamlit as st
from streamlit import session_state as state
import musicpy as mp

from utils.app_utils.midi_audio import play_audio, export_to_midi_as_bytes

def main():
    state['song'] = state.get('song', None)
    st.title('MIDI Generator') 

    with st.expander('MIDI Generator', expanded=True):
        form_part()

    if state['song'] is not None:
        song = state['song']
        with st.expander('MIDI Player', expanded=True):
            st.write(song)

        play_button = st.button('Play')
        if play_button:
            audio = play_audio(song)
            if audio is not None:
                st.audio(audio)

            # Generate MIDI bytes
            midi_fname = f'untitled.mid'
            midi_bytes = export_to_midi_as_bytes(song)
            download_midi_no_refresh(midi_fname, midi_bytes)



def form_part(): 
    AVAILABLE_KEYS = list(mp.database.standard2.keys())
    AVAILABLE_MODES = mp.database.diatonic_modes
    AVAILABLE_PROGRESSIONS = [
        '6451', '6415',
        '3456',
        '4536',
        '14561451',
        '1564', '15634145',
        '4156','4565','4563',
        '6341','6345',
    ]
    AVAILABLE_DURATIONS = [1/16, 2/16, 3/16, 4/16, 6/16, 8/16]
    AVAILABLE_CHORD_INTERVALS = [1/8, 0, 1/4, 1/2]

    with st.form('Select Parameters'): 
        st.write('Select the key and the mode')
        c1, c2 = st.columns([1,1])
        with c1:
            selected_key = st.selectbox('Select key', options=AVAILABLE_KEYS)
        with c2:
            selected_mode = st.selectbox('Select mode', options=AVAILABLE_MODES)

        st.divider()
        st.write('Basic parameters')

        c1, c2 = st.columns([1,1])
        with c1: 
            selected_bpm = st.slider('BPM', min_value=50, max_value=200, value=120)
            selected_melody_instrument = st.selectbox('Melody Instrument', options=list(mp.database.INSTRUMENTS.keys()), index=6)
        with c2:
            selected_length = st.slider('Length', min_value=10, max_value=30, value=10)
            selected_chord_instrument = st.selectbox('Chord Instrument', options=list(mp.database.INSTRUMENTS.keys()), index=0)

        st.divider()
        st.write('Chord parameters')
        c1, c2 = st.columns([1,1])
        with c1:
            selected_progression = st.selectbox('Select chord progression', options=AVAILABLE_PROGRESSIONS)
        with c2:
            selected_chord_duration = st.selectbox('Select chord duration', options=[1/2, 1, 2], index=0)
        selected_chord_intervals = st.multiselect('Select chord interval', options=AVAILABLE_CHORD_INTERVALS, default=[1/8, 0])


        st.divider()
        st.write('Melody parameters')
        selected_melody_octave= st.selectbox('Melody relative pitch', options=[-1, 0, 1, 2], index=1)

        rest_list = [f'rest({duration})' for duration in AVAILABLE_DURATIONS]
        melody_duration_options = AVAILABLE_DURATIONS + rest_list
        selected_melody_durations = st.multiselect('Select melody duration', options=melody_duration_options, default=[0.1875, 0.375, 'rest(0.1875)'])

        submit_button = st.form_submit_button('Submit')
    
    if submit_button:
        st.write(f'You selected the key {selected_key} and the mode {selected_mode}')
        s = mp.scale(selected_key, selected_mode)
        st.write(s)

        # parsing selects 
        melody_durations = [] 
        for duration in selected_melody_durations:
            if type(duration) == str: 
                beat = string_to_beat(duration)
                melody_durations.append(beat)
            else: 
                melody_durations.append(duration)

        melody_i = mp.database.INSTRUMENTS[selected_melody_instrument]
        chord_i = mp.database.INSTRUMENTS[selected_chord_instrument]

        # Call the write_pop function with the selected parameters
        song = mp.alg.write_pop(
            bpm=selected_bpm,
            length=[selected_length, selected_length],
            melody_chord_octave_diff=selected_melody_octave,
            melody_ins=melody_i,
            chord_ins=chord_i,
            scale_type=s,
            choose_chord_progressions=selected_progression,

            default_chord_durations=selected_chord_duration,
            choose_chord_intervals=selected_chord_intervals,
            choose_melody_durations=melody_durations,
        )
        state['song'] = song

    









def string_to_beat(string='rest(0.1875)'): 
    try: 
        b = mp.beat(float(string.split('(')[1].split(')')[0]), 1)
        return b
    except: 
        raise Exception('Unable to convert string to beat') 



@st.experimental_fragment
def download_midi_no_refresh(midi_fname, midi_bytes):
    """ 
    st.download_button() refreshes the page. The workaround is to wrap it in a fragment. 
    It is possible for the first download to fail.
    """
    st.download_button(
        label='Download MIDI', 
        data=midi_bytes, 
        file_name=midi_fname, 
        mime='audio/midi'
    )