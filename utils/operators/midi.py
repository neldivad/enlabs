import musicpy as mp

# Function to convert a note to its MIDI position
def note_to_midi(note):
    try:
        if isinstance(note, str):
            # Check if the note has an octave indicator
            if note[-1].isdigit():
                note_str = note[:-1]
                note_octave = int(note[-1]) # rmb to convert str to int
                return mp.note(note_str, note_octave).degree
            
            # get note obj for str itself
            else:
                return mp.note(note).degree

        # access note method if is note instance already
        return note.degree

    except Exception as e:
        print(f"Error converting note {note} to MIDI: {e}")
        return None


# Function to convert a MIDI position to a note
def midi_to_note(midi_pos, note_as_string=False):
    try:
        note_obj = mp.note('C', 4) # init note obj
        note_obj.degree = midi_pos

        if note_as_string == True:
            return str(note_obj)
        else:
            return note_obj # note obj, not string!

    except Exception as e:
        print(f"Error converting MIDI {midi_pos} to note: {e}")
        return None
