import musicpy as mp


def generate_rhythm_for_chord(chord, rhythm:str, bars:int=1, accent:bool=False, high_volume:int=80, low_volume:int=50):
    """ 
    Applies rhythm to chord obj.
    If accent is True, replaces all rest and sustain with beat, but beat velocity is set lower. 

    params:
        chord: mp.chord
        rhythm: str
        bars: int
        accent: bool
        high_volume: int
        low_volume: int 
    """
    if accent != True:
        chd = chord.from_rhythm(mp.rhythm(rhythm, bars))
        return chd
    
    r_list = rhythm.split()
    new_r_list = ' '.join(['b' if x != 'b' else 'b' for x in r_list])
    chd = chord.from_rhythm(mp.rhythm(new_r_list, bars))
    notes = chd.notes
    note_count = len(chord.notes)  # Number of simultaneous notes in the chord
    rhythm_length = len(r_list)
    
    for i in range(0, len(notes), note_count):
        chunk_index = (i // note_count) % rhythm_length
        for j in range(note_count):
            if r_list[chunk_index] == 'b':
                notes[i + j].set_volume(high_volume)
            else:
                notes[i + j].set_volume(low_volume)

    return chd