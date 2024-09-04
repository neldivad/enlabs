import musicpy as mp
from utils.operators.midi import note_to_midi, midi_to_note






def join_chords(chords:list):
    joined = mp.chord('')
    for chd in chords:
        joined += chd
    return joined



def normalize_chord(chord, target_octave:int=5, note_as_string:bool=False):
    midi_positions = [note_to_midi(note) for note in chord]
    normalized_midi = [(midi % 12) + (target_octave * 12) for midi in midi_positions]
    return [midi_to_note(midi, note_as_string) for midi in normalized_midi]



def voice_2_chords(chord1, chord2, note_as_string:bool=False):
    """ 
    Converts all notes in both chords to MIDI. Then minimize the difference by rearranging
    each note by octaves to discover optimal inversion. 
    """
    # Normalize both chords to pitch 4
    chord1 = normalize_chord(chord1, 4, note_as_string)
    chord2 = normalize_chord(chord2, 4, note_as_string)

    # transform list of notes to MIDI numbers
    c1_midi = [note_to_midi(note) for note in chord1]
    c2_midi = [note_to_midi(note) for note in chord2]

    midi_best_range = float('inf')
    midi_combination = c2_midi # list of midi values

    for i in range(len(c2_midi)):
        # shift notes in chord2 by octaves to minimize transition from chord1
        shifted_combination = c2_midi[i:] + [note + 12 for note in c2_midi[:i]]

        # get the sum of the absolute differences between the chord notes 
        midi_range = sum(abs(a - b) for a, b in zip(c1_midi, shifted_combination)) / len(c1_midi)

        if midi_range < midi_best_range:
            midi_combination = shifted_combination
            midi_best_range = midi_range

    return [midi_to_note(midi, note_as_string) for midi in midi_combination]






def lengthen_note_duration_in_chord(chord, duration:float=0.125):
    """
    Lengthens the duration of all notes in the chord by the given duration.
    
    chord: mp.chord
        The chord object to lengthen.

    duration: float
        The duration to lengthen the notes by.

    Returns:
        mp.chord
            The chord object with the notes lengthened.
    """
    new_chord = chord.copy()
    original_bars = chord.bars()
    for note in new_chord.notes:
        note.duration = duration
    new_chord.cut(ind1=0, ind2=original_bars, cut_extra_duration=True, cut_extra_interval=True, round_duration=True, round_cut_interval=True)
    return new_chord






def detect_chord_name(chord_obj):
    """
    Infers the chord name from the chord object. 

    chord_obj: mp.chord
        The chord object to infer the chord name from.

    Returns:
        str
            The chord name.
    """
    # Infer chord
    notes = [str(n) for n in chord_obj.notes]
    chord_str = ','.join(notes)
    detected_chord = mp.alg.detect(chord_str, root_preference=True)

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
    return short_chord



def accenting_rhythm_chord(chord, rhythm, bars, high_volume:int=80, low_volume:int=60, bounce_low_notes:bool=False, bounce_pattern:str='fifth'):
    """ 
    Instead of applying rhythm to a chord, replaces all rests and sustains with beats and lowers volume.

    chord: mp.chord
        The chord object to apply accent to.
    
    rhythm: str
        Rhythm string in the form of 'b b b b b b b b'
    
    bars: int
        Number of bars the rhythm should last.

    high_volume: int
        Volume of the high beats.
        
    low_volume: int
        Volume of the low beats.
        
    bounce_low_notes: bool 
        If True, the low notes will bounce up by 12 semitones.
    """
    r_list = rhythm.split()
    new_r_list = ' '.join(['b' if x != 'b' else 'b' for x in r_list])
    chd = chord.from_rhythm(mp.rhythm(new_r_list, bars))
    notes = chd.notes
    note_count = len(chord.notes)  # Number of simultaneous notes in the chord
    rhythm_length = len(r_list)
    bounce_counter = 0
    
    for i in range(0, len(notes), note_count):
        chunk_index = (i // note_count) % rhythm_length

        for j in range(note_count):
            if r_list[chunk_index] == 'b':
                notes[i + j].set_volume(high_volume)
            else:
                notes[i + j].set_volume(low_volume)
                if bounce_low_notes == True:
                    if bounce_pattern == 'octave':
                        notes[i + j] += 12
                    
                    elif bounce_pattern == 'fifth':
                        if bounce_counter % 2 == 0:
                            notes[i + j] += 7
                        else:
                            notes[i + j] += 12
                        bounce_counter += 1

                    else:
                        raise ValueError(f'Bounce pattern {bounce_pattern} not supported.')

    return chd



def clamp_chord_pattern(chord_obj, pattern):
    """ 
    Certain patterns cannto be applied to chords if they contain notes outside the chord range.
    This function will clamp the pattern to the chord range. 

    EG: 
    Cmaj : [1, 2.2, 3.1, 4.2] >> [1, 2.2, 3.1, 3.2]
    """
    n_notes = len(chord_obj.notes)
    clamped_pattern = []

    for index in pattern:
        # Clamp the index to the valid range [1, n_notes]
        if isinstance(index, float):
            base_note = int(index)  # Get the base note index (before the decimal point)
            fractional_part = index - base_note  # Keep the fractional part
            base_note = max(1, min(base_note, n_notes))  # Clamp the base note
            clamped_index = round(base_note + fractional_part, 1)  # Recombine with the fractional part
        else:
            clamped_index = max(1, min(index, n_notes))  # Clamp the integer index

        clamped_pattern.append(clamped_index)

    return clamped_pattern




# def reconstruct_note_dict(note_dict):
#     chd  = mp.chord('')
#     for dct in note_dict:
#         notes = dct.get('notes', 'Unknown')
#         note_str = ','.join(notes)
#         interval = dct.get('interval', 0) 
#         chd += mp.chord(note_str, duration=interval) # implicitly already has legato
    
#     return chd


# def reconstruct_bass(deconstructed_bass):
#     try:
#         chd = mp.chord('')
#         for c in deconstructed_bass:
#             cname = c.get('chord', 'Unknown')
#             pitch = c.get('pitch', 4)
#             rhythm = c.get('rhythm', [])
#             pattern = c.get('pattern', [])
#             try:
#                 chd += mp.C(cname, pitch=pitch) @ pattern % (rhythm, rhythm)
#             except Exception as e:
#                 chd += mp.chord(cname) @ pattern % (rhythm, rhythm)
                
#         chd = apply_legato(chd)
#         return chd
    
#     except Exception as e:
#         print(f"Error {e}. Pattern contains note outside chord range.")
#         st.error(f"Error {e}. Pattern contains note outside chord range.")
#         return
    