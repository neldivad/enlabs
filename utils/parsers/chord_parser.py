import numpy as np
import musicpy as mp

from utils.operators.chord import voice_2_chords, normalize_chord


class ChordParser:

    def __init__(self, chord):
        self.chord = chord.standard_notation()
        self.pitch = None # set global pitch for all notes
        self.verbose = 0

        self.deconstructed_melody = None
        self.deconstructed_bass = None
        self.deconstructed_intervals_chords = None

        self.reconstructed_bass = None
        self.reconstructed_intervals_chords = None
        self.reconstructed_melody = None


    #-----------
    # data structure methods
    #-----------

    
    def is_drum(self):
        """Check if the chord is from a drum channel (channel 10)."""
        if len(self.chord.notes) > 0:
            return self.chord.notes[0].channel == 9
        return False
    

    def set_channel(self, channel:int):
        """Set the channel of the chord."""
        for note in self.chord.notes:
            note.channel = channel

    
    def split_melody(self): 
        """ 
        Wrapper for mp.alg.split_melody()
        """
        return mp.alg.split_melody(self.chord)


    def split_chord(self): 
        """ 
        Wrapper for mp.alg.split_chord()
        """
        return mp.alg.split_chord(self.chord)
    

    def to_piece(self, leading_rests=False):
        """
        Converts the chord object to a piece object.

        Example:
            c = mp.chord('C4, E4, G4, B4')
            ChordParser(c).to_piece()

        Returns:
            piece(notes=[C4, E4, G4, B4], start_time=0)
        """
        total_bars = self.chord.bars()
        remainder = total_bars % 1 

        if leading_rests == True:
            if remainder == 0:
                print('No leading rests needed. Total bars is a whole number.')
            else:
                piece = mp.piece(tracks=[self.chord], start_times=[remainder])
        else:
            piece = mp.piece(tracks=[self.chord])
        return piece
    

    def to_dict(self, note_as_string=False, round_interval:int=16):
        """
        Converts the chord object to a list of dictionaries with notes and intervals.

        Example:
        c = mp.chord('C4, E4, G4, B4') % (1/8, 1/8)
        ChordParser(c).to_dict()

        Returns:
            [{'notes': ['C4'], 'interval': 0.125},
             {'notes': ['E4'], 'interval': 0.125},
             {'notes': ['G4'], 'interval': 0.125},
             {'notes': ['B4'], 'interval': 0.125}]
        """
        chord_data = []
        current_notes = []
        for note, interval in zip(self.chord.notes, self.chord.interval):
            note_str = f"{note.name}{note.num}"
            # current_notes.append(note_str)
            
            note_degree = note.degree
            current_notes.append((note_str, note_degree))  # eg: ('C4', 60)
            
            if interval > 0:
                # Round the interval to the nearest 1/16
                rounded_interval = round(interval * round_interval) / round_interval

                # Sort current_notes by degree before appending
                sorted_notes = sorted(current_notes, key=lambda x: x[1])   
                chord_data.append({
                    'notes': [note_str for note_str, _ in sorted_notes] if not note_as_string else ','.join(note_str for note_str, _ in sorted_notes),
                    'interval': rounded_interval
                })
                current_notes = []  # Reset current notes

        return chord_data
    

    def to_md(self):
        """
        Converts the chord object to a markdown string.

        Example:
            c = chord(notes=[C#3, C2, C2, D2, A#2, A#2, C2, C2, D2, A#2], interval=[0, 1/4, 1/8, 0, 1/4, 0, 1/8, 1/8, 0, 1/8], start_time=0)
            md = ChordParser(c).to_md()

            print(md)
            >>
            C#3,C2[1/4]
            C2[1/8]
            D2,A#2[1/4]
            A#2,C2[1/8]
            C2[1/8]
            D2,A#2[1/8]
        """
        chord_dict = self.to_dict(note_as_string=True)
        md_lines = [
            f"{item['notes']}[{self._format_interval(item['interval'])}]"
            for item in chord_dict
        ]
        return '\n'.join(md_lines)
    

    def _format_interval(self, interval, quantize_limit=64):
        """
        Converts a float interval to a simplified fraction string.
        """
        from fractions import Fraction

        denominators = {1, 2, 3, 4, 6, 8, 16, 32, 64}
        fraction = Fraction(interval).limit_denominator(quantize_limit)

         # If float very small, return 0
        if fraction.numerator == 0:
            return '0'
        return f"{fraction.numerator}/{fraction.denominator}"
    

    #-----------
    # chord syntax methods
    #-----------

    def get_syntax(self, reconcile=False):
        """
        Returns a list of string syntax used to reproduce the chord. 
        No support for high level chord like mp.C('Amin7') ^ 2 for now.

        Example: 
            syntax = get_syntax(chord) 

            chord(notes=[C5, G4, E4, A3, A3, E4, G4, C5, B4, C5, ...], interval=[0, 0, 0, 1/4, 0, 0, 0, 1/4, 1/8, 1/8, ...], start_time=0)
            >> ['C5,G4,E4,A3[1/4;.]', 'A3,E4,G4,C5[1/4;.]', 'B4[1/8;.]', 'C5[1/8;.]',...]

        c = mp.chord('')
        for s in syntax:
            c += mp.chord(s)
        
        assert c == chord
        """
        notes = self.chord.notes # list of note objects
        intervals = self.chord.interval # list of intervals in floats
        syntaxes = [] 
        current_notes = []

        for i, (note, interval) in enumerate(zip(notes, intervals)): 
            note_str = str(note)
            note_degree = note.degree
            formated_interval = self._format_interval(interval) # eg: '0.25 >> 1/4'

            if interval == 0: 
                # current_notes.append(note) # eg: ['C5'] 
                current_notes.append((note_str, note_degree))  # Append as a tuple (note_str, note_degree) Eg: ('C4', 60)

            else: 
                if current_notes: 
                    current_notes.append((note_str, note_degree)) # add last note of chord
                    sorted_notes = sorted(current_notes, key=lambda x: x[1]) # sort current_notes by note degree

                    # Convert sorted notes back to string format
                    chord_syntax = ','.join(note_str for note_str, _ in sorted_notes) + f'[{formated_interval};.]'
                    syntaxes.append(chord_syntax)
                    current_notes = [] # reset current chord

                else:
                    chord_syntax = f'{note_str}[{formated_interval};.]' # eg 'C5[1/4;.]'
                    syntaxes.append(chord_syntax)

        # If we are at the last note, append the current chord
        if i == len(notes) - 1 and current_notes:
            sorted_notes = sorted(current_notes, key=lambda x: x[1])
            chord_syntax = ','.join(note_str for note_str, _ in sorted_notes) + f'[{formated_interval};.]'
            syntaxes.append(chord_syntax)

        # test if syntax reconciles chord
        if reconcile: 
            chord_obj = mp.chord('')
            for syntax in syntaxes:
                chord_obj += mp.chord(syntax)
            
            if chord_obj != self.chord:
                print(f"Error: chord syntax does not reconcile chord object")
            else:
                print(f'Success: chord syntax reconciles chord object')
            
        return syntaxes
    

    def get_generalized_funcs(self, as_string=True):
        """
        For a chord obj, it is possible it is built from multiple chords or notes. 
        This function tries to isolate each chords in track and return a list of simplest syntax to reproduce track. 
        
        TODO: Not able to recover arpeggios or inversions yet. 
        
        as_string: bool
            If True, the function returns a list of string syntax. 
            If False, the function returns a list of partial functions. 

        func_strs: list of string syntax
            EG: 'mp.C(C4, E4, G4, B4)'

        funcs: list of partial functions
            EG: funcs[0]()

        Example: 
            c = mp.C() # a long chord or even the whole track

            ChordParser(c).get_generalized_funcs()
            >> ['mp.C(C4, E4, G4, B4)', 'mp.C(C4, E4, G4, B4)']
        """
        import re
        from functools import partial 

        # get all string syntaxes
        syntaxes = self.get_syntax(reconcile=False) 
        func_strs = [] 
        funcs = []

        for syntax in syntaxes:
            # apply chord detection to each string
            detected_chord = mp.alg.detect(mp.chord(syntax))
            interval = syntax.split('[')[1].split(';')[0] # 'C#5[1/8;.]' >> 1/8

            # syntax is not chord, append as mp.chord()
            if 'note' in detected_chord:
                string = f"mp.chord('{syntax}')"
                partial_func = partial(mp.chord, syntax) # no need interval bc syntax has it
                func_strs.append(string)
                funcs.append(partial_func)

            # syntax is chord, append as mp.C()
            else:
                cname = detected_chord.split(' ')[0] # eg: 'Dmaj7'
                fnote = syntax.split(',')[0] # eg: 'C4' 
                pitch = re.search(r'\d+', fnote).group() # eg: 4

                # edge case: capture the suffix for maj or minor e.g: 'major third'
                try: 
                    suffix = detected_chord.split(' ')[-2]
                    if 'major' in suffix:
                        chord_type = 'M'
                    elif 'minor' in suffix:
                        chord_type = 'm'
                    else:
                        chord_type = '' # No suffix
                except:
                    chord_type = ''

                string = f"mp.C(obj='{cname}{chord_type}', pitch={pitch}, duration={interval})" # eg: "mp.C('Dmaj7', duration=1/8)"
                partial_func = partial(mp.C, obj=f"{cname}{chord_type}", pitch=int(pitch), duration=float(eval(interval)) ) # eg: mp.C('Dmaj7', pitch=3, duration=0.125)
                func_strs.append(string)
                funcs.append(partial_func)

        if as_string:
            return func_strs
        else:
            return funcs
        

    #-----------
    # chord deconstruction methods
    #-----------
    def _adjust_pitch(self, chord_obj):
        highest_degree = max(n.degree for n in chord_obj.notes)
        print(highest_degree)


    def _get_patterns(self, reference_chord, chord_obj, pitch):
        """ 
        Helper function for analyze segment. 
        
        While here we tried to guard for chords containing notes that exceed MIDI range,
        it is still possible for notes to exceed range upon reconstruction. 
        Adjust pitch can only realistically be done from the reconstruction side. 


        reference_chord: mp.chord obj
            Chord from database. EG: mp.C('Cmaj7', pitch=3)
        
        chord_obj: mp.chord obj
            User's chord. EG: mp.chord('C4, E4, G4, B4')
        
        pitch: int
            Pitch of the chord

        Returns: 
            list of floats
            EG: [1.0, 2.0, 3.0, 1.1, 2.1, 3.1, 1.2, 2.2]
        """
        # create pattern based on order of notes. requires detected chord info
        chord_note_names = [n.base_name for n in reference_chord.notes]
        first_note = chord_obj.notes[0]
        pattern = [] 

        for n in chord_obj.notes: 
            note_base = n.base_name

            # if note is in chord, find position of note
            if note_base in chord_note_names: 
                    
                # if note is in chord, find position of note
                note_index = chord_note_names.index(note_base) + 1 

                # some notes match, but belong to different octaves.
                offset_limit = 8 - pitch
                degree_diff = abs(n.degree - first_note.degree) # cannot be negative. first note must be the lowest note
                octave_offset = min(offset_limit, degree_diff // 12)
                octave_offset = octave_offset * 0.1

                # add position+pitch to pattern
                pattern.append(note_index + octave_offset)

            # assume note as root
            else:
                pattern.append(1.0)
        
        return pattern


    def _analyze_segment(self, chord_obj, include_pattern=True):
        """ 
        Helper function for deconstruct bass and intervals chords
        
        """
        notes = [str(n) for n in chord_obj.notes]
        
        new_intervals = []
        intervals = chord_obj.interval
        for interval in intervals: 
            interval = round(interval * 16) / 16
            new_intervals.append(interval)

        # Infer chord
        chord_str = ','.join(notes)
        detected_chord = mp.alg.detect(chord_str, root_preference=True)

        if self.verbose > 0:
            print(f"Detected chord: {detected_chord}")
        
        if '/' in detected_chord:
            chord_candidates = detected_chord.split('/')

            # slash is between 2 bracket chords, eg [Em]/[Cm]
            if any('[' in segment or ']' in segment for segment in chord_candidates):
                print(f"Ambiguous chord detected: {detected_chord}")
                chord_candidates = [segment.replace('[', '').replace(']', '') for segment in chord_candidates]
                chord_candidates = [segment.split()[0] for segment in chord_candidates]

                # Exclude any candidates that are notes
                chord_candidates = [c for c in chord_candidates if not c.lower().startswith('note')]

                # If no valid chord candidates are found, default to the first note if it's the only option
                if not chord_candidates:
                    detected_chord = chord_str.split()[0] if len(chord_str.split()) == 1 else chord_candidates[0]
                else:
                    detected_chord = min(chord_candidates, key=len).strip()
                print(f'Resolved ambiguous chord: {detected_chord}')
        else:
            # this is an inversion EG: Cmin/G
            pass
        
        short_chord = detected_chord.split()[0] # eg: 'Cmaj7'

        # Edge case: capture the suffix for maj or minor e.g., 'F# with major third', Handle ambiguous chords indicated by '/'
        try:
            suffix = detected_chord.split(' ')[-2]
            if 'major' in suffix:
                chord_type = 'M'
            elif 'minor' in suffix:
                chord_type = 'm'
            else:
                chord_type = ''  # No suffix
            short_chord = f"{short_chord}{chord_type}" # eg 'F#m'
        except:
            pass

        if self.pitch == None:
            pitch = chord_obj.notes[0].num # not reliable. Sometimes the first note is not the bass depending on midi file
        else:
            pitch = self.pitch

        # return literal note
        if short_chord == 'note':
            literal_note = f'{detected_chord.split()[1]}' # eg: 'C#1'
            reference_chord = mp.chord(literal_note)
            short_chord = f"{literal_note[:-1]}5(+octave)"
        else:
            reference_chord = mp.C(short_chord, pitch=pitch)

        # Create pattern if required
        pattern = []
        if include_pattern:
            pattern = self._get_patterns(reference_chord,chord_obj, pitch)

        return {
            'chord': short_chord,
            'intervals': new_intervals,
            'pattern': pattern if include_pattern else None,
            'pitch': pitch
        }
    

    def deconstruct_bass(self, sample_rate:float=1.0):
        """
        Tries to reproduce bass lines by retrieving their chords. 

        bass: mp.chord obj 

        sample_rate: float
            Number of bars we aggregate all notes as chord. 

        Returns: 
            list of dict of chord, intervals, pattern, pitch 

        Example:
            bass = mp.C('Bm7', pitch=3)
            deconstructed = deconstruct_bass(bass, sample_rate=1)
            [{
                'chord': 'Gmaj7', 
                'intervals': [0.25, 0.125, 0.125, 0, 0.125, 0.125, 0.125, 0.25], 
                'pattern': [1.0, 1.1, 1.0, 3.0, 3.0, 4.0, 1.0, 1.1], 
                'pitch': 1
            }]
        """        
        track = self.chord.copy()
        num_bars = int(track.bars()) 
        deconstructed = [] 

        for i in np.arange(0.0, float(num_bars)+1, sample_rate):  # +1 to make sure we get last bar 
            start = i
            end = i + sample_rate 
            sampled_chord = track.cut(ind1=start, ind2=end)

            if not sampled_chord.notes:  # Skip if the chord is empty
                continue

            try:
                segment = self._analyze_segment(sampled_chord, include_pattern=True)
                segment['start'] = start
                segment['end'] = end
                deconstructed.append(segment)
            except Exception as e: 
                continue

        self.deconstructed_bass = deconstructed
        self.deconstructed_melody = deconstructed
        return
    

    



    #-----------
    # reconstruction methods
    #-----------
    def _standardize_pitch(self, chord_obj):
        """
        Sets all pitch for note in chord to 4 
        """
        temp = chord_obj.copy()
        for note in temp.notes:
            note.num = 4
        return temp
        

    def _adjust_pitch(self, chord_obj):
        """
        Adjust the pitch of the chord object so that the highest note's degree is <= 127.
        If the chord range is outside the MIDI note range (0-127), normalize all notes to a pitch of 4.
        """
        highest_degree = max(n.degree for n in chord_obj.notes)
        lowest_degree = min(n.degree for n in chord_obj.notes)
        
        # Adjust if highest note exceeds 127 - 24
        while highest_degree > 103:
            chord_obj = chord_obj - 12  # Lower all notes by one octave
            highest_degree = max(n.degree for n in chord_obj.notes)
            lowest_degree = min(n.degree for n in chord_obj.notes)

        # Normalize if the note range is invalid
        if highest_degree > 127 and lowest_degree < 0: 
            print(f"Adjusting pitch for chord {chord_obj}")
            chord_obj = self._standardize_pitch(chord_obj)

        return chord_obj

    
    def reconstruct_bass(self):        
        reconstructed = []
        for info in self.deconstructed_bass:
            chord = info.get('chord', None)
            intervals = info.get('intervals', None)
            pattern = info.get('pattern', None)
            pitch = info.get('pitch', None)

            if pattern == None:
                print(f"Pattern is None for chord {chord}. You should try 'reconstruct_intervals_chords()' instead.")
                return 
            
            try:
                chord_obj = mp.C(obj=chord, pitch=pitch) @ pattern % (intervals, intervals)
                reconstructed.append(chord_obj) 
            
            except Exception as e:
                # fail case is usually bc chord is a note name instead of chord name
                chord_obj = mp.chord(chord) @ pattern % (intervals, intervals)
                reconstructed.append(chord_obj)

        bassline = mp.chord('')
        for chd in reconstructed:
            bassline += chd

        bassline = self._adjust_pitch(bassline)
        self.reconstructed_bass = bassline
        return self.reconstructed_bass


    def reconstruct_all(self):
        self.reconstruct_bass()








