import streamlit as st
from streamlit import session_state as state
from st_aggrid import GridOptionsBuilder, AgGrid

import io 
import json
import pathlib
import os
import pandas as pd

import musicpy as mp

from utils.app_utils.midi_audio import export_to_midi_as_bytes, play_audio
from utils.parsers.chord_parser import ChordParser
from utils.plotting import plot_chords
from utils.app_utils.df_utils import df_to_grid

STANDARD_NOTES = list(mp.database.standard2.keys())
CHORD_TYPES = list(mp.database.chord_function_dict.keys())

def main(): 
    state['parsed_chord_midi'] = state.get('parsed_chord_midi', {})
    state['parsed_chord_json'] = state.get('parsed_chord_json', {})
    state['chord_parser'] = state.get('chord_parser', {})
    state['chord_data'] = state.get('chord_data', [])

    with st.sidebar:
        if st.button('Clear cache'):
            clear_cache()

        # do not expose content to public
        user_level = state.get('user_level', 1)
        if user_level > 1:
            with st.expander('Show MIDI content', expanded=True):
                st.write(state['parsed_chord_midi'])
                st.write(state['parsed_chord_json'])
                st.write(state['chord_parser'])
                st.write(state['chord_data'])


    t1, t2, t3= st.tabs(['Create MIDI/JSON', 'JSON to MIDI', 'MIDI to JSON'])
    with t1:
        create_midi_json()
    with t2:
        upload_chord_json()
    with t3:
        upload_chord_midi()
        

    st.divider()
        



def upload_chord_midi():
    with st.form('Upload MIDI'):
        uploaded_files = st.file_uploader('Upload MIDI file', type=['mid', 'midi'], accept_multiple_files=True)
        
        if st.form_submit_button('Upload MIDI') and uploaded_files:
            for uploaded_file in uploaded_files:
                uploaded_file.seek(0)
                raw_midi = io.BytesIO(uploaded_file.read())
                mid = mp.read(raw_midi, is_file=True)
                state['parsed_chord_midi'][uploaded_file.name] = mid # piece obj 

    # requires uploaded 
    if state['parsed_chord_midi'] != {}:
        for name, piece in state['parsed_chord_midi'].items():
            chord = piece.tracks[0]  # Assume a single track for simplicity

            # Display MIDI content visually
            with st.expander(f'Show MIDI content for {name}', expanded=True):
                fig = plot_chords(chord, start_time=0.0, end_time=None, title=name, height=300)
                st.plotly_chart(fig, use_container_width=True)

                t1, t2 = st.tabs(['Parse as note', 'Parse as chord'])
                with t1:
                    with st.form(f'Note Parser Parameters for {name}'):
                        if st.form_submit_button('Parse as note'): 
                            cp = ChordParser(chord) 
                            note_dict = cp.to_dict()
                            state['chord_parser'][name] = note_dict 

                with t2:
                    # Form for ChordParser parameters
                    with st.form(f'Chord Parser Parameters for {name}'):
                        sample_rate = st.number_input('Sample Rate', min_value=0.5, max_value=8.0, value=1.0, step=0.5)

                        if st.form_submit_button('Parse as chord'):
                            cp = ChordParser(chord)
                            cp.deconstruct_bass(sample_rate=sample_rate)

                            # store deconsstructed bass in state
                            state['chord_parser'][name] = cp.deconstructed_bass
                            st.success(f"Bass processing complete for {name}!")

        st.divider()
        st.subheader('Download processed content')

        # Once processed, show download options
        for name, deconstructed in state['chord_parser'].items():
            with st.expander(f'Download processed content for {name}', expanded=False):
                # Convert to JSON or MIDI
                json_data = json.dumps(deconstructed, indent=4)

                c1, c2 = st.columns([1,1])
                with c1:
                    play_button = st.button('Play', key=f'play_button_{name}')
                with c2:
                    download_json_no_refresh(f"{name}.json", json_data)

                st.code(json_data)

                if play_button:
                    cname = deconstructed[0].get('chord')

                    if cname:
                        chord = reconstruct_bass(deconstructed)
                        audio = play_audio(chord)
                        if audio is not None:
                            st.audio(audio)
                    
                    else:
                        chord = reconstruct_note_dict(deconstructed)
                        audio = play_audio(chord)
                        if audio is not None:
                            st.audio(audio)









