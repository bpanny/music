# random_chord_generator.py

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
    'minor_natural': [0, 2, 3, 5, 7, 8, 10]
}

# Diatonic chord qualities for each scale degree (1-7)
DIATONIC_QUALITIES = {
    'major': ['maj', 'min', 'min', 'maj', 'maj7', 'min', 'dim'], # V is dom7
    'minor_natural': ['min', 'dim', 'maj', 'min', 'min', 'maj', 'maj']
}

# Chord voicings (intervals from root)
CHORD_VOICINGS = {
    'maj': [0, 4, 7], 'min': [0, 3, 7], 'dim': [0, 3, 6],
    'maj7': [0, 4, 7, 10], # Dominant 7th
}

# ----------------------------------------------------------------------
# %% --- Helper Functions ---
# ----------------------------------------------------------------------

def get_diatonic_chords(root_name: str, scale_type: str) -> list[str]:
    """Generates the 7 diatonic chord symbols for a given key and scale."""
    root_val = PITCH_MAP[root_name.upper()]
    intervals = SCALES[scale_type]
    qualities = DIATONIC_QUALITIES[scale_type]
    chords = []
    for i in range(7):
        note_val = (root_val + intervals[i]) % 12
        note_name = NOTE_NAMES[note_val]
        chords.append(f"{note_name}{qualities[i]}")
    return chords

def get_chord_pitches(chord_symbol: str, base_octave: int, inversion: int = 0) -> list[int]:
    """Converts a chord symbol into a list of MIDI pitches, applying inversion."""
    if len(chord_symbol) > 1 and (chord_symbol[1] == '#' or chord_symbol[1] == 'b'):
        root_name = chord_symbol[0:2]
        quality = chord_symbol[2:]
    else:
        root_name = chord_symbol[0]
        quality = chord_symbol[1:]
    if quality not in CHORD_VOICINGS:
        quality = 'maj'
    
    root_pitch = PITCH_MAP[root_name] + (base_octave * 12)
    pitches = [root_pitch + i for i in CHORD_VOICINGS[quality]]
    
    for i in range(inversion):
        if pitches:
            bass_note = pitches.pop(0)
            pitches.append(bass_note + 12)
    return pitches

# ----------------------------------------------------------------------
# %% --- Generator Configuration ---
# ----------------------------------------------------------------------

CONFIG = {
    "title": "Random C Major Progression",
    "output_filename": "random_progression.mid",
    "tempo": 90,
    "time_signature": (4, 4),
    
    # --- Musical Context ---
    "key": "G",
    "scale_type": "minor_natural",
    "total_duration_beats": 32, # Total length (e.g., 32 beats = 8 measures of 4/4)

    # --- Chord Selection Weights ---
    # Assigns a probability weight for choosing each scale degree (1-7).
    # Higher numbers are more likely.
    # For Major:  [ I,   ii,  iii, IV,  V,   vi,  vii ]
    "chord_weights": [1, 1, 1, 1,  1, 1, 1],

    # --- Rhythm ---
    # A list of chord durations (in beats) to cycle through.
    # [4] = All chords are whole notes
    # [2, 2, 4] = half, half, whole, then repeat
    "rhythm_beats": [1, 1, 1, 0.5, 0.5],

    # --- Voicing & Performance ---
    "base_octave": 4,
    "instrument_program": 0, # 0: Acoustic Grand Piano
    "play_style": "block", # 'block' or 'arpeggio'
    "arpeggio_pattern": [0.5, 0.5, 0.5, 0.5], # Durations for arpeggio notes
    "use_random_inversions": True, # If true, randomly picks root or 1st inv.
}

# ----------------------------------------------------------------------
# %% --- Main Generation Logic ---
# ----------------------------------------------------------------------

def main():
    """Generates and exports the randomized chord progression."""
    print(f"Generating random progression: '{CONFIG['title']}'")

    # 1. Set up diatonic chords and track
    try:
        diatonic_chords = get_diatonic_chords(CONFIG['key'], CONFIG['scale_type'])
        degrees = list(range(1, 8)) # [1, 2, 3, 4, 5, 6, 7]
        print(f"Diatonic chords in {CONFIG['key']} {CONFIG['scale_type']}: {', '.join(diatonic_chords)}")
    except Exception as e:
        print(f"Error setting up chords: {e}")
        return

    track = Track(
        name="Random Chords",
        instrument_program=CONFIG['instrument_program'],
    )
    song = Composition(
        title=CONFIG['title'],
        tempo=CONFIG['tempo'],
        time_signature=CONFIG['time_signature']
    )

    # 2. Generate the chord sequence randomly
    current_time = 0.0
    rhythm_index = 0
    generated_symbol_list = []

    print("Generating notes...")
    while current_time < CONFIG['total_duration_beats']:
        # --- Determine duration for this chord ---
        duration = CONFIG['rhythm_beats'][rhythm_index % len(CONFIG['rhythm_beats'])]
        rhythm_index += 1
        # Ensure the final chord doesn't overshoot the total duration
        if current_time + duration > CONFIG['total_duration_beats']:
            duration = CONFIG['total_duration_beats'] - current_time
        if duration <= 0:
            break

        # --- Randomly select a chord degree based on weights ---
        chosen_degree = random.choices(degrees, weights=CONFIG['chord_weights'], k=1)[0]
        chord_symbol = diatonic_chords[chosen_degree - 1]
        generated_symbol_list.append(chord_symbol)

        # --- Get pitches with optional random inversion ---
        inversion = random.randint(0, 1) if CONFIG['use_random_inversions'] else 0
        pitches = get_chord_pitches(chord_symbol, CONFIG['base_octave'], inversion)
        
        # --- Generate notes based on play style ---
        if CONFIG['play_style'] == 'arpeggio':
            arp_time = 0.0
            arp_pattern = CONFIG['arpeggio_pattern']
            note_index = 0
            while arp_time < duration:
                note_duration = arp_pattern[note_index % len(arp_pattern)]
                if arp_time + note_duration > duration:
                    note_duration = duration - arp_time
                if note_duration <= 0:
                    break
                
                pitch = pitches[note_index % len(pitches)]
                track.add_element(Note(
                    pitch=pitch,
                    start_time=current_time + arp_time,
                    duration=note_duration,
                    velocity=random.randint(75, 95)
                ))
                arp_time += note_duration
                note_index += 1
        else: # Block chords
            notes = [Note(p, current_time, duration, 85) for p in pitches]
            track.add_element(Chord(notes=notes))

        current_time += duration

    # 3. Finalize and export
    song.add_track(track)
    
    print("=" * 40)
    print(f"✅ Generated Random Progression:")
    print("   " + " - ".join(generated_symbol_list))
    print("=" * 40)

    exporter = MidiExporter(ticks_per_beat=480)
    try:
        exporter.export(song, CONFIG['output_filename'])
        print(f"✅ Success! Song exported to '{CONFIG['output_filename']}'")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

# ----------------------------------------------------------------------
# %% --- Script Execution ---
# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()