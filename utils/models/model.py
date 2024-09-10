from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from typing import List, Union
import musicpy as mp
import random
import warnings


class ChordJson(BaseModel):
    chord: str = Field(None, description='Chord name defined from musicpy', example='Cmaj')
    intervals: list = Field(None, description='Rhythm of the chord', example=[1/8, 1/8, 1/8, 1/8])
    pattern: list = Field(None, description='Pattern of the chord', example=[1.0, 3.0, 4.0, 1.1, 4.0, 3.0])
    pitch: int = Field(4, description='Pitch of the chord', example=4)







CHORD_TYPES_PROBABILITIES = [
    ('maj7', 0.15),
    ('m7', 0.15),
    ('7', 0.10),
    ('minormajor7', 0.05),
    ('dim7', 0.05),
    ('half-diminished7', 0.05),
    ('aug7', 0.05),
    ('augmaj7', 0.05),
    ('frenchsixth', 0.02),
    ('aug9', 0.02),
    ('9', 0.08),
    ('maj9', 0.08),
    ('m9', 0.08),
    ('augmaj9', 0.02),
    ('add9', 0.04),
    ('madd9', 0.04),
    ('7sus4', 0.04),
    ('7sus2', 0.04),
    ('maj7sus4', 0.02),
    ('maj7sus2', 0.02),
    ('9sus4', 0.02),
    ('9sus2', 0.02),
    ('maj9sus4', 0.02),
]







