import musicpy as mp 
import pandas as pd
from copy import deepcopy
import random


from utils.operators.chord import accenting_rhythm_chord
from utils.constants import PATTERN_VARIANTS
from utils.operators.chord import clamp_chord_pattern, detect_chord_name, lengthen_note_duration_in_chord



class ChordEnhancer:
    def __init__(self):
        self.time_signature = [4,4]
        self.chord_df = pd.DataFrame(columns=['chord_obj', 'chord_name', 'start', 'end', 'intervals', 'pattern'])
        pass 

    def __get_basic_row_info(self, row):
        chord = deepcopy(row['chord_obj'])
        chord_name = row['chord_name']
        start = row['start']
        end = row['end']
        bars = end - start
        return chord, chord_name, start, end, bars
    
    def to_dict(self):
        df_copy = self.chord_df.copy()
        df_copy.drop(columns=['chord_obj'], inplace=True)
        return df_copy.to_dict(orient='records')

    def show(self):
        print(self.to_dict())


    def set_time_signature(self, time_signature:list=[4,4]):
        self.time_signature = time_signature

    
    def load_preset_chords(self):
        self.chord_df = pd.DataFrame(columns=['chord_obj', 'chord_name', 'start', 'end', 'intervals', 'pattern'])
        cnames = ['Fmaj7', 'G7, b9, omit 5', 'Am7', 'D7', 'FmM7', 'G7,#5', 'Cmaj7', 'Bdim7']
        chords = [
            mp.C('Fmaj7',3),
            mp.C('G7, b9, omit 5',3), 
            mp.C('Am7', 3), 
            mp.C('D7', 3) ^ 2, 
            mp.C('FmM7', 3) ^ 2, 
            mp.C('G7,#5', 3), 
            mp.C('Cmaj7',4), 
            mp.C('Bdim7',3), 
        ]
        for i, chord in enumerate(chords):
            self.add_chord(chord, chord_name=cnames[i])


    def add_chord(self, chord:mp.chord, chord_name:str=None, start:int=None, end:int=None, intervals:list=None, pattern:list=None):
        """ 
        Adds a chord to the chord_df. Using df because it is easier to search and filter and apply functions
        """
        if chord_name == None:
            chord_name = detect_chord_name(chord)

        latest_end = self.chord_df.iloc[-1]['end'] if len(self.chord_df) > 0 else 0
        cdict = {
            "chord_name": chord_name,
            "chord_obj": chord,
            "start": latest_end if start == None else start,
            "end": latest_end + 1 if end == None else end,
        }
        self.chord_df.loc[len(self.chord_df)] = cdict


    def apply_rhythm(
        self, 
        rhythm_str:str=None, 
        bars:int=None,
        indices:list=None, 
        accent:bool=False, 
        high_volume:int=100, 
        low_volume:int=80
    ):
        """
        OVERWRITES apply_patterns()

        Applies rhythm to all chords in the chord_df or selected indices. 

        rhythm_str: str
            Rhythm string in the form of 'b b b b b b b b'

        indices: list
            List of indices to apply rhythm to. If None, applies to all chords.

        accent: bool
            If True, replaces all rests and sustains with beats and lowers volume.

        high_volume: int
            Volume of the high beats.

        low_volume: int
            Volume of the low beats.
        """
        # apply rhythm to all records if None
        if indices in [None, []]:
            indices = range(len(self.chord_df))

        for i, row in self.chord_df.iterrows():
            if i in indices:
                chord, chord_name, start, end, default_bars = self.__get_basic_row_info(row)
                if bars == None:
                    bars = default_bars
            
                if accent == True:
                    chord = accenting_rhythm_chord(chord, rhythm_str, bars, high_volume, low_volume)
                else:
                    rhythm = mp.rhythm(rhythm_str, bars)
                    chord = chord.from_rhythm(rhythm)
                self.chord_df.at[i, 'chord_obj'] = chord

    
    def apply_patterns(
        self, 
        indices:list=None, 
        pattern_list:list=None, 
        interval_list:list=None, 
        round_robin:bool=True
    ):
        """
        OVERWRITES apply_rhythm() 

        Applies pattern to all chords in the chord_df or selected indices. 
        
        indices: list
            List of indices to apply pattern to. If None, applies to all chords.

        pattern: list
            List of floats representing the pattern. 
            
        intervals: list
            List of floats representing the intervals between notes. 
            
        round_robin: bool
            If True, the pattern and interval is applied in round robin fashion. Else, applies P and I to random indices. 
        """
        if indices in [None, []]:
            indices = range(len(self.chord_df)) 

        if pattern_list == None or interval_list == None:
            # get all patterns from pattern name map
            pattern_name_map = {p['name']: p for p in PATTERN_VARIANTS} 
            pattern_list = [pattern_name_map[p]['pattern'] for p in pattern_name_map]
            interval_list = [pattern_name_map[p]['intervals'] for p in pattern_name_map]
        
        for i, (pattern, interval) in enumerate(zip(pattern_list, interval_list)):
            if len(pattern) != len(interval):
                raise ValueError(f'Pattern and intervals must have the same length. Error at index {i}')
            
        for i, row in self.chord_df.iterrows():
            if i in indices:
                chord, chord_name, start, end, bars = self.__get_basic_row_info(row)
                
                if round_robin == True:
                    pattern = pattern_list[i % len(pattern_list)]
                    interval = interval_list[i % len(interval_list)]
                else:
                    random_idx = random.randint(0, len(pattern_list)-1)
                    pattern = pattern_list[random_idx]
                    interval = interval_list[random_idx]

                # clamp pattern if it contains notes outside the chord range
                clamped_pattern = clamp_chord_pattern(mp.C(chord_name), pattern)
                new_chord = chord @ clamped_pattern % (interval, interval)
                new_chord = lengthen_note_duration_in_chord(new_chord)
                self.chord_df.at[i, 'chord_obj'] = new_chord
            

    def apply_bass(
        self,
        indices:list=None,
        intervals:list=None,
        pattern:list=None,
        rhythm:str=None,
        accent:bool=False,
        pitch_diff:int=-2,
    ):
        """
        WILL BE OVERWRITTEN if function is called before apply_rhythm() or apply_patterns(). Recommend to do it last.
        """
        if indices in [None, []]:
            indices = range(len(self.chord_df))

        if rhythm == None:
            rhythm = 'b b b b b b b b'

        for i, row in self.chord_df.iterrows():
            if i in indices:
                chord, chord_name, start, end, bars = self.__get_basic_row_info(row)
                root = chord.notes[0]
                bass = mp.chord(f"{root}") 
                bass = bass + (pitch_diff * 12)
                
                # apply accent if required
                if accent == True:
                    bass = accenting_rhythm_chord(bass, rhythm, bars, bounce_low_notes=True)
                else:
                    r = mp.rhythm(rhythm, bars)
                    bass = bass.from_rhythm(r)

                new_chord = chord & bass 
                self.chord_df.at[i, 'chord_obj'] = new_chord

                



    def reconcile_length(self): 
        """ 
        Reconciles the duration of every chord object in chord df according to their respective start and end
        """
        def get_last_notes(chord):
            # Find the index of the last note in the chord
            last_note_index = len(chord.notes)-1

            # Include all preceding notes with zero intervals until the first non-zero interval
            last_notes_indices = []
            for i in range(last_note_index, -1, -1):
                last_notes_indices.append(i)
                if chord.interval[i] > 0:
                    break
            return last_notes_indices

        # go through all records in df
        for i, row in self.chord_df.iterrows():
            chord, chord_name, start, end, bars = self.__get_basic_row_info(row)

            # Get the indices of the last notes
            last_notes_indices = get_last_notes(chord)

            # Set the duration of the last notes to bars
            for idx in last_notes_indices:
                chord.notes[idx].duration = bars

            # Trim the chord by bars
            new_chord = chord.cut(ind1=0, ind2=bars, cut_extra_duration=True, cut_extra_interval=True, round_duration=True, round_cut_interval=True)

            # Update the chord in the DataFrame
            self.chord_df.at[i, 'chord_obj'] = new_chord







        