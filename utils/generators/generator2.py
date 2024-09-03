import random
import musicpy as mp
from operators.chord import join_chords




def chords_to_dict_list(chords:list=[]):
    """ 
    Converts a list of chords to a list of dicts. 
    
    Example: 
        input: 
            [mp.C('Cmaj7'), mp.C('Fmaj7'), mp.C('G7sus'), mp.C('Am11')]
        output: 
            [{'chord': 'Cmaj7', 'rhythm': [0.25, 0.125, 0.125, 0, 0.125, 0.125, 0.125, 0.25], 'pattern': [1.0, 1.1, 1.0, 3.0, 3.0, 4.0, 1.0, 1.1], 'pitch': 4, 'start': 0.0, 'end': 1.0},
             {'chord': 'Fmaj7', 'rhythm': [0.125, 0.125, 0.125, 0.25, 0.125, 0.25], 'pattern': [1.0, 3.0, 1.1, 4.0, 1.1, 1.0], 'pitch': 4, 'start': 1.0, 'end': 2.0},..
            ]
    """
    dict_list = []
    for chd in chords:
        inferred_chord = mp.alg.detect(chd).split(' ')[0]
        n_notes = len(mp.C(inferred_chord).notes)

        # Create a pattern by cycling through 1 to n_notes
        pattern = []
        while len(pattern) < len(chd.interval):
            pattern.extend(range(1, n_notes + 1))

        # Trim the pattern if it's longer than the interval length
        pattern = pattern[:len(chd.interval)]

        dict_list.append({
            'chord': inferred_chord,
            "intervals": chd.interval,
            "pattern": pattern,
            "pitch": chd.notes[0].num,
        })
    return dict_list



def generate_chord_from_scale(
    scale, 
    progression:int=6543, 
    n_notes:int=4,
    rhythm: mp.rhythm=None,
    omit:list=[],
    inversion:int=None,
    return_as_chord:bool=False,
):
    """
    Generates chords based on the given scale and chord progression.

    :param scale: The scale object (e.g., mp.scale)
    :param progression: Chord progression positions (e.g., 6451)
    :param rhythm_duration: Duration of each chord
    :return: List of chords
    """
    chords = scale % (progression, n_notes)  # Default to 4 notes per chord

    # Apply omission if specified
    if omit != []:
        for o in omit:
            chords = [chord.omit(o) for chord in chords]

    # Apply inversion if specified
    if inversion:
        chords = [chord.inversion_highest(inversion) for chord in chords]

    if rhythm:
        chords = [chd.from_rhythm(rhythm) for chd in chords]

    if return_as_chord:
        return join_chords(chords)
    
    dict_list = chords_to_dict_list(chords)
    return dict_list



def generate_chord_from_chords(
    chords: list=[],
    rhythm: mp.rhythm=None,
    return_as_chord:bool=True,
):
    if rhythm == None:
        raise ValueError('Must have rhythm before chords can be generated')

    if chords == []:
        chords = [
            mp.C('Cmaj7',4), 
            mp.C('Fmaj7',3),
            mp.C('G7, b9, omit 5',3), 
            mp.C('Bdim7',3), 
            mp.C('Am7', 3), 
            mp.C('D7', 3) ^ 2, 
            mp.C('FmM7', 3) ^ 2, 
            mp.C('G7,#5', 3)
        ]
    
    chds = []
    for chord in chords:
        chd = chord.from_rhythm(rhythm)
        chds.append(chd)
    
    if return_as_chord:
        return join_chords(chds)
    
    dict_list = chords_to_dict_list(chds)
    return dict_list




def generate_arp_from_scale(
    scale,
    progression:int=6541,
    n_notes:int=4, 
    interval:float=1/8, 
    omit:list=[], 
    inversion:int=None,
    pattern:list=[],
    return_as_chord:bool=False,
):
    """
    Generates an arpeggio based on the given scale, chord progression, and transformations.

    scale: The scale object (e.g., mp.scale)
    
    progression: int 
        Chord progression positions (e.g., 6451)
    
    n_notes: int
        Number of notes in the chord, extending upwards. EG: 3 for a triad, 4 for Cm7, 5 for Cm9 

    interval: float
        Interval between notes in the chord. EG: 1/8 for a simple arpeggio

    omit: list of int
        Degree of the chord to omit (e.g., 3 for the 5th). Will reduce the final number of notes by 1 per int in list 

    inversion: int
        Degree to invert (e.g., 2 for the 2nd inversion) 

    pattern: list of int
        Arpeggio pattern. EG: [1,2,3,1.1] for a simple arpeggio

    """
    chords = scale % (progression, interval, interval, n_notes)

    # Apply omission if specified
    if omit != []:
        for o in omit:
            chords = [chord.omit(o) for chord in chords]

    # Apply inversion if specified
    if inversion:
        chords = [chord.inversion_highest(inversion) for chord in chords]

    if pattern == []:
        if return_as_chord:
            return join_chords(chords)
        
        dict_list = chords_to_dict_list(chords)
        return dict_list
    
    dict_list = []
    new_chords = []
    for chd in chords:
        new_chords.append(chd @ pattern % (interval, interval))
        cname = mp.alg.detect(chd).split(' ')[0] # eg: 'Cmaj7'
        chord_dict = {
            'chord': cname,
            'intervals': [interval] * len(chd.notes),
            'pattern': pattern,
            'pitch': chd.notes[0].num,
        }
        dict_list.append(chord_dict)

    if return_as_chord:
        return join_chords(new_chords) 
    return dict_list




def generate_arp_from_chords(
    chords: list=[], 
    patterns: list=[[1, 3, 4, 2.1, 3.1, 4, 1.1, 3.1], [1, 3, 4, 2.1, 3.1, 4, 2.1, 3.1]],
    time_signature:list=[4,4],
    bar_length_per_chord:int=1,
    return_as_chord:bool=True,
):
    """ 
    Generates an arpeggio based on the given chords and patterns.
    
    :param chords: List of chords (e.g., [C('Cmaj7', 4), C('Fmaj7', 3)])
    :param patterns: List of arpeggio patterns (e.g., [[1, 3, 4, 2.1, 3.1, 4, 1.1, 3.1], [1, 3, 4, 2.1, 3.1, 4, 2.1, 3.1]])
    :param time_signature: Time signature (e.g., [4,4])
    :return: mp.chord object
    """
    numerator, denominator = time_signature
    pattern_length = len(patterns[0])
    for pattern in patterns:
        if len(pattern) % numerator !=0:
            raise ValueError(f'Pattern length must by divisible by numerator. Time: {time_signature}, Pattern: {pattern}')
        
    # have a default chord set
    if chords == []:
        chords = [
            mp.C('Cmaj7',4), 
            mp.C('Fmaj7',3),
            mp.C('G7, b9, omit 5',3), 
            mp.C('Bdim7',3), 
            mp.C('Am7', 3), 
            mp.C('D7', 3) ^ 2, 
            mp.C('FmM7', 3) ^ 2, 
            mp.C('G7,#5', 3)
        ]

    dict_list = []
    chds = []
    for chord in chords:
        interval = bar_length_per_chord / pattern_length
        pattern = random.choice(patterns)
        chd = chord @ pattern % (interval, interval)
        chds.append(chd)

        # add to dict_list
        cname = mp.alg.detect(chd).split(' ')[0] # eg: 'Cmaj7'
        chord_dict = {
            'chord': cname,
            'intervals': [interval] * len(chd.notes),
            'pattern': pattern,
            'pitch': chd.notes[0].num,
        }
        dict_list.append(chord_dict)

    if return_as_chord == False:
        return dict_list
    return join_chords(chds)














