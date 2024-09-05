import streamlit as st 
from streamlit import session_state as state
import pandas as pd
import json
import musicpy as mp

from utils.app_utils.df_utils import df_to_grid
from utils.app_utils.midi_audio import play_audio, export_to_midi_as_bytes, download_midi_no_refresh
from utils.plotting import plot_chords
from utils.constants import RHYTHM_VARIANTS, PATTERN_VARIANTS
from utils.generators.rhythm_generator import generate_rhythm_for_chord
from utils.generators.chord_enhancer import ChordEnhancer




STANDARD_NOTES = list(mp.database.standard2.keys())
CHORD_TYPES = list(mp.database.chord_function_dict.keys())



def main():
    state['r_select_chord'] = state.get('r_select_chord', {})
    state['r_select_rhythm'] = state.get('r_select_rhythm', {})
    state['enhanced_chord_dict'] = state.get('enhanced_chord_dict', {})
    state['chord_enhancer_settings'] = state.get('chord_enhancer_settings', {})
    state['generated_enhanced_chord'] = state.get('generated_enhanced_chord', {})

    st.title('Rhythm Generator')
    with st.sidebar:
        with st.expander('Show cache'):
            st.write(state['r_select_chord'])
            st.write(state['r_select_rhythm'])
            st.write(state['enhanced_chord_dict'])

    t1, t2 = st.tabs(['Basic Rhythm', 'Advanced Rhythm'])

    with t1:
        with st.expander('Select the chord or note', expanded=True):
            chord_form_part()

        if state['r_select_chord'] != {}:
            with st.expander('Rhythm for the chord', expanded=True):
                rhythm_chord_part()

            with st.expander('JSON data for rhythm chord', expanded=False):
                json_data = state['r_select_chord']
                st.text_area(label='JSON', value=json.dumps(json_data, indent=4))

    with t2:
        advanced_rhythm_part()


#------
# tab 1
#------
def chord_form_part():
    rhythm_name_map = {rhythm['name']: rhythm for rhythm in RHYTHM_VARIANTS} # {'name': 'quarter', 'rhythm': 'b b b b', 'bars': 1} >> {'quarter': {'name': 'quarter', 'rhythm': 'b b b b', 'bars': 1}}

    selected_ts = st.selectbox('Select Time Signature', options=[None, '3/4', '4/4'], index=0, help='Warning: Changing time signature may cause errors. Currently only supports 4/4')

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

        if selected_ts in ['None', None, '', 0]:
            state['r_select_chord']['time_signature'] = rhythm_name_map[selected_rhythm]['time_signature']
        else:
            state['r_select_chord']['time_signature'] = selected_ts

        state['r_select_chord']['key'] = selected_key
        state['r_select_chord']['chord'] = selected_chord
        state['r_select_chord']['inversion'] = selected_inversion
        state['r_select_chord']['rhythm_name'] = selected_rhythm
        state['r_select_chord']['rhythm'] = rhythm_name_map[selected_rhythm]['rhythm']
        state['r_select_chord']['accented'] = selected_accent
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
        audio = play_audio(chd*4)
        if audio is not None:
            st.audio(audio)
        
        # Generate MIDI bytes
        midi_fname = f'untitled.mid'
        midi_bytes = export_to_midi_as_bytes(chd)
        download_midi_no_refresh(midi_fname, midi_bytes)


    fig = plot_chords(chd, end_time=None, height=300)
    st.plotly_chart(fig, use_container_width=True)






#-----
# tab 2
#-----
@st.experimental_fragment
def adv_part_contents_and_settings():
    t1, t2 = st.tabs(['Chord Content', 'Selected settings'])
    with t1:
        if state['enhanced_chord_dict'] == {}:
            st.write('No chords added yet.')
            load_preset = st.button('Load preset chords')
            if load_preset:
                ce = ChordEnhancer()
                ce.load_preset_chords()
                state['enhanced_chord_dict'] = ce.to_dict()
                st.rerun()

        if state['enhanced_chord_dict'] != {}:
            df = pd.DataFrame(state['enhanced_chord_dict'])
            grid = df_to_grid(df)
            c1, c2 = st.columns([1,1])
            with c1:
                delete_selected = st.button('Delete selected', key='chord_delete_selected')
            with c2:    
                clear_all = st.button('Clear all', key='chord_clear_all')

            if delete_selected:
                selected_rows = grid['selected_rows'] # nested dict
                for idx, row_data in selected_rows.iterrows():
                    state['enhanced_chord_dict'].pop(int(idx))
                st.rerun()

            if clear_all:
                state['enhanced_chord_dict'] = {}
                st.rerun()

    with t2:
        if state['chord_enhancer_settings'] != {}:
            st.write(state['chord_enhancer_settings'])