def upload_chord_json():
    with st.form('Upload JSON'):
        uploaded_files = st.file_uploader('Upload JSON file', type=['json'], accept_multiple_files=True)
        
        if st.form_submit_button('Upload JSON') and uploaded_files:
            for uploaded_file in uploaded_files: 
                json_data = json.load(uploaded_file)
                state['parsed_chord_json'][uploaded_file.name] = json_data


    if state['parsed_chord_json'] != {}:
        for name, json_data in state['parsed_chord_json'].items():
            st.info(f"**File**: {name}")

            cname = json_data[0].get('chord')

            # parsed json is a chord json
            if cname:
                chd = mp.chord('')
                for sample in json_data: # json data is actually a list of dicts
                    cname = sample.get('chord', 'Unknown')
                    intervals = sample.get('intervals', [])
                    pattern = sample.get('pattern', [])
                    pitch = sample.get('pitch', 4)
                    
                    try:
                        chd += mp.C(cname, pitch=pitch) @ pattern % (intervals, intervals)
                    except Exception as e:
                        print(f"Error parsing chord: {cname}")

            # parsed json is a note json
            else:
                chd = reconstruct_note_dict(json_data)

            with st.expander(f'Show JSON content for {name}', expanded=True):
                st.write(mp.track(chd))
                st.write(json_data)

            with st.expander(f'Show chord content for {name}', expanded=True):
                fig = plot_chords(chd, start_time=0.0, end_time=None, title=name, height=300)
                st.plotly_chart(fig, use_container_width=True)

                c1, c2 = st.columns([1,1]) 
                with c1:
                    play_button = st.button('Play', key=f'j2m_play_button_{name}')
                with c2:
                    midi_bytes = export_to_midi_as_bytes(chd)
                    download_midi_no_refresh(f"{name}.mid", midi_bytes)

                if play_button:
                    audio = play_audio(chd)
                    if audio is not None:
                        st.audio(audio)

            st.divider()








def create_midi_json():
    with st.expander('Create midi/json form', expanded=True):
        create_chord_form()
    
    with st.expander('Show chord content', expanded=True):
        show_chord_df()

    with st.expander('Free text editor', expanded=False):
        iknowwhatimdoing()






