import random
import tempfile  
import os      
from music_elements import Note, Chord
from track import Track
from composition import Composition
from midi_exporter import MidiExporter



# ----------------------------------------------------------------------
# %% --- Music Theory Definitions ---
# ----------------------------------------------------------------------

PITCH_MAP = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor_natural': [0, 2, 3, 5, 7, 8, 10],
    'minor_harmonic': [0, 2, 3, 5, 7, 8, 11]
}

### UPDATED ###
# Diatonic chord qualities for each scale degree (1-7)
DIATONIC_QUALITIES = {
    'major': ['maj', 'min', 'min', 'maj', 'dom7', 'min', 'dim'], # V is dom7
    'minor_natural': ['min', 'dim', 'maj', 'min', 'min', 'maj', 'maj'],
    # V is dom7 in harmonic minor
    'minor_harmonic': ['min', 'dim', 'maj(aug)', 'min', 'dom7', 'maj', 'dim']
}

# More complex voicings (intervals from root)
# The parser in get_chord_pitches will find the longest matching key
CHORD_VOICINGS = {
    # Triads
    'maj': [0, 4, 7],
    'min': [0, 3, 7],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'maj(aug)': [0, 4, 8], # Alias
    'sus2': [0, 2, 7],
    'sus4': [0, 5, 7],
    
    # Sevenths
    'maj7': [0, 4, 7, 11], # Major 7th
    'dom7': [0, 4, 7, 10], # Dominant 7th
    'min7': [0, 3, 7, 10],
    'dim7': [0, 3, 6, 9],
    'm7b5': [0, 3, 6, 10], # Half-diminished
    'min(maj7)': [0, 3, 7, 11],
    
    # Extensions (common voicings)
    'add9': [0, 4, 7, 14],
    'min(add9)': [0, 3, 7, 14],
    'maj9': [0, 4, 7, 11, 14],
    'min9': [0, 3, 7, 10, 14],
    'dom9': [0, 4, 7, 10, 14],
    'dom13': [0, 4, 7, 10, 14, 21], # Omits 11th
    'maj13': [0, 4, 7, 11, 14, 21], # Omits 11th
    'min11': [0, 3, 7, 10, 14, 17],
    
    ### NEWLY ADDED VOICINGS ###
    'dom7#9': [0, 4, 7, 10, 15],  # The "Hendrix Chord"
    'dom7b9': [0, 4, 7, 10, 13],
    'maj7#11': [0, 4, 7, 11, 18], # No 9
    'min13': [0, 3, 7, 10, 14, 21]
}

# ----------------------------------------------------------------------
# %% --- Helper Functions ---
# ----------------------------------------------------------------------

def midi_to_note_name(pitch: int) -> str:
    """Converts a MIDI pitch number (0-127) to a note name (e.g., C4)."""
    if not (0 <= pitch <= 127):
        return "N/A"
    
    # MIDI 12 is C0, 24 is C1, 60 is C4 (Middle C)
    octave = (pitch // 12) - 1
    note_index = pitch % 12
    note = NOTE_NAMES[note_index]
    return f"{note}{octave}"

def get_diatonic_chords(root_name: str, scale_type: str) -> list[str]:
    """
    Generates the 7 diatonic chord symbols for a given key and scale.
    e.g., ('C', 'major') -> ['Cmaj', 'Dmin', 'Emin', 'Fmaj', 'Gdom7', 'Amin', 'Bdim']
    """
    if scale_type not in SCALES or scale_type not in DIATONIC_QUALITIES:
        raise ValueError(f"Scale type '{scale_type}' not defined.")
        
    root_val = PITCH_MAP[root_name.upper()]
    intervals = SCALES[scale_type]
    qualities = DIATONIC_QUALITIES[scale_type]
    
    chords = []
    for i in range(7):
        note_val = (root_val + intervals[i]) % 12
        note_name = NOTE_NAMES[note_val]
        quality = qualities[i]
        chords.append(f"{note_name}{quality}")
        
    return chords


def get_chord_pitches(chord_symbol: str, base_octave: int, octave_offset: int = 0, inversion: int = 0) -> list[int]:
    """
    Converts a chord symbol into a list of MIDI pitches, applying octave and inversion.
    e.g., ('Cmaj', 4, 0, 1) -> [64, 67, 72] (1st inversion)
    """
    
    ### UPDATED PARSER ###
    # This parser is now more robust. It finds the longest matching
    # quality string (e.g., 'min(maj7)') before falling back to 'min'.
    
    # 1. Parse Root
    if len(chord_symbol) > 1 and (chord_symbol[1] == '#' or chord_symbol[1] == 'b'):
        root_name = chord_symbol[0:2]
        quality_str = chord_symbol[2:]
    else:
        root_name = chord_symbol[0]
        quality_str = chord_symbol[1:]
        
    if root_name not in PITCH_MAP:
        raise ValueError(f"Root note '{root_name}' not in PITCH_MAP.")

    # 2. Parse Quality
    # Find the longest matching quality key in CHORD_VOICINGS
    quality = None
    for length in range(len(quality_str), 0, -1):
        if quality_str[:length] in CHORD_VOICINGS:
            quality = quality_str[:length]
            # You could also parse alterations here (e.g., b9, #11)
            # but that requires a more complex interval system.
            # For now, we just match the main quality.
            break
            
    if quality is None:
        print(f"Warning: Quality '{quality_str}' not in CHORD_VOICINGS. Using 'maj'.")
        quality = 'maj'
        
    # 3. Get root position pitches
    root_pitch = PITCH_MAP[root_name] + ((base_octave + octave_offset) * 12)
    intervals = CHORD_VOICINGS[quality]
    pitches = [root_pitch + i for i in intervals]
    
    # 4. Apply Inversions
    for i in range(inversion):
        if not pitches:
            break
        # Take the lowest note, move it up an octave
        bass_note = pitches.pop(0)
        pitches.append(bass_note + 12)
        
    return pitches


# ----------------------------------------------------------------------
# %% --- Song Configuration ---
# ----------------------------------------------------------------------

SONG_STRUCTURE = [
    {
        "part_name": "Chorus (Specified)",
        "key": "C",
        "scale_type": "major",
        
        "progression_symbols": [
            "Cmaj9",    # I
            "Gdom9",    # V(9)
            "Amin11",   # vi
            "REST",     # <--- A rest
            "Fmaj13"    # IV
        ],
        "inversions": [0, 1, 0, 0, 0], # Added a 0 for the rest (it's ignored)
        "octave_pattern": [0, 0, 0, 0, 0], # Added a 0 for the rest
        "rhythm_beats": [
            4,          # Cmaj9
            4,          # Gdom9
            4,          # Amin11
            2,          # <--- 2-beat rest
            2           # <--- 2-beat chord
        ], 
        "play_style": "block",
        "arpeggio_pattern": [0.25, 0.25, 0.25, 0.25],
        "num_loops": 1
    }
]

# --- Global Song Settings ---
SONG_TITLE = "Modular Progression v2"
OUTPUT_FILENAME = "modular_progression_v2.mid"
TEMPO = 120
TIME_SIGNATURE = (4, 4)
INSTRUMENT_PROGRAM = 50 # 50: Synth Strings 1
CHANNEL = 0
VOLUME = 90
BASE_OCTAVE = 4 # The "home" octave for all parts


# ----------------------------------------------------------------------
# %% --- Main Generation Logic ---
# ----------------------------------------------------------------------

def main():
    """Generates and exports the multi-part chord progression."""
    print(f"Generating song: '{SONG_TITLE}'")
    
    # 1. Set up Track and Composition
    chord_track = Track(
        name="Chord Progression",
        instrument_program=INSTRUMENT_PROGRAM,
        channel=CHANNEL,
        volume=VOLUME
    )
    
    song = Composition(
        title=SONG_TITLE,
        tempo=TEMPO,
        time_signature=TIME_SIGNATURE
    )

    # 2. Generate the full sequence part-by-part
    current_time = 0.0
    full_progression_symbols = []
    
    print("Generating notes...")
    
    for part in SONG_STRUCTURE:
        part_name = part['part_name']
        print(f"--- Generating Part: {part_name} ---")
        
        # This list will hold the chord symbols for this part
        part_chord_symbols = []

        ### NEW LOGIC: Check for 'progression_symbols' first ###
        if 'progression_symbols' in part:
            print(f"    Using specified chord symbols.")
            part_chord_symbols = part['progression_symbols']
            
        elif 'progression_degrees' in part:
            print(f"    Using diatonic degrees for {part['key']} {part['scale_type']}.")
            try:
                diatonic_chords = get_diatonic_chords(part['key'], part['scale_type'])
                print(f"    Diatonic chords: {', '.join(diatonic_chords)}")
                for degree in part['progression_degrees']:
                    if not (1 <= degree <= 7):
                        print(f"    Invalid degree {degree}, skipping.")
                        continue
                    part_chord_symbols.append(diatonic_chords[degree - 1])
            except Exception as e:
                print(f"    Error setting up diatonic chords for {part_name}: {e}")
                continue
        else:
            print(f"    No 'progression_symbols' or 'progression_degrees' found for {part_name}. Skipping part.")
            continue
            
        # --- Loop through the part's progression ---
        for _ in range(part['num_loops']):
            for i, chord_symbol in enumerate(part_chord_symbols):
                
                # ... inside the `for i, chord_symbol in enumerate(part_chord_symbols):` loop ...

                # --- Get Chord Properties ---
                duration = part['rhythm_beats'][i % len(part['rhythm_beats'])]
                
                if chord_symbol == "REST":
                    current_time += duration  # Skip note generation, just add time
                    full_progression_symbols.append("REST")
                    continue  # Move to the next chord symbol
                
                inversion = part['inversions'][i % len(part['inversions'])]
                oct_offset = part['octave_pattern'][i % len(part['octave_pattern'])]
                
                full_progression_symbols.append(chord_symbol)
                
                # --- Get Pitches ---
                try:
                    pitches = get_chord_pitches(chord_symbol, BASE_OCTAVE, oct_offset, inversion)
                except Exception as e:
                    print(f"    Failed to get pitches for '{chord_symbol}': {e}")
                    continue
                
                
                # --- Generate Notes based on Play Style ---
                if part['play_style'] == 'arpeggio':
                    arp_time = 0.0
                    arp_pattern = part['arpeggio_pattern']
                    arp_pattern_len = len(arp_pattern)
                    pitches_len = len(pitches)
                    if pitches_len == 0: continue

                    note_index = 0
                    while arp_time < duration:
                        # Get duration for this arp note
                        note_duration = arp_pattern[note_index % arp_pattern_len]
                        
                        if arp_time + note_duration > duration:
                            note_duration = duration - arp_time # Truncate
                        if note_duration <= 0:
                            break
                            
                        # Cycle through pitches (simple up/down)
                        # e.g., for 4 pitches: 0, 1, 2, 3, 2, 1
                        max_idx = pitches_len - 1
                        total_cycle_len = max(1, max_idx * 2) # e.g., 4 pitches -> 6 steps (0,1,2,3,2,1)
                        if total_cycle_len == 0:
                            pitch_index = 0
                        else:
                            pos_in_cycle = note_index % total_cycle_len
                            if pos_in_cycle > max_idx:
                                pitch_index = max_idx - (pos_in_cycle - max_idx)
                            else:
                                pitch_index = pos_in_cycle
                        
                        note = Note(
                            pitch=pitches[pitch_index],
                            start_time=current_time + arp_time,
                            duration=note_duration * 0.95, # Add separation
                            velocity=random.randint(80, 100)
                        )
                        chord_track.add_element(note)
                        arp_time += note_duration
                        note_index += 1
                
                else: # Default to 'block'
                    note_objects = [
                        Note(pitch=p, start_time=current_time, duration=duration * 0.9, velocity=85)
                        for p in pitches
                    ]
                    chord_track.add_element(Chord(notes=note_objects))
                
                # Advance time
                current_time += duration

    # 3. Finalize and export
    song.add_track(chord_track)
    
    print("=" * 40)
    print(f"✅ Generated Full Progression:")
    print("    " + " - ".join(full_progression_symbols))
    print("=" * 40)

    # Export to MIDI
    exporter = MidiExporter(ticks_per_beat=480)
    try:
        exporter.export(song, OUTPUT_FILENAME)
        print(f"✅ Success! Song exported to '{OUTPUT_FILENAME}'")
    except Exception as e:
        print(f"❌ An error occurred during MIDI export: {e}")
        import traceback
        traceback.print_exc()

# ----------------------------------------------------------------------
# %% --- Script Execution ---
# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()