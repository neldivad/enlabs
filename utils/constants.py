DRUM_MAPPING = {
    35: 'Acoustic Bass Drum',
    36: 'Bass Drum 1',
    37: 'Side Stick',
    38: 'Acoustic Snare',
    39: 'Hand Clap',
    40: 'Electric Snare',
    41: 'Low Floor Tom',
    42: 'Closed Hi-Hat',
    43: 'High Floor Tom',
    44: 'Pedal Hi-Hat',
    45: 'Low Tom',
    46: 'Open Hi-Hat',
    47: 'Low-Mid Tom',
    48: 'Hi-Mid Tom',
    49: 'Crash Cymbal 1',
    50: 'High Tom',
    51: 'Ride Cymbal 1',
    52: 'Chinese Cymbal',
    53: 'Ride Bell',
    54: 'Tambourine',
    55: 'Splash Cymbal',
    56: 'Cowbell',
    57: 'Crash Cymbal 2',
    58: 'Vibraslap',
    59: 'Ride Cymbal 2',
    60: 'Hi Bongo',
    61: 'Low Bongo',
    62: 'Mute Hi Conga',
    63: 'Open Hi Conga',
    64: 'Low Conga',
    65: 'High Timbale',
    66: 'Low Timbale',
    67: 'High Agogo',
    68: 'Low Agogo',
    69: 'Cabasa',
    70: 'Maracas',
    71: 'Short Whistle',
    72: 'Long Whistle',
    73: 'Short Guiro',
    74: 'Long Guiro',
    75: 'Claves',
    76: 'Hi Wood Block',
    77: 'Low Wood Block',
    78: 'Mute Cuica',
    79: 'Open Cuica',
    80: 'Mute Triangle',
    81: 'Open Triangle'
}   


MAIN_DRUMS = {36, 38, 40, 41, 43, 45, 47, 48, 50}  # Snares, bass, sticks, toms
METAL_DRUMS = {42, 44, 46, 49, 51}  # Hi-hats, crash cymbals



RHYTHM_VARIANTS = [
    {
        'name': 'Quarter',
        'rhythm': 'b b b b',
        'bars': 1,
        'time_signature': '4/4',
    },
    {
        'name': 'Eighth',
        'rhythm': 'b b b b b b b b',
        'bars': 1,
        'time_signature': '4/4',
    }, 
    {
        'name': 'Tresillo',
        'rhythm': 'b - - b - - b b',
        'bars': 1,
        'time_signature': '4/4',
    },
    {
        'name': 'Double Tresillo',
        'rhythm': 'b 0 0 b 0 0 b 0 0 b 0 0 b 0 b 0',
        'bars': 2,
        'time_signature': '4/4',
    },
    {
        'name': 'Gallop',
        'rhythm': 'b 0 b b b 0 b b',
        'bars': 1,
        'time_signature': '4/4',
    },
    {
        'name': 'Habanera',
        'rhythm': 'b 0 0 b b 0 b 0',
        'bars': 1,
        'time_signature': '4/4',
    },
    {
        'name': 'Barbara Ann',
        'rhythm': 'b 0 b 0 b 0 0 b 0 b 0 b b 0 b 0',
        'bars': 2,
        'time_signature': '4/4',
    },
    {
        'name': 'Aksak 9/8',
        'rhythm': 'b 0 b 0 b 0 b 0 0',
        'bars': 1,
        'time_signature': '9/8',
    },
    {
        'name': 'Son Clave',
        'rhythm': 'b 0 0 b 0 0 b 0 0 0 b 0 b 0 0 0',
        'bars': 2,
        'time_signature': '4/4',
    },
    {
        'name': 'Bossa Nova',
        'rhythm': 'b 0 0 b 0 0 b 0 0 0 b 0 0 b 0 0',
        'bars': 2,
        'time_signature': '4/4',
    },
    {
        'name': 'Mission Impossible 5/4',
        'rhythm': 'b 0 0 b 0 0 b 0 b 0',
        'bars': 1,
        'time_signature': '5/4',
    },
    {
        'name': 'Football Clap',
        'rhythm': 'b 0 b 0 b b b 0 b b b b 0 b b 0',
        'bars': 2,
        'time_signature': '4/4',
    },
]