def create_chord_form():
    AVAILABLE_INTERVALS = [[0.125] * 8, [0.25]*4, [0.5]*2, [0.125, 0.25, 0.5, 0.125]]
    AVAILABLE_PATTERNS = [[1, 2, 3, 1.1, 1, 2, 1.1, 2], [1, 2, 3, 2, 1, 2, 3, 1.1], [1, 4, 6, 4, 1, 2, 6, 4], [1, 3, 5, 3, 1, 3, 2.1, 3]]
    with st.form(key='create_chord'):
        c1, c2 = st.columns([1,1])
        with c1:
            start = st.selectbox('Start Time', range(16))
        with c2:
            end = st.selectbox('End Time', range(1, 17))

        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            key = st.selectbox('Key', STANDARD_NOTES, index=4)
        with c2:
            chordname = st.selectbox('Chord Name', CHORD_TYPES, index=3)
        with c3:
            pitch = st.selectbox('Pitch', range(1, 6), index=1)

        c1, c2 = st.columns([1,1])
        with c1:
            intervals = st.text_input('intervals (comma-separated)', value="", placeholder='0.25,0.25,0.25,0.25', help='use floats, no fractions as its text input')
            pattern = st.text_input('Pattern (comma-separated)', value="", placeholder='1.1,2.1,4.1,1.1', help='use floats')
        with c2:
            intervals_select = st.selectbox('Quick intervals', options=AVAILABLE_INTERVALS, index=0, help='Select intervals from list')
            pattern_select = st.selectbox('Quick pattern', options=AVAILABLE_PATTERNS, index=0, help='Select pattern from list')

        submit = st.form_submit_button('Add Chord')

    if submit:
        try:
            if intervals == "":
                intervals_list = intervals_select
            else:
                intervals_list = [float(r) for r in intervals.split(',')]

            if pattern == "":
                pattern_list = pattern_select
            else:
                pattern_list = [float(p) for p in pattern.split(',')]

            # Validate lengths
            if len(intervals_list) != len(pattern_list):
                st.error('intervals and Pattern lengths must be equal.')
                return
            
            if sum(intervals_list) != (end-start):
                st.warning('intervals sum is not equal to end minus start, the next chord added will be shifted.')
            
            if start > end:
                st.warning('Start time must be less than end time.')
            

            # Validate unique start and end times
            for chord in st.session_state['chord_data']:
                if chord['start'] == start:
                    st.warning('Start time should be unique.')
                if chord['end'] == end:
                    st.warning('End time should be unique.')
                    
                
            chord_dict = {
                "chord": f"{key}{chordname}",
                "intervals": intervals_list,
                "pattern": pattern_list,
                "pitch": pitch,
                "start": start,
                "end": end
            }

            chd = reconstruct_bass([chord_dict])
            if chd is None:
                st.error(f"Pattern contains note outside chord range.")
                return
                
            # Append data to session state
            st.session_state['chord_data'].append(chord_dict)
            st.success('Chord added successfully.')
            
            # auto increase form
            start += 1
            end += 1

        except ValueError:
            st.error('Invalid input. Please ensure intervals and pattern are valid numbers.')



def iknowwhatimdoing():
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
            
            #  if parsed json is a note json
            else:
                chd = reconstruct_note_dict(json_data)

        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_text = ''
            return

        state['chord_data'] = json_data
        st.success('JSON parsed successfully.')
        st.rerun()




def show_chord_df():
    if state['chord_data'] == []:
        return
    
    dict_list = state['chord_data']
    cname = dict_list[0].get('chord')
    if cname:
        chord = reconstruct_bass(dict_list)
    else:
        chord = reconstruct_note_dict(dict_list)

    t1, t2 = st.tabs(['Play', 'Download'])
    with t1:
        select_bpm = st.slider('Select BPM', min_value=60, max_value=300, value=120, step=1, help='Warning: BPM does not affect audio playback for cloud')
        play_button = st.button('Play', key='play_button_show_chord')

    with t2:
        dict_list_display = st.text_area('Copy JSON content', value=json.dumps(dict_list, indent=4), height=200)
        c1, c2 = st.columns([1,1])
        with c1:
            download_json_no_refresh(f"untitled.json", json.dumps(dict_list, indent=4))
        with c2:
            midi_bytes = export_to_midi_as_bytes(chord)
            download_midi_no_refresh(f"untitled.mid", midi_bytes)



    if play_button:
        audio = play_audio(chord, bpm=select_bpm)
        if audio is not None:
            st.audio(audio)


    st.divider()
    st.info(f"Saved chords: {len(state['chord_data'])}")
    df = pd.DataFrame(dict_list)
    grid = df_to_grid(df)

    c1, c2 = st.columns([1,1])
    with c1:
        delete_selected = st.button('Delete selected', key='chord_delete_selected')
    with c2:    
        clear_all = st.button('Clear all', key='chord_clear_all')

    if delete_selected:
        selected_rows = grid['selected_rows'] # nested dict
        for idx, row_data in selected_rows.iterrows():
            state['chord_data'].pop(int(idx))
        st.rerun()

    if clear_all:
        state['chord_data'] = []
        st.rerun()