class PatternGenerator:
    """ 
    USAGE: 
    pg = PatternGenerator()
    """
    def __init__(
        self,
        bars:int=4,
        key:str='C',
        mode:str='major',
        time_signature:list=[4,4],
        chord_progression:int=6543,
        category:str='chord',
    ):
        self.bars= bars
        self.key= key
        self.mode = mode
        self.category = category
        self.time_signature = time_signature
        self.chord_progression = chord_progression
        self.chords = []
        self.chord_choices = []
        self.patterns = []

    # internal methods
    def _update_scale(self):
        return mp.scale(self.key, self.mode)
    
    def print_settings(self):
        print(f'Bars: {self.bars}')
        print(f'Key: {self.key}')
        print(f'Mode: {self.mode}')
        print(f'Time Signature: {self.time_signature}')
        print(f'Chord Progression: {self.chord_progression}')
        print(f'Patterns: {self.patterns}')
        print(f'Intervals: {self.intervals}')
    
    def random_settings(self):
        self.set_bars(random.choice([4,8,12,16]))
        self.set_key(random.choice(['C', 'D', 'E', 'F', 'G', 'A', 'B']))
        self.set_mode(random.choice(['major', 'minor']))
        self.set_category(random.choice(['chord', 'arp']))
        self.set_progression(random.choice([6543, 2345, 1245, 6451, 4362, 6123]))
        self.rhythms = [random.choice(['b - - -', 'b 0 0 b 0 0 b 0', 'b 0 0 b 0 0 b b'])]
        
        combos = [
            {"patterns": [1,2,4,2], "intervals": [1/4]*4},
            {"patterns": [1,2,3,5,1,2,5,3], "intervals": [1/8]*8},
        ]
        selected = random.choice(combos)
        pattern = selected['patterns']
        intervals = selected['intervals']
        self.set_pattern_and_intervals(pattern=pattern, intervals=intervals)
        self.print_settings()

    # settings
    def set_bars(self, bars:int):
        if bars % 4 != 0:
            warnings.warn(f'Bars {bars} is not divisible by 4.')
        self.bars = bars

    def set_key(self, key:str):
        self.key = key
        self.scale = self._update_scale()

    def set_mode(self, mode:str):
        self.mode = mode
        self.scale = self._update_scale() 

    def set_scale(self, scale:mp.scale):
        self.scale = scale
        self.key = scale.tonic()
        self.mode = scale.mode

    def set_category(self, category:str='chord'):
        available_categories = ['chord', 'arp']
        if category not in available_categories:
            raise ValueError(f'Category {category} not in {available_categories}')
        self.category = category

    def set_progression(self, progression:int=6543):
        if self.bars % len(str(progression)) != 0:
            warnings.warn(f'Bars {self.bars} is not divisible by chord progression length {len(str(progression))}')
        self.chord_progression = progression

    def set_time_signature(self, time_signature:list=[4,4]):
        self.time_signature = time_signature
        numerator, denominator = time_signature
        if denominator % 4 != 0:
            warnings.warn(f'Denominator {denominator} is not divisible by 4.')
        if self.bars % numerator != 0:
            warnings.warn(f'Bars {self.bars} is not divisible by time signature {numerator}/{denominator}')

    def set_chord_choices(self, chord_choices:list=[]):
        """
        Choices from mp.database.CHORD_TYPES. Do not include root notes
        """
        if chord_choices == []:
            self.default_chords = CHORD_TYPES_PROBABILITIES # all types

        for chord_type in chord_choices:
            if chord_type[0] in ['C', 'D', 'E', 'F', 'G', 'A', 'B']:
                raise ValueError(f'Root notes in chord_choices not required. Please refer to mp.database.CHORD_TYPES')
        self.chord_choices = list(set(chord_choices))

    def set_patterns(self, patterns:list=[]):
        """
        List of arpeggio patterns.
        
        params: patterns: list of list of floats # [[1,2,3,1.1], [1.1,3,2,1]]
        """
        if patterns == []:
            patterns = [[1,2,3,1.1]] # default up and down

        numerator, denominator = self.time_signature
        for pattern in patterns:
            if len(pattern) != numerator:
                warnings.warn(f'Pattern length must be equal to time signature. Time: {numerator}/{denominator}. Pattern: {pattern}')
        self.patterns = patterns

    def set_intervals(self, intervals:list=[]):
        """
        List of intervals to apply to each chord in the chord progression. Only relevant if we doing arpeggios.
        
        params: intervals: list of floats # [[1/8, 1/2, 1/4, 1/8], [1/8, 1/8, 1/8, 1/8]]
        """
        if intervals == []:
            intervals = [[1/4, 1/4, 1/4, 1/4]]
        
        numerator, denominator = self.time_signature
        for interval in intervals:
            if len(interval) != numerator:
                warnings.warn(f'Interval length must be equal to time signature. Time: {numerator}/{denominator}. Interval: {interval}')
        self.intervals = intervals

    def set_pattern_and_intervals(self, pattern:list=[], intervals:list=[]):
        """
        Practically, cycle of an arpeggios will have an even bars. 
        """
        if pattern == []:
            pattern = [1, 3, 4, 2.1, 3.1, 4, 1.1, 3.1] # default up
        if intervals == []:
            intervals = [1/8, 1/8, 1/8, 1/8, 1/8, 1/8, 1/8, 1/8]

        numerator, denominator = self.time_signature
        if len(pattern) != len(intervals):
            raise ValueError('Pattern and intervals must be the same length')
    
        if sum(intervals) != numerator/denominator:
            warnings.warn(f'Intervals do not add up to time signature. Time: {numerator}/{denominator}. Intervals: {intervals}')

        self.patterns = [pattern]
        self.intervals = [intervals]
        
    def set_rhythms(self, rhythms:list=[]):
        """
        List of rhythms to apply to each chord in the chord progression. Only relevant for non-arpeggio chords.
        """
        if rhythms == []:
            rhythms = ['b - - -']
        self.rhythms = rhythms
        
    # calculate methods
    def get_random_chord_from_default(self):
        chord_types, probabilities = zip(*self.default_chords)
        return random.choices(chord_types, weights=probabilities, k=1)[0]
    
    def generate_chord(self, category='chord', use_self_patterns=True):
        """ 
        Generates a chord for the current chord progression.

        params: use_self_patterns: bool
            If True, the chord will use the patterns set in the PatternGenerator. 
            If False, the chord will invent its own pattern based on its chord type. 
        """

        def adjust_pattern(pattern, n_notes):
            """
            Adjusts a pattern to fit within the number of available notes.
            - If a note in the pattern exceeds `n_notes`, it is replaced with a random available note.
            - If `n_notes` is less than the length of the pattern, the pattern is truncated.
            """
            adjusted_pattern = [min(p, n_notes) for p in pattern]
            return adjusted_pattern

        scale = self.scale
        chord = mp.chord("")

        while chord.bars(mode=0) < self.bars:
            for string in str(self.chord_progression): # '6543'
                degree = int(string)
                root_note = scale.get_note_from_degree(degree) # mp.note obj
                note_str = root_note.name
                pitch = root_note.num 

                # get chord type
                if self.chord_choices == []:
                    chord_type = self.get_random_chord_from_default()
                else:
                    chord_type = random.choice(self.chord_choices)

                intervals = random.choice(self.intervals)
                temp_c = mp.C(f"{note_str}{chord_type}", pitch=pitch)
                n_notes = len(temp_c.notes)
    
                # generate pattern from self, or if chordtype cant support, generate random pattern
                if use_self_patterns == True:
                    pattern = random.choice(self.patterns)
                    pattern = adjust_pattern(pattern, n_notes)
                else:
                    pattern = (random.choices(range(1, n_notes+1), k=len(intervals)))

                print(f'Pattern: {pattern}, {note_str}{chord_type}')

                # arp chord or apply rhythm
                if category == 'arp':
                    chd = mp.C(f"{note_str}{chord_type}", pitch=pitch) @ pattern % (intervals, intervals)
                else:
                    chd = mp.C(f"{note_str}{chord_type}", pitch=pitch)
                    chd = chd.from_rhythm(mp.rhythm(random.choice(self.rhythms), 1))

                self.chords.append(chd)
                chord += chd

        return chord
    








