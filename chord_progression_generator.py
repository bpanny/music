# modular_chord_generator.py

import random
from music_elements import Note, Chord
from track import Track
from composition import Composition
from midi_exporter import MidiExporter

# ----------------------------------------------------------------------
# %% --- Music Theory Definitions ---
# ----------------------------------------------------------------------

# Maps note names to their base MIDI pitch value (Octave 0)
PITCH_MAP = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

# 12-tone note names (preferring sharps for simplicity)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Scale definitions (intervals in semitones)
SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor_natural': [0, 2, 3, 5, 7, 8, 10],
    'minor_harmonic': [0, 2, 3, 5, 7, 8, 11]
}

# Diatonic chord qualities for each scale degree (1-7)
DIATONIC_QUALITIES = {
    'major': ['maj', 'min', 'min', 'maj', 'maj7', 'min', 'dim'], # V is dom7
    'minor_natural': ['min', 'dim', 'maj', 'min', 'min', 'maj', 'maj'],
    'minor_harmonic': ['min', 'dim', 'maj(aug)', 'min', 'maj7', 'maj', 'dim'] # V is dom7
}

# Simple triad/seventh voicings (intervals from root)
CHORD_VOICINGS = {
    'maj': [0, 4, 7],
    'min': [0, 3, 7],
    'dim': [0, 3, 6],
    'maj(aug)': [0, 4, 8], # Augmented
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'maj7': [0, 4, 7, 10], # Dominant 7th
    'min7b5': [0, 3, 6, 10]
}

# ----------------------------------------------------------------------
# %% --- Helper Functions ---
# ----------------------------------------------------------------------

def get_diatonic_chords(root_name: str, scale_type: str) -> list[str]:
    """
    Generates the 7 diatonic chord symbols for a given key and scale.
    e.g., ('C', 'major') -> ['Cmaj', 'Dmin', 'Emin', 'Fmaj', 'Gmaj7', 'Amin', 'Bdim']
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
    # 1. Parse Symbol
    if len(chord_symbol) > 1 and (chord_symbol[1] == '#' or chord_symbol[1] == 'b'):
        root_name = chord_symbol[0:2]
        quality = chord_symbol[2:]
    else:
        root_name = chord_symbol[0]
        quality = chord_symbol[1:]
        
    if quality not in CHORD_VOICINGS:
        print(f"Warning: Quality '{quality}' not in CHORD_VOICINGS. Using 'maj'.")
        quality = 'maj'
        
    if root_name not in PITCH_MAP:
        raise ValueError(f"Root note '{root_name}' not in PITCH_MAP.")

    # 2. Get root position pitches
    root_pitch = PITCH_MAP[root_name] + ((base_octave + octave_offset) * 12)
    intervals = CHORD_VOICINGS[quality]
    pitches = [root_pitch + i for i in intervals]
    
    # 3. Apply Inversions
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
        "part_name": "Verse",
        "key": "A",
        "scale_type": "minor_natural",
        "progression_degrees": [1, 6, 3, 7, 3, 6, 1, 6, 3, 7],
        "inversions": [0, 0, 1, 2],       # 0=root, 1=1st inv. Loops.
        "octave_pattern": [0, 0, 1, 0],   # Octave offset per chord. Loops.
        "rhythm_beats": [1, 1, 1, 0.5, 0.5, 1, 1, 0.5, 0.5, 1],          # Duration per chord. Loops.
        "play_style": "block",        # 'block' or 'arpeggio'
        "arpeggio_pattern": [0.5, 0.5, 0.5, 0.5], # Note durations for arpeggio
        "num_loops": 2
    },
    {
        "part_name": "Verse 2",
        "key": "F",
        "scale_type": "minor_harmonic",
        "progression_degrees": [6, 3, 7, 3, 6, 1, 6, 3, 7, 1],
        "inversions": [1, 2, 1, 0],       # 0=root, 1=1st inv. Loops.
        "octave_pattern": [0, 0, 1, 0],   # Octave offset per chord. Loops.
        "rhythm_beats": [1, 1, 1, 0.5, 0.5, 1, 1, 0.5, 0.5, 1],          # Duration per chord. Loops.
        "play_style": "block",        # 'block' or 'arpeggio'
        "arpeggio_pattern": [0.5, 0.5, 0.5, 0.5], # Note durations for arpeggio
        "num_loops": 2
    }
]

# --- Global Song Settings ---
SONG_TITLE = "Modular Progression"
OUTPUT_FILENAME = "modular_progression.mid"
TEMPO = 110
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
        print(f"--- Generating Part: {part_name} ({part['key']} {part['scale_type']}) ---")
        
        try:
            diatonic_chords = get_diatonic_chords(part['key'], part['scale_type'])
            print(f"    Diatonic chords: {', '.join(diatonic_chords)}")
        except Exception as e:
            print(f"    Error setting up chords for {part_name}: {e}")
            continue

        for _ in range(part['num_loops']):
            for i, degree in enumerate(part['progression_degrees']):
                if not (1 <= degree <= 7):
                    print(f"    Invalid degree {degree}, skipping.")
                    continue
                
                # --- Get Chord Properties ---
                chord_symbol = diatonic_chords[degree - 1]
                duration = part['rhythm_beats'][i % len(part['rhythm_beats'])]
                inversion = part['inversions'][i % len(part['inversions'])]
                oct_offset = part['octave_pattern'][i % len(part['octave_pattern'])]
                
                full_progression_symbols.append(chord_symbol)
                
                # --- Get Pitches ---
                pitches = get_chord_pitches(chord_symbol, BASE_OCTAVE, oct_offset, inversion)
                
                # --- Generate Notes based on Play Style ---
                if part['play_style'] == 'arpeggio':
                    arp_time = 0.0
                    arp_pattern = part['arpeggio_pattern']
                    while arp_time < duration:
                        for j, note_duration in enumerate(arp_pattern):
                            if arp_time + note_duration > duration:
                                note_duration = duration - arp_time # Truncate
                            if note_duration <= 0:
                                break
                                
                            # Cycle through pitches [0, 1, 2, 1, 0, 1, 2, 1...]
                            pitch_index = (j % (len(pitches) + max(0, len(pitches)-2)))
                            if pitch_index >= len(pitches):
                                pitch_index = len(pitches) - 2 - (pitch_index - len(pitches))
                                
                            note = Note(
                                pitch=pitches[pitch_index],
                                start_time=current_time + arp_time,
                                duration=note_duration,
                                velocity=random.randint(80, 100)
                            )
                            chord_track.add_element(note)
                            arp_time += note_duration
                
                else: # Default to 'block'
                    note_objects = [
                        Note(pitch=p, start_time=current_time, duration=duration, velocity=85)
                        for p in pitches
                    ]
                    chord_track.add_element(Chord(notes=note_objects))
                
                # Advance time
                current_time += duration

    # 3. Finalize and export
    song.add_track(chord_track)
    
    print("=" * 40)
    print(f"✅ Generated Full Progression:")
    print("   " + " - ".join(full_progression_symbols))
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