def clear_cache():
    state['parsed_chord_midi'] = {}
    state['parsed_chord_json'] = {}
    state['chord_parser'] = {}
    state['chord_data'] = []




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


@st.experimental_fragment
def download_json_no_refresh(fname, bytes):
    """ 
    st.download_button() refreshes the page. The workaround is to wrap it in a fragment. 
    It is possible for the first download to fail.
    """
    st.download_button(
        label='Download JSON', 
        data=bytes,
        file_name=fname, 
        mime='application/json'
    )






def apply_legato(chord):
    total_duration = sum(chord.interval)  # Total duration of the chord progression
    
    for i, note in enumerate(chord.notes):
        if i < len(chord.notes) - 1:
            # Check the duration till the next non-zero interval
            j = i + 1
            while j < len(chord.notes) and chord.interval[j] == 0:
                j += 1
            if j < len(chord.notes):
                # Extend the duration up to the start of the next note
                note.duration = sum(chord.interval[i:j+1])
            else:
                # Extend to the end of the progression for the last note with zero interval
                note.duration = total_duration - sum(chord.interval[:i])
        else:
            # Last note: ensure it spans to the end of the progression
            note.duration = total_duration - sum(chord.interval[:i])

    return chord




def reconstruct_note_dict(note_dict):
    chd  = mp.chord('')
    for dct in note_dict:
        notes = dct.get('notes', 'Unknown')
        note_str = ','.join(notes)
        interval = dct.get('interval', 0) 
        chd += mp.chord(note_str, duration=interval) # implicitly already has legato
    
    return chd


def reconstruct_bass(deconstructed_bass):
    try:
        chd = mp.chord('')
        for c in deconstructed_bass:
            cname = c.get('chord', 'Unknown')
            pitch = c.get('pitch', 4)
            intervals = c.get('intervals', [])
            pattern = c.get('pattern', [])
            try:
                chd += mp.C(cname, pitch=pitch) @ pattern % (intervals, intervals)
            except Exception as e:
                chd += mp.chord(cname) @ pattern % (intervals, intervals)
                
        chd = apply_legato(chd)
        return chd
    
    except Exception as e:
        print(f"Error {e}. Pattern contains note outside chord range.")
        st.error(f"Error {e}. Pattern contains note outside chord range.")
        return
    