class Track:
    """ 
    Wrapper for mp.chord object
    """
    def __init__(
        self,
        content: mp.chord | None = None,
        name:str='untitled',
        category:str=None,
        progression:list=None,
        instrument:int=None,
        channel:int=None,
        time_signature:list=[4,4],
        key_signature:list=None,
    ):  
        self.content = content
        self.name = name
        self.category = category
        self.progression = progression
        self.time_signature = time_signature
        self.key_signature = key_signature
        self.instrument = instrument
        self.channel = channel
        self.length = None if self.content == None else self.calculate_length()
        
    def __repr__(self):
        if self.name == None:
            name = 'None'
        elif len(self.name) <= 10:
            name = self.name
        else:
            name = f"{self.name[:10]}..."

        if self.category == None:
            category = 'None'
        elif len(self.category) <= 10:
            category = self.category
        else:
            category = f"{self.category[:10]}..."

        length = self.length
        return f"Track(name={name}, category={category}, length={length})"


    def add_chord(self, chord:mp.chord):
        self.content += chord


    def clear(self):
        self.content = None


    def calculate_length(self):
        return self.content.bars()
    
    def cut(self, start, end):
        return # Track(self.content[start:end], self.category, self.progression, self.time_signature, self.key_signature)
    



class SongPart:
    """ 
    Example structure: 
    SP = {
        tracks: [t1, t2, t3], 
        category: 'intro', 
        arrangement: {
            bar_1: [t1, t2], 
            2: [t1], 
            3: [t1], 
            4: [t1, t2, t3],
        }
    }
    """

    def __init__(
        self, 
        name:str=None,
        category:str=None,
    ): 
        self.category = category # intro, verse, chorus, etc 
        self.name = name 
        self.tracks = [] # list of Track objects
        self._arrangement = {} # index and Track

    
    def __repr__(self):
        return (
            f"[SongPart]\n"
            f"Category: {self.category}\n"
            f"Name: {self.name}\n"
            f"Tracks: {self.show()}\n"
        )    


    def show(self, limit=10, only_names=True):
        if limit is None:
            limit = len(self.tracks)
        
        # Truncate tracks if they exceed the limit
        truncated_tracks = self.tracks[:limit]
        if len(self.tracks) > limit:
            truncated_tracks.append('...')  # Indicate more tracks exist
        
        if only_names == True:
            names = []
            for track in truncated_tracks:
                if len(track.name) > 10:
                    name = track.name[:10] + '...'
                else:
                    name = track.name 
                names.append(name)
            result = ', '.join(name for name in names)

        else:
            result = ', '.join(str(track) for track in truncated_tracks)
        return result
    

    def add_track(self, track:Track, set_index:list=[]):
        """ 
        Add a Track object to part. 
        If no set_index is given, the track is added, but will not appear in arrangement!
        """
        if not isinstance(track, Track):
            raise TypeError(f"Expected a Track object, but got {type(track).__name__}.")

        self.tracks.append(track)
        message = f"{track} added as index: {len(self.tracks)-1}"

        if set_index != []:
            self.set_track_to_index(track_index=len(self.tracks)-1, part_index=set_index)
            message += f" and set to index: {set_index}"
        print(message)     


    def set_track_to_index(self, track_index:int, part_index:list=[0]):
        """
        Assign Track to the index of Part.
        Usage: 
            part.set_track_to_index(track_index=0, part_index=[0,1,2,3])

        Assigns Track0 for bar 0, 1, 2, 3.
        If Track0 plays for longer than 1 bar, you can get simultaneous playing
        """
        if track_index < 0 or track_index >= len(self.tracks):
            raise IndexError("Track index is out of range.")
        
        track = self.tracks[track_index]
        for i in part_index:
            if i not in self._arrangement:
                self._arrangement[i] = []
            if track not in self._arrangement[i]:
                self._arrangement[i].append(track)

    
    def delete_track_from_index(self, track_index:int, part_index:list=[0]):
        """ 
        Delete Track from the index of Part.
        """
        if track_index < 0 or track_index >= len(self.tracks):
            raise IndexError("Track index is out of range.")
        
        track = self.tracks[track_index]
        for i in part_index:
            if i not in self._arrangement:
                continue

            if track in self._arrangement[i]:
                self._arrangement[i].remove(track)


    def clear_tracks(self):
        self.tracks = []
        self._arrangement = {}


    def clear_arrangement(self):
        self._arrangement = {}


    def build(self, bpm=120) -> mp.piece:
        """ 
        WARNING: While it works, each mp.track created is a separate track when exporting as mid
        If you have non-zero start times, or if you have repititive arps, you will end up creating a lot of tracks. 
        This is not ideal when it comes to saving MIDI files as you get a lot of duplicated tracks. 

        We have another method that only returns the track -- export_tracks()

        Build a mp.piece obj out from arrangement: 

        Example:
        arrangement = {
            0: [Track0],
            1: [Track4, Track5, Track6],
        }

        t1 = mp.track(Track0, channel=1, instrument=2, start_time=0)
        t2 = mp.track(Track4, channel=1, instrument=2, start_time=1)
        t3 = mp.track(Track5, channel=1, instrument=2, start_time=1)
        t4 = mp.track(Track6, channel=1, instrument=2, start_time=1)

        piece = mp.build([t1, t2, t3, t4], bpm=120)
        """
        if self._arrangement == {}:
            raise Exception('No parts found. Run either add_part() or set_part_to_index() first.')
        
        # create chord as key, start times as values
        dct = {}
        for bar_index, track_list in self._arrangement.items():
            for track in track_list:
                chd = track.content
                if chd not in dct:
                    dct[chd] = {"start_times": [], "instrument": track.instrument, "channel": track.channel}
                dct[chd]["start_times"].append(bar_index)

        # one track for each unique chord
        # BUG: It is possible for track instrument to not be respected if there is collision in channel.
        tracks = []
        for chd, info in dct.items():
            combined_chord = mp.chord('')
            for start_time in info["start_times"]:
                chd_copy = chd.copy() 
                chd_copy.start_time = start_time 
                combined_chord &= chd_copy

            mp_track = mp.track(
                combined_chord, 
                channel=info["channel"] if info["channel"] is not None else 1, 
                instrument=info["instrument"] if info["instrument"] is not None else 2, 
                start_time=0, 
                volume=mp.volume(80)
            )
            tracks.append(mp_track)

        piece = mp.build(tracks, bpm=bpm)
        return piece


    def export_tracks(self, as_file=True, name='untitled.mid', bpm=120):
        """ 
        Exports all tracks as a MIDI file.
        """
        tracks = [] 

        for track in self.tracks:
            chd = track.content 
            mp_track = mp.track(
                chd, 
                channel=track.channel if track.channel is not None else 1,
                instrument=track.instrument if track.instrument is not None else 2,
                start_time=0, 
                volume=mp.volume(60)
            )
            tracks.append(mp_track)

        piece = mp.build(tracks, bpm=bpm)
        if as_file == True:
            mp.write(piece, name=name)
            print(f"MIDI file saved as {name}")
        else:
            return piece
    





