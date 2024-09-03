import streamlit as st
from streamlit import session_state as state
import musicpy as mp
import json
import traceback

from utils.constants import RHYTHM_VARIANTS
from utils.app_utils.midi_audio import play_audio, export_to_midi_as_bytes
from utils.generators.generator import PopGenerator
from utils.plotting import plot_chords


def main():
    state['generator_params'] = state.get('generator_params', {})

    st.subheader('Song Generator')
    t1, t2 = st.tabs(['Setup', 'Generate'])


    with st.sidebar:
        with st.expander('Show generator parameters'):
            st.write(state['generator_params'])


    with t1:
        with st.expander('Submit custom chords', expanded=True):
            chord_json_form()

        with st.expander('Chord Parameters', expanded=False):
            select_chord_params_form()

        with st.expander('Melody Parameters', expanded=False):
            select_melody_params_form()

    with t2:
        with st.expander('Basic Parameters', expanded=True):
            select_basic_params_form()
    
        with st.expander('Track Generator', expanded=True):
            track_generator()

        if state['generator_params'].get('song', None) is not None:
            song = state['generator_params']['song']
            with st.expander('MIDI Player', expanded=True):
                st.write(song)
                fig = plot_chords(song, end_time=None)
                st.plotly_chart(fig, use_container_width=True)

            if st.button('Play'):
                audio = play_audio(song)
                if audio is not None:
                    st.audio(audio)
                
                # Generate MIDI bytes
                midi_fname = f'untitled.mid'
                midi_bytes = export_to_midi_as_bytes(song)

            


def track_generator():
    if state['generator_params'] == {}:
        st.error('You need to submit some paramaters first')
        return
    
    with st.form('Track Generator'):
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            with_chords = st.checkbox('Chords', value=True, disabled=True)
            with_bass = st.checkbox('Bass', value=True)
            with_melody = st.checkbox('Melody', value=True)

        submit_button = st.form_submit_button('Generate Track')

    if submit_button:
        if with_chords == False and with_bass == False and with_melody == False:
            st.error('You need to select at least one track')
            return
        
        try:
            bpm = state['generator_params'].get('bpm', 120)
            length = state['generator_params'].get('length', 10)
            melody_ins = state['generator_params'].get('melody_instrument', 25)
            chord_ins = state['generator_params'].get('chord_instrument', 47)

            chords = state['generator_params'].get('chord_list', [])
            key = state['generator_params'].get('key', 'C')
            mode = state['generator_params'].get('mode', 'major')
            progression = state['generator_params'].get('progression', None)
            chord_duration = state['generator_params'].get('chord_duration', 1)
            chord_intervals = state['generator_params'].get('chord_intervals', [1/8, 0])

            melody_octave = state['generator_params'].get('melody_octave', 3)
            melody_durations = state['generator_params'].get('melody_durations', [3/8, 5/8, 1/8, 1/2, 1/4, mp.beat(1/2,1), mp.beat(1/8,1)])

            bass_octave = state['generator_params'].get('bass_octave', 2)
            bass_rhythms = state['generator_params'].get('bass_rhythms', RHYTHM_VARIANTS[0]['rhythm'])

            pg = PopGenerator(
                scale=mp.scale(key, mode),
                length=length,
                bpm=bpm,
                chord_instrument=chord_ins,
                melody_instrument=melody_ins,

                chord_duration=chord_duration,
                selected_chord_intervals=chord_intervals,
                melody_durations=melody_durations,
                melody_octave=melody_octave,

                bass_octave=bass_octave,
                bass_rhythms=bass_rhythms,
            )
            if chords != []:
                st.info('Adding custom chords. Progression will be ignored')
                for chorddict in chords:
                    cname = chorddict['chord']
                    intervals= chorddict['intervals']
                    pattern = chorddict['pattern']
                    pitch = chorddict['pitch'] 
                    pg.add_chord(cname, pitch, pattern, interval=intervals)

            else:
                st.info('No custom chords provided, generating from progression')
                pg.set_chord_progressions(progression=progression)

            song = pg.generate_all(
                generate_chords=with_chords, 
                generate_bass=with_bass, 
                generate_melody=with_melody
            )
            state['generator_params']['song'] = song

        except Exception as e:
            st.error(f'Error: {e}')
            traceback.print_exc()
            return




