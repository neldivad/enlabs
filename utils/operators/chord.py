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
    