class Song: 
    def __init__(
        self, 
    ): 
        self.parts = []
        self._arrangement = {}


    def __repr__(self):
        base_str = ", ".join([f"{part.name}" for part in self.parts])
        return (
            f"[Song]\n"
            f"Parts: [{base_str}]\n"
        )
    

    def show_arrangement(self):
        dct = {}
        for start, parts in sorted(self._arrangement.items()):
            dct[start] = [part.name for part in parts]
        return dct


    def add_part(self, part:SongPart, set_index:list=[]):
        """ 
        Add a SongPart to Song. 
        If no set_index is given, the part is added, but will not appear in arrangement!
        """
        if not isinstance(part, SongPart):
            raise TypeError(f"Expected a SongPart object, but got {type(part).__name__}.")
    
        self.parts.append(part)
        message = f"{part} added as index: {len(self.parts)-1}"

        if set_index != []:
            self.set_part_to_index(part_index=len(self.parts)-1, start_times=set_index)
            message += f" and set to time: {set_index}"
        print(message)   


    def set_part_to_index(self, part_index:int, start_times:list=[0.0]):
        """
        Assign Part to the index of Song.
        Usage: 
            song.set_part_to_index(part_index=0, start_time=0.0)

        Assigns Part0 for bar 0.
        If Part0 plays for longer than 1 bar, you can get simultaneous playing
        """
        if part_index < 0 or part_index >= len(self.parts):
            raise IndexError("Part index is out of range.")
        
        part = self.parts[part_index]

        for start_time in start_times:
            if start_time not in self._arrangement:
                self._arrangement[start_time] = []
        
            if part not in self._arrangement[start_time]:
                self._arrangement[start_time].append(part)


    def delete_part_from_index(self, part_index:int, start_times:list=[0.0]):
        """ 
        Delete Part from the index of Song.
        """
        if part_index < 0 or part_index >= len(self.parts):
            raise IndexError("Part index is out of range.")
        
        part = self.parts[part_index]
        
        for start_time in start_times:
            if start_time not in self._arrangement:
                continue
            
            if part in self._arrangement[start_time]:
                self._arrangement[start_time].remove(part)
                
                if self._arrangement[start_time] == []:
                    del self._arrangement[start_time]


    def build(self, bpm=120) -> mp.piece:
        """
        Builds a `mp.piece` object from all parts and their arrangements.
        
        Will merge all common pattern into a single track, regardless of which song part
        it originates from.
        """
        # create chord as key, start times as values EG: { mp.C: [1,2,3] }
        chord_dict = {} 
        for start_time, parts in self._arrangement.items(): # 0: [intro], 1: [verse]
            
            for part in parts:
                part_arrangement = part._arrangement # intro: { 1: [Track1, Track2], 2: [Track3] }

                for bar, track_list in part_arrangement.items():
                    adjusted_start_time = bar + start_time 

                    for track in track_list:
                        chd = track.content
                        if chd not in chord_dict:
                            chord_dict[chd] = []
                        chord_dict[chd].append(adjusted_start_time)
        
        tracks = []
        for chd, start_times in chord_dict.items():
            combined_chord = mp.chord('')
            for start_time in start_times:
                chd_copy = chd.copy() 
                chd_copy.start_time = start_time 
                combined_chord &= chd_copy
                
            mp_track = mp.track(combined_chord, channel=1, instrument=2, start_time=0, volume=mp.volume(60))
            tracks.append(mp_track)

        piece = mp.build(tracks, bpm=bpm)
        return piece
    

    def export_tracks(self, as_file=True, name='untitled.mid', bpm=120):
        """Exports all tracks as a MIDI file."""
        piece = self.build(bpm=bpm)
        if as_file:
            mp.write(piece, name=name)
            print(f"MIDI file saved as {name}")
        else:
            return piece

