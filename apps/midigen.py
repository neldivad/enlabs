import streamlit as st
from streamlit import session_state as state
import musicpy as mp

from utils.app_utils.midi_audio import play_audio, export_to_midi_as_bytes
from utils.plotting import plot_chords

def main():
    state['song'] = state.get('song', None)
    st.title('MIDI Generator') 

    with st.expander('Help', expanded=False):
        confused()

    with st.expander('MIDI Generator', expanded=True):
        form_part()

    if state['song'] is not None:
        song = state['song']
        with st.expander('MIDI Player', expanded=True):
            st.write(song)
            fig = plot_chords(song, end_time=None)
            st.plotly_chart(fig, use_container_width=True)

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
            selected_bpm = st.slider('BPM', min_value=50, max_value=200, value=120, help='BPM, determines the speed of the song')
            selected_melody_instrument = st.selectbox('Melody Instrument', options=list(mp.database.INSTRUMENTS.keys()), index=6, help='Select the instrument for the melody')
        with c2:
            selected_length = st.slider('Length', min_value=10, max_value=30, value=10, help='Length of the song in bars')
            selected_chord_instrument = st.selectbox('Chord Instrument', options=list(mp.database.INSTRUMENTS.keys()), index=0, help='Select the instrument for the arpegiator/chord')

        st.divider()
        st.write('Chord parameters')
        c1, c2 = st.columns([1,1])
        with c1:
            # selected_progression = st.selectbox('Select chord progression', options=AVAILABLE_PROGRESSIONS, help='4 bar or 8 bar chord progression. Numbers represent the chord degree in scale.')
            selected_progression = st.text_input('Enter chord progression', value='45634561', placeholder='1245', help='4 bar or 8 bar chord progression. Numbers represent the chord degree in scale.')
        with c2:
            selected_chord_duration = st.selectbox('Select chord duration', options=[1/2, 1, 2], index=0, help='Duration of chord before it cycles to the next chord')
        selected_chord_intervals = st.multiselect('Select chord interval', options=AVAILABLE_CHORD_INTERVALS, default=[1/8, 0], help='Longer duration means slower arpegiator. Zero means chord has all notes played at once. Randomized in list.')


        st.divider()
        st.write('Melody parameters')
        selected_melody_octave= st.selectbox('Melody relative pitch', options=[-1, 0, 1, 2], index=1, help='Melody notes are played at a higher or lower octave than the chord. Negative numbers are lower, positive numbers are higher.')

        rest_list = [f'rest({duration})' for duration in AVAILABLE_DURATIONS]
        melody_duration_options = AVAILABLE_DURATIONS + rest_list
        selected_melody_durations = st.multiselect('Select melody duration', options=melody_duration_options, default=[0.1875, 0.375, 'rest(0.1875)'], help='Duration of melody notes. Rests are used to create a rest between notes. Randomized in list.')

        st.divider()
        st.write('Bass parameters')
        st.info('Not implemented yet') 

        st.divider()
        st.write('Drums parameters')
        st.info('Not implemented yet')

        submit_button = st.form_submit_button('Submit')
    
    if submit_button:
        if selected_melody_durations == []:
            st.error('You need to select at least one melody duration')
            return
        if selected_chord_intervals == []:
            st.error('You need to select at least one chord interval')
            return

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

    

def confused():
    st.warning("Don't know what to do?")

    st.markdown(help_md)
    pass 








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


help_md="""
> Oh no, so much buttons and sliders!

- **Just click submit and see what happens**
    - You learn how to tweak knobs better after you hear it. 

- **Change key, mode, and chord progression**
    - This is the part where the biggest differences between songs come from. You are highly encouraged to look up the music theory of key, mode, and chord progression. 

- **Add/remove intervals in chord, melody**

    - Algorithm randomly choose an interval after a note was played from arpegiator or melody. If you want to experience more variance in melody, you can change up the intervals. 
For better results, use abnormal time signatures like 3/8, 5/8 (there is a music theory behind why this is). Adding rests to the melody also makes it more natural. 

- **Change BPM, length, and instruments**

    - BPM is the speed of the song. Length is the number of bars. Instruments are the instruments used in the song. 
Maybe music theory and math isn't your thing. You just like hearing sounds made by different objects in different pace. 
"""