example_json = """
[
    {
        "chord": "Fmaj7",
        "intervals": [
            0.125,
            0.125,
            0.125,
            0.25,
            0.25,
            0.375
        ],
        "pattern": [
            1.0,
            3.0,
            4.0,
            1.1,
            4.0,
            3.0
        ],
        "pitch": 2,
        "start": 0.0,
        "end": 1.0
    },
    {
        "chord": "FM",
        "intervals": [
            0.125,
            0.625
        ],
        "pattern": [
            1.0,
            1.0
        ],
        "pitch": 3,
        "start": 1.0,
        "end": 2.0
    },
    {
        "chord": "Gmajor",
        "intervals": [
            0.125,
            0.125,
            0.125,
            0.25,
            0.125,
            0.25
        ],
        "pattern": [
            1.0,
            3.0,
            1.1,
            2.1,
            1.1,
            1.0
        ],
        "pitch": 2,
        "start": 2.0,
        "end": 3.0
    },
    {
        "chord": "Gmajor",
        "intervals": [
            0,
            0,
            0,
            0.125,
            0.125,
            0.125,
            0.25,
            0.125,
            0.25
        ],
        "pattern": [
            1.0,
            3.0,
            1.1,
            2.1,
            3.0,
            1.1,
            2.1,
            1.1,
            1.0
        ],
        "pitch": 2,
        "start": 3.0,
        "end": 4.0
    },
    {
        "chord": "Em11",
        "intervals": [
            0.125,
            0.125,
            0.125,
            0.625
        ],
        "pattern": [
            1.0,
            4.0,
            2.1,
            6.1
        ],
        "pitch": 2,
        "start": 4.0,
        "end": 5.0
    },
    {
        "chord": "Gmajor",
        "intervals": [
            0,
            0,
            1
        ],
        "pattern": [
            1.0,
            2.0,
            3.0
        ],
        "pitch": 3,
        "start": 5.0,
        "end": 6.0
    },
    {
        "chord": "Am7",
        "intervals": [
            0.125,
            0.125,
            0.125,
            0.25,
            0.125,
            0.25
        ],
        "pattern": [
            1.0,
            3.0,
            4.0,
            2.1,
            4.0,
            3.0
        ],
        "pitch": 2,
        "start": 6.0,
        "end": 7.0
    },
    {
        "chord": "Am11",
        "intervals": [
            0,
            0,
            0,
            0.5,
            0,
            0,
            0,
            0.5
        ],
        "pattern": [
            1.0,
            2.1,
            3.0,
            4.0,
            4.0,
            6.0,
            4.0,
            5.1
        ],
        "pitch": 2,
        "start": 7.0,
        "end": 8.0
    },
    {
        "chord": "Fmaj7",
        "intervals": [
            0.125,
            0.125,
            0.125,
            0.25,
            0.125,
            0.25
        ],
        "pattern": [
            1.0,
            4.0,
            1.1,
            3.1,
            1.1,
            4.0
        ],
        "pitch": 2,
        "start": 8.0,
        "end": 9.0
    },
    {
        "chord": "Fmaj7",
        "intervals": [
            0.25,
            0.125,
            0.25,
            0.125,
            0.125,
            0.125
        ],
        "pattern": [
            1.0,
            4.0,
            3.0,
            1.0,
            4.0,
            1.1
        ],
        "pitch": 3,
        "start": 9.0,
        "end": 10.0
    },
    {
        "chord": "Gmajor",
        "intervals": [
            0.125,
            0.125,
            0.125,
            0.25,
            0.125,
            0.25
        ],
        "pattern": [
            1.0,
            3.0,
            1.1,
            2.1,
            1.1,
            3.0
        ],
        "pitch": 2,
        "start": 10.0,
        "end": 11.0
    },
    {
        "chord": "Cmaj9sus4",
        "intervals": [
            0,
            0,
            0,
            0.25,
            0.125,
            0,
            0.25,
            0.25,
            0.125
        ],
        "pattern": [
            3.0,
            5.0,
            3.1,
            1.1,
            5.0,
            3.1,
            4.1,
            5.0,
            2.0
        ],
        "pitch": 2,
        "start": 11.0,
        "end": 12.0
    },
    {
        "chord": "Em11",
        "intervals": [
            0.125,
            0.125,
            0.125,
            0.625
        ],
        "pattern": [
            1.0,
            4.0,
            2.1,
            6.1
        ],
        "pitch": 2,
        "start": 12.0,
        "end": 13.0
    },
    {
        "chord": "E9",
        "intervals": [
            0,
            0,
            0.25,
            0.125,
            0.25,
            0.125,
            0.125,
            0.125
        ],
        "pattern": [
            1.0,
            2.0,
            3.0,
            4.0,
            4.0,
            3.0,
            2.0,
            1.0
        ],
        "pitch": 3,
        "start": 13.0,
        "end": 14.0
    },
    {
        "chord": "Am11",
        "intervals": [
            0.125,
            0.125,
            0.125,
            0.25,
            0.125,
            0.25
        ],
        "pattern": [
            1.0,
            3.0,
            4.0,
            2.1,
            6.1,
            4.0
        ],
        "pitch": 2,
        "start": 14.0,
        "end": 15.0
    },
    {
        "chord": "Am7",
        "intervals": [
            0,
            0,
            0.5,
            0,
            0,
            0.5
        ],
        "pattern": [
            1.0,
            3.0,
            4.0,
            4.0,
            3.0,
            4.0
        ],
        "pitch": 2,
        "start": 15.0,
        "end": 16.0
    }
]
"""