def advanced_rhythm_part():
    rhythm_name_map = {rhythm['name']: rhythm for rhythm in RHYTHM_VARIANTS}
    pattern_name_map = {p['name']: p for p in PATTERN_VARIANTS}

    # Prepare a mapping from display name to index
    chord_display_names = [f"{i}: {chord['chord_name']}" for i, chord in enumerate(state['enhanced_chord_dict'])]
    display_to_index = {name: i for i, name in enumerate(chord_display_names)}


    with st.expander('Show chord content and selected settings', expanded=True):
        adv_part_contents_and_settings()

            
    with st.expander('Add chords', expanded=True):
        with st.form('Add Chord'):
            c1, c2 = st.columns([1,1])
            with c1:
                key = st.selectbox('Select Key', STANDARD_NOTES)
            with c2:
                chord_name = st.selectbox('Select Chord', options=CHORD_TYPES)

            if st.form_submit_button('Add Chord'):
                short_name = f"{key}{chord_name}"
                state['enhanced_chord_dict'].append({
                    'chord_name': short_name,
                })
                st.success(f'Added chord {short_name} to index {len(state["enhanced_chord_dict"])-1}')
    
    with st.expander('Chord settings ', expanded=True):
        st.info('No implementation for custom patterns yet. Please use the presets.')

        selected_cs_chords = st.multiselect('Select chords', options=chord_display_names, key='chord_selected_chords', help='Leave blank to apply to all chords')

        c1, c2 = st.columns([1,1])
        with c1:
            selected_pattern = st.multiselect('Select pattern', options=list(pattern_name_map), key='ce_pattern', help='If any pattern is selected, OVERWRITES RHYTHM')
        with c2:
            selected_round_robin = st.selectbox('Round Robin', options=[True, False], key='ce_round_robin', help='If True, the pattern and interval is applied in round robin fashion. Else, applies P and I to random indices.')

        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            selected_rhythm = st.selectbox('Select rhythm', options=list(rhythm_name_map), index=0, help='If pattern is selected, rhythm WILL HAVE NO EFFECT')
        with c2:
            selected_bars = st.number_input('Select number of bars', min_value=0, max_value=8, value=None, key='ce_bars', help="Tries to fit the rhythm within a range of selected bar. If None, will infer from rhythm")
        with c3:
            selected_accent = st.selectbox('Accented', options=[True, False], key='ce_accent', help="Replaces all rests and sustains with beats and lowers volume.")
        
        
        submit_button = st.button(label='Apply settings for chords')
        if submit_button:
            selected_indices = [display_to_index[display_name] for display_name in selected_cs_chords]
            state['chord_enhancer_settings']['chord_selected_indices'] = selected_indices
            state['chord_enhancer_settings']['chord_pattern'] = selected_pattern
            state['chord_enhancer_settings']['chord_round_robin'] = selected_round_robin
            state['chord_enhancer_settings']['chord_rhythm'] = selected_rhythm
            state['chord_enhancer_settings']['chord_accent'] = selected_accent
            state['chord_enhancer_settings']['chord_bars'] = selected_bars

            if selected_pattern not in [None, []]: 
                st.info('Patterns are selected. Rhythm will be ignored.')


    with st.expander('Bass settings', expanded=True):
        selected_bs_chords = st.multiselect('Select chords', options=chord_display_names, key='bass_selected_chords', help='Leave blank to apply to all chords')
        
        c1, c2= st.columns([1,1,])
        with c1:
            selected_bass_rhythm = st.selectbox('Select rhythm', options=rhythm_name_map, index=0, )
        with c2:
            selected_accent = st.selectbox('Accented', options=[True, False], help="Replaces all rests and sustains with beats and lowers volume.")

        submit_button = st.button(label='Apply settings for bass')
        if submit_button:
            selected_indices = [display_to_index[display_name] for display_name in selected_bs_chords]
            state['chord_enhancer_settings']['bass_selected_indices'] = selected_indices
            state['chord_enhancer_settings']['bass_rhythm'] = selected_bass_rhythm
            state['chord_enhancer_settings']['bass_accent'] = selected_accent


    if state['chord_enhancer_settings'] != {}:
        with st.expander('Generate chord', expanded=True):
        
            button = st.button('Generate chord')
            if button:
                chord_rhythm = state['chord_enhancer_settings'].get('chord_rhythm', None)
                chord_accent = state['chord_enhancer_settings'].get('chord_accent', None)
                chord_bars = state['chord_enhancer_settings'].get('chord_bars', None)
                chord_indices = state['chord_enhancer_settings'].get('chord_selected_indices', None)
                chord_pattern = state['chord_enhancer_settings'].get('chord_pattern', None)
                chord_rr = state['chord_enhancer_settings'].get('chord_round_robin', None)

                bass_rhythm = state['chord_enhancer_settings'].get('bass_rhythm', None)
                bass_accent = state['chord_enhancer_settings'].get('bass_accent', None)
                bass_indices = state['chord_enhancer_settings'].get('bass_selected_indices', None)

                # map settings
                pattern_list = [pattern_name_map[p]['pattern'] for p in chord_pattern]
                interval_list = [pattern_name_map[p]['intervals'] for p in chord_pattern]
                cr_str = rhythm_name_map[chord_rhythm]['rhythm']
                br_str = rhythm_name_map[bass_rhythm]['rhythm']

                ce = ChordEnhancer()
                for dict in state['enhanced_chord_dict']:
                    ce.add_chord(chord=mp.C(dict['chord_name']), chord_name=dict['chord_name']) 

                if chord_pattern in [None, []]:
                    ce.apply_rhythm(rhythm_str=cr_str, accent=chord_accent, bars=chord_bars, indices=chord_indices)
                
                if pattern_list not in [None, []]:
                    ce.apply_patterns(indices=chord_indices, pattern_list=pattern_list, interval_list=interval_list, round_robin=chord_rr)

                if bass_rhythm not in [None, []]:
                    ce.apply_bass(indices=bass_indices, rhythm=br_str, accent=bass_accent, pitch_diff=-2)
                ce.reconcile_length()

                if ce.chord_df.empty:
                    st.error('No chords were generated. Check your settings.')
                    return
                co = mp.chord('')
                for c in ce.chord_df['chord_obj']:
                    co += c
                state['generated_enhanced_chord'] = co


            if state['generated_enhanced_chord'] != {}:
                co = state['generated_enhanced_chord']
                play_button = st.button('Play')
                if play_button:
                    audio = play_audio(co)
                    if audio is not None:
                        st.audio(audio)
                    
                    # Generate MIDI bytes
                    midi_fname = f'untitled.mid'
                    midi_bytes = export_to_midi_as_bytes(co)
                    download_midi_no_refresh(midi_fname, midi_bytes)


    