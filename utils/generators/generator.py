import musicpy as mp
import random
import re
from copy import deepcopy

from utils.constants import RHYTHM_VARIANTS


class PopGenerator:
    """ 
    USAGE: 

    s = mp.scale('C', 'minor')

    pg = PopGenerator(scale=s, bpm=120)
    """
    def __init__(
        self,
        scale: mp.scale=None,
        length:int=10,
        melody_instrument:int=25,
        chord_instrument:int=47,
        bpm:int=120,

        chord_notes_num:list=[4],
        chord_duration:int=1,
        inversion_highest_num:int=2,
        selected_chord_intervals:list=[1/8],
        melody_durations:list=[3/8, 5/8, 1/8, 1/2, 1/4, mp.beat(1/2,1), mp.beat(1/8,1)],

        chord_progression:int=None,
        melody_octave:int=3,
        bass_octave:int=2,
        bass_rhythms:list=[RHYTHM_VARIANTS[0]['rhythm']],
        bass_techniques:list=mp.database.default_choose_bass_playing_techniques,

        harmonize:bool=False,
        num_harmony_notes:int=1,
        variance:float=100,
    ):
        if scale:
            self.scale = scale if not 'minor' in scale.mode else scale.relative_key()
        else:
            self.scale = None

        # basic params
        self.length = length
        self.melody_instrument = melody_instrument
        self.chord_instrument = chord_instrument
        self.bpm = bpm
        self.verbose = 0

        # chord params
        self.chord_progressions = chord_progression
        self.chord_notes_num = chord_notes_num
        self.chord_duration = chord_duration
        self.inversion_highest_num = inversion_highest_num
        self.selected_chord_intervals = selected_chord_intervals

        # melody params
        self.melody_durations = melody_durations         
        self.melody_octave = melody_octave

        # bass params
        self.bass_octave = bass_octave
        self.bass_rhythms = bass_rhythms
        self.bass_techniques = bass_techniques

        # extra params 
        self.harmonize = harmonize
        self.num_harmony_notes = num_harmony_notes
        self.variance = variance

        # generated objects
        self.chords = []
        self.chord_patterns = [] # 
        self.chord_intervals = []
        self.chord_index = 0 
        self.length_count = 0
        self.chords_part = mp.chord([])
        self.melody_part = mp.chord([])
        self.bass_part = mp.chord([])

    def _apply_legato(self, chord:mp.chord, intervals:list):
        chord = chord.copy()
        for i, note in enumerate(chord.notes):
            if intervals[i] == 0:
                # Find the next non-zero interval
                next_non_zero = next((x for x in intervals[i+1:] if x != 0), None)
                if next_non_zero is not None:
                    note.duration = next_non_zero
                else:
                    note.duration = 0  # Fallback if no non-zero interval is found
            else:
                note.duration = intervals[i]
        return chord


    def add_chord(self, chord_name:str, pitch:int=4, pattern:list=[], interval:list=[]):
        """ 
        param: chord: mp.chord

        param: pattern: list of floats representing the pattern 
        
        param: interval: lsit of floats representing the interval between notes

        Example: 
            pg.add_chord(mp.C('Cmaj7'), [1,2,3,1.1], [1/8,1/8,1/8,1/8])
        """
        if len(pattern) != len(interval):
            raise ValueError('Pattern and interval must be the same length')
        
        if self.chord_progressions != None:
            self.chord_progressions = None
            print('Chord progression reset to None after adding custom chords')

        chd = mp.C(chord_name, pitch=pitch) @ pattern % (interval, interval) # setting interval and duration to be equal, but both ARE NOT THE SAME THING! 
        chd = self._apply_legato(chd, interval)

        self.chords.append(chd)
        if self.verbose > 0:
            print(f'Added chord: {chd} at index {len(self.chords)}')
        return 
    

    def infer_scale(self):
        """
        """
        pass 


    def set_chord_progressions(self, progression:int=None):
        """ 
        Choose chord progression where int represents the sequence. Example 1234 >> I ii III IV
        """
        if progression in [None]:
            chord_progression = random.choice(mp.database.choose_chord_progressions_list)
        else:
            chord_progression = progression

        # # will create a sequence of chords at constant intervals
        self.chords = self.scale % (
            chord_progression,  # progression: 12346451
            self.chord_duration, # 1
            0, # interval: 0
            random.choice(self.chord_notes_num) # 4 notes per chord
        )
        self.chord_progressions = chord_progression
        
        print(f"Chord progression: {self.chord_progressions}")

    
    def set_bass_rhythms(self, rhythms:list=[mp.rhythm], patterns:list=[], sample_mode:str='random'):
        available_modes = ['random', 'roundrobin']
        if sample_mode not in available_modes:
            raise ValueError(f'Sample mode {sample_mode} not in {available_modes}')
        
        if rhythms == []:
            base_rhythm = RHYTHM_VARIANTS[0]['rhythm']
            rhythms = [base_rhythm]
        
        self.bass_rhythms = rhythms
        self.bass_patterns = patterns
        self.bass_sample_mode = sample_mode

        print(f"Bass rhythms: {self.bass_rhythms}")
        print(f"Bass patterns: {self.bass_patterns}")
        print(f"Bass sample mode: {self.bass_sample_mode}")


    def replace_5th_chords(self):
        """
        Get all dominant chord in scale, then replace notes with triad + octave instead of 7th.
        No idea why you want to do this
        """
        for i in range(len(self.chords)):
            chd = self.chords[i]
            if chd[0] == self.scale[4]:
                chd = mp.C(
                    f'{self.scale[4].name}', 
                    chd[0].num,
                    duration=self.chord_duration
                ) @ [1, 2, 3, 1.1] # from 1,2,3,4 to 1,2,3,1.1
                self.chords[i] = chd

                if self.verbose > 0:
                    print(f"Chord {i}: {chd}")

        print(f"All dominant chords replaced with triad + octave")


    def apply_reverse(self, probability=100):
        """
        param: probability: int
            Probability of reversing a chord for each chord in list. Default is 100.
        """
        self.chords = [chord.reverse() if random.randint(0, 100) < probability else chord for chord in self.chords]
        print(f"Chords reversed")

    
    def apply_omission(self, omit:list=None):
        """ 
        Applies omission to all chords in the list. Will turn a 4/4 chord into a 3/4 chord if self.n_notes is 4 and omit list length is 1. 
        To change this behavior, simply set self.n_notes to a bigger chord and you can omit more of it.
        """
        if omit is not None:
            self.chords = [chord.omit(omit) for chord in self.chords]
        print(f"Chord omission: {omit}")

    
    def apply_inversion(self, inversion:int=None, probability=100):
        """ 
        Applies inversion to all chords in the list.
        """
        if inversion is not None:
            self.chords = [i ^ inversion if random.randint(0, 100) < probability else i for i in self.chords]
            self.inversion_highest_num = inversion
        print(f"Chord inversion: {self.inversion_highest_num}")


    def generate_chord_and_melody(self, non_chord_prob:float=30):
        """ 
        Basic working function. Very unsophisticated.

        Generates the arp pattern based on chords and rhythm.
        Melody and bass must be generated simulatenously with the chords.
        """
        from copy import deepcopy

        length_count = 0
        chord_index = 0
        chords_part = mp.chord([])
        melody_part = mp.chord([])
        bass_part = mp.chord([])
        melody_octave = self.melody_octave

        # fill length with chords
        while length_count < self.length:
            current_chord = self.chords[chord_index]

            if self.verbose > 0:
                print(f"Current scale index: {chord_index}")
                print(f"Current chord: {current_chord}")

            current_chord_interval = random.choice(self.selected_chord_intervals)
            if isinstance(current_chord_interval, mp.beat):
                current_chord_interval = current_chord_interval.get_duration()
            
            current_chord = current_chord.set(interval=current_chord_interval)
            chords_part += current_chord
            length_count = chords_part.bars(mode=0)

            # generate bass part 
            progression_index = str(self.chord_progressions)[chord_index]
            current_chord_tonic = mp.note(
                self.scale[ int(progression_index)- 1].name, 
                self.bass_octave
            )
            if self.bass_rhythms is None:
                current_bass_part = mp.chord([current_chord_tonic]) % (length_count, length_count)
            else:
                current_bass_part = mp.get_chords_from_rhythm(
                    mp.chord([current_chord_tonic]),
                    mp.rhythm(self.bass_rhythms[0], 1),
                )
                if len(current_bass_part) > 1:
                    for i in range(len(current_bass_part)):
                        if i % 2 != 0:
                            current_bass_part[i] += 12
            bass_part += current_bass_part

            # generate melody concurrently with chords
            while melody_part.bars(mode=0) < chords_part.bars(mode=0):
                passing_note = random.randint(0, 100)

                # 30% chance of using a non-chord note
                if passing_note < non_chord_prob:
                    non_chord_notes = [note for note in self.scale.notes if note not in current_chord.notes]
                    current_melody = random.choice(non_chord_notes) # get a random note from the scale
                else:
                    current_melody = random.choice(current_chord.notes) # get a random note from the chords

                current_chord_duration = random.choice(self.melody_durations)
                if isinstance(current_chord_duration, mp.beat):
                    current_chord_duration = current_chord_duration.get_duration()
                current_melody.duration = current_chord_duration

                current_melody.num = melody_octave
                melody_part.notes.append(current_melody)
                melody_part.interval.append( deepcopy(current_melody.duration) )
        
            # keep moving up the chord progression
            chord_index += 1
            if chord_index >= len(self.chords):
                chord_index = 0

        chords_part.set_volume(70)
        bass_part.set_volume(60)

        self.chords_part = chords_part
        self.melody_part = melody_part
        self.bass_part = bass_part

        piece = mp.piece(
            tracks=[melody_part, chords_part, bass_part],
            instruments=[self.melody_instrument, self.chord_instrument, 38],
            bpm=self.bpm,
            start_times=[0, 0, 0],
            track_names=['melody', 'chords', 'bass'],
            channels=[0, 1, 2]
        )
        return piece
    

    def generate_chord(self):
        """
        Generates a chord for the current chord progression.
        """
        current_chord = deepcopy(self.chords[self.chord_index]) 
        if self.chord_progressions == None:
            return current_chord 
        
        current_chord_interval = random.choice(self.selected_chord_intervals)
        if current_chord_interval != 0:
            current_chord = current_chord.set(interval=current_chord_interval)
        return current_chord 
    
    
    def generate_bass(self):
        """
        Generates a bass line for the current chord progression.
        """
        current_chord = deepcopy(self.chords[self.chord_index])
        chord_duration = current_chord.bars(mode=0) # sum of intervals

        if self.chord_progressions != None:
            # Use the root note of the scale based on the chord progression
            progression_index = str(self.chord_progressions)[self.chord_index]
            current_chord_tonic = mp.note(
                self.scale[ int(progression_index)- 1].name, 
                self.bass_octave
            )
            chord_duration = current_chord.bars(mode=1) # FK the bars() method. WTF IS MODE 1 AND 0 and why do they always cause bugs?! 
        else:
            # Use the root note of the custom chord. Naively assume the first note must be the root
            current_chord_tonic = current_chord.notes[0]
            current_chord_tonic.num = self.bass_octave    

        # Calculate the number of notes needed based on the chord duration
        bass_rhythm = self.bass_rhythms[0] # 'b b b b'
        br_list = bass_rhythm.split() # ['b', 'b', 'b', 'b']
        note_count = int(chord_duration / (1/8))

        # Truncate or extend the rhythm string if chord duration is less/more than rhythm string (1 by default)
        if chord_duration < len(br_list) * (1/8):
            adjusted_rhythm = ' '.join(br_list[:note_count])
        else:
            multiplier = note_count // len(br_list)
            remainder = note_count % len(br_list)
            adjusted_rhythm = (' '.join(br_list) + ' ') * multiplier + ' '.join(br_list[:remainder])

        # apply rhythm to root
        current_bass_part = mp.get_chords_from_rhythm(
            mp.chord([current_chord_tonic]),
            mp.rhythm(adjusted_rhythm, chord_duration)
        )
        return current_bass_part 
    

    def harmonize_melody(self, melody:mp.note, chord:mp.chord, num_notes:int=1):
        """
        """
        if num_notes < 1 or num_notes > 3:
            raise ValueError('Number of notes must be between 1 and 3') 
        
        harmonized = mp.chord([])
        harmony = [melody] # mp.chord obj
        available_notes = [n for n in chord.notes if n not in harmony]
        extra_notes = min(num_notes, len(available_notes))
        harmony += random.sample(available_notes, extra_notes)
        harmony.sort()

        # set interval to 0 to stack chords. set duration to 0 for now
        for i, note in enumerate(harmony):
            note.interval = 0
            note.duration = 0

        # stack chords
        for note in harmony:
            harmonized &= mp.chord([note])
        return harmonized
    

    def generate_melody(self, probability:float=30, harmonize:bool=False, num_harmony_notes:int=1):
        """ 
        BUG: When exporting to MIDI, possible to have overlapping notes. From FL piano roll, select overlapping notes and delete them.
        """
        # BRUH THE FKING RHYTHM IS CAUSING SO MUCH BUGS
        # bar mode 1 if chord progression is set, bar mode 0 if not
        if self.chord_progressions != None:
            mode = 1
        else:
            mode = 0

        melody_for_chord = mp.chord([])
        current_chord = deepcopy(self.chords[self.chord_index])
        chord_duration = current_chord.bars(mode=mode)
        remainder = chord_duration

        # fill chord with random notes in chord notes and scale notes
        while melody_for_chord.bars(mode=mode) < chord_duration:
            passing_note = random.randint(0, 100)

            if self.chord_progressions == None:
                try:
                    weighted_options = current_chord.notes + self.scale.notes
                    current_melody = random.choice(weighted_options)
                except Exception as e:
                    current_melody = random.choice(current_chord.notes)

            elif passing_note < probability:
                non_chord_notes = [note for note in self.scale.notes if note not in current_chord]
                current_melody = random.choice(non_chord_notes) # get a random note from the scale
            else:
                current_melody = random.choice(current_chord.notes) # get a random note from the chords

            # set duration for the melody note
            current_melody_duration = random.choice(self.melody_durations)
            if isinstance(current_melody_duration, mp.beat):
                current_melody_duration = current_melody_duration.get_duration()
            elif isinstance(current_melody_duration, str): # from app, rest(0.1875)
                float_value = float(re.search(r'\d+\.\d+', current_melody_duration).group()) # remove 'rest(' and ')' from string
                current_melody_duration = float_value

            current_melody_duration = min(current_melody_duration, remainder)
            remainder -= current_melody_duration
            current_melody.duration = current_melody_duration
            current_melody.num = self.melody_octave
            
            if harmonize:
                current_melody = self.harmonize_melody(current_melody, current_chord, num_harmony_notes)
                for note in current_melody.notes:
                    note.duration = current_melody_duration
                melody_for_chord += current_melody
            else:
                melody_for_chord.notes.append(current_melody)
                melody_for_chord.interval.append( deepcopy(current_melody.duration) )


        return melody_for_chord    


    def generate_all(self, generate_bass=True, generate_melody=True, generate_chords=True):
        """ 
        Simulataneously generate all parts by cycling chord progressions. 
        """
        length_count = 0
        self.chord_index = 0

        while length_count < self.length:
            if self.verbose > 0:
                print(f"{self.chord_progressions}[{self.chord_index}]")

            # generate chord regardless
            chd = self.generate_chord()
            length_count += chd.bars(mode=0)

            if generate_chords == True:
                self.chords_part += chd
            if generate_bass == True:
                bass = self.generate_bass()
                self.bass_part += bass
            if generate_melody == True:
                melody = self.generate_melody(probability=self.variance, harmonize=self.harmonize, num_harmony_notes=self.num_harmony_notes)
                self.melody_part += melody

            self.chord_index += 1
            if self.chord_index >= len(self.chords):
                self.chord_index = 0

        t1 = mp.track(self.melody_part, instrument=self.melody_instrument, channel=0, start_time=0, volume=mp.volume(80))
        t2 = mp.track(self.chords_part, instrument=self.chord_instrument, channel=1, start_time=0, volume=mp.volume(60))
        t3 = mp.track(self.bass_part, instrument=38, channel=2, start_time=0, volume=mp.volume(60))
        piece = mp.build([t1, t2, t3], bpm=self.bpm)
        return piece