def select_basic_params_form():
    with st.form('Select Parameters'): 
        st.write('Basic parameters')

        c1, c2 = st.columns([1,1])
        with c1: 
            selected_bpm = st.slider('BPM', min_value=50, max_value=200, value=120, help='BPM, determines the speed of the song')
            selected_melody_instrument = st.selectbox('Melody Instrument', options=list(mp.database.INSTRUMENTS.keys()), index=6, help='Select the instrument for the melody')
        with c2:
            selected_length = st.slider('Length', min_value=8, max_value=32, value=16, help='Length of the song in bars')
            selected_chord_instrument = st.selectbox('Chord Instrument', options=list(mp.database.INSTRUMENTS.keys()), index=0, help='Select the instrument for the arpegiator/chord')

        if st.form_submit_button('Submit'):
            state['generator_params']['bpm'] = selected_bpm
            state['generator_params']['length'] = selected_length
            state['generator_params']['melody_instrument'] = selected_melody_instrument
            state['generator_params']['chord_instrument'] = selected_chord_instrument



def select_chord_params_form():
    st.info('Optional if you already provided your custom chords')
    with st.form('Select Chord Parameters'):
        st.write('Select the key and the mode')
        c1, c2 = st.columns([1,1])
        with c1:
            selected_key = st.selectbox('Select key', options=AVAILABLE_KEYS)
        with c2:
            selected_mode = st.selectbox('Select mode', options=AVAILABLE_MODES)

        st.divider()

        st.write('Chord parameters')
        c1, c2 = st.columns([1,1])
        with c1:
            # selected_progression = st.selectbox('Select chord progression', options=AVAILABLE_PROGRESSIONS, help='4 bar or 8 bar chord progression. Numbers represent the chord degree in scale.')
            selected_progression = st.text_input('Enter chord progression', value='45634561', placeholder='1245', help='4 bar or 8 bar chord progression. Numbers represent the chord degree in scale.')
        with c2:
            selected_chord_duration = st.selectbox('Select chord duration', options=[1/2, 1, 2], index=0, help='Duration of chord before it cycles to the next chord')
        selected_chord_intervals = st.multiselect('Select chord interval', options=AVAILABLE_CHORD_INTERVALS, default=[1/8, 0], help='Longer duration means slower arpegiator. Zero means chord has all notes played at once. Randomized in list.')

        if st.form_submit_button('Submit'):
            if selected_chord_intervals == []:
                st.error('You need to select at least one chord interval')
                return
    
            state['generator_params']['mode'] = selected_mode
            state['generator_params']['key'] = selected_key
            state['generator_params']['progression'] = selected_progression
            state['generator_params']['chord_duration'] = selected_chord_duration
            state['generator_params']['chord_intervals'] = selected_chord_intervals



def select_melody_params_form():
    with st.form('Select Melody Parameters'):
        st.write('Melody parameters')
        selected_melody_octave= st.selectbox('Melody pitch', options=[2,3,4,5,6,7], index=2, help='Melody notes are played at a higher or lower octave than the chord. Negative numbers are lower, positive numbers are higher.')
        rest_list = [f'rest({duration})' for duration in AVAILABLE_DURATIONS]
        melody_duration_options = AVAILABLE_DURATIONS + rest_list
        selected_melody_durations = st.multiselect('Select melody duration', options=melody_duration_options, default=[0.1875, 0.375, 'rest(0.1875)'], help='Duration of melody notes. Rests are used to create a rest between notes. Randomized in list.')

    
        if st.form_submit_button('Submit'):
            if selected_melody_durations == []:
                st.error('You need to select at least one melody duration')
                return
            
            state['generator_params']['melody_octave'] = selected_melody_octave
            state['generator_params']['melody_durations'] = selected_melody_durations

    

        










def chord_json_form():
    with open('jsons/example.json', 'r') as f:
        json_file = f.read()
        example_json = json_file

    with st.form(key='iknowwhatimdoing'):
        json_text = st.text_area('Paste JSON here', height=300, placeholder=example_json, value=example_json)
        submit = st.form_submit_button('Submit')

    if submit:
        try:
            json_data = json.loads(json_text)
            cname = json_data[0].get('chord')

            # if parsed json is a chord json    
            if cname: 
                chd = mp.chord('')
                for sample in json_data: 
                    cname = sample.get('chord', 'Unknown')
                    intervals = sample.get('intervals', [])
                    pattern = sample.get('pattern', [])
                    pitch = sample.get('pitch', 4)
                    chd += mp.C(cname, pitch=pitch) @ pattern % (intervals, intervals)

        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_text = ''
            return

        state['generator_params']['chord_list'] = json_data
        st.success('JSON parsed successfully.')
        st.rerun()










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