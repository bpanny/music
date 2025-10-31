# random_melody_generator.py

import random
from music_elements import Note, Rest
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

# Scale definitions (intervals in semitones)
SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor_natural': [0, 2, 3, 5, 7, 8, 10],
    'minor_harmonic': [0, 2, 3, 5, 7, 8, 11],
    'pentatonic_major': [0, 2, 4, 7, 9],
    'pentatonic_minor': [0, 3, 5, 7, 10]
}

# ----------------------------------------------------------------------
# %% --- Helper Functions ---
# ----------------------------------------------------------------------

def get_scale_notes(root_note_name: str, scale_type: str, min_octave: int, max_octave: int) -> list[int]:
    """
    Generates a sorted list of all valid MIDI pitches for a given scale and octave range.
    """
    if scale_type not in SCALES:
        raise ValueError(f"Scale type '{scale_type}' not defined.")
        
    root_midi = PITCH_MAP[root_note_name.upper()]
    intervals = SCALES[scale_type]
    
    note_palette = []
    for octave in range(min_octave, max_octave + 1):
        for interval in intervals:
            pitch = root_midi + (octave * 12) + interval
            if 0 <= pitch <= 127: # Ensure valid MIDI range
                note_palette.append(pitch)
            
    return sorted(list(set(note_palette))) # Return unique, sorted pitches

# ----------------------------------------------------------------------
# %% --- Generator Configuration ---
# ----------------------------------------------------------------------

CONFIG = {
    "title": "My Random Melody",
    "output_filename": "random_melody.mid",
    "tempo": 120,
    "time_signature": (4, 4),
    
    # --- Musical Context ---
    "key": "G",
    "scale_type": "pentatonic_minor", # e.g., 'major', 'minor_natural', 'pentatonic_minor'
    "total_duration_beats": 32, # Total length (e.g., 32 beats = 8 measures of 4/4)
    "min_octave": 4,
    "max_octave": 6,

    # --- Generative Parameters ---
    # The melody performs a "random walk" on the scale.
    # This is the max number of scale degrees it can move up or down in one step.
    # 1 = purely stepwise motion. 3 = allows small leaps.
    "max_step_size": 2,

    # --- Rhythm ---
    # A list of note durations (in beats) to choose from randomly.
    # 0.25 = 16th, 0.5 = 8th, 1.0 = quarter
    "rhythm_choices": [0.25, 0.25, 0.5, 0.5, 0.5, 0.75, 1.0],
    
    # --- Rests ---
    # The chance (0.0 to 1.0) that any given event will be a rest instead of a note.
    "rest_chance": 0.15,
    # A list of rest durations (in beats) to choose from.
    "rest_duration_choices": [0.25, 0.5],

    # --- Performance ---
    "instrument_program": 80, # 80: Lead 1 (square)
    "volume": 100,
}

# ----------------------------------------------------------------------
# %% --- Main Generation Logic ---
# ----------------------------------------------------------------------

def main():
    """Generates and exports the randomized melody."""
    print(f"Generating random melody: '{CONFIG['title']}'")

    # 1. Set up note palette and track
    try:
        note_palette = get_scale_notes(
            CONFIG['key'],
            CONFIG['scale_type'],
            CONFIG['min_octave'],
            CONFIG['max_octave']
        )
        if not note_palette:
            print("Error: No notes generated. Check key and octave range.")
            return
        print(f"Generated {len(note_palette)} notes in palette (from {note_palette[0]} to {note_palette[-1]}).")
    except Exception as e:
        print(f"Error setting up note palette: {e}")
        return

    track = Track(
        name="Random Melody",
        instrument_program=CONFIG['instrument_program'],
        volume=CONFIG['volume']
    )
    song = Composition(
        title=CONFIG['title'],
        tempo=CONFIG['tempo'],
        time_signature=CONFIG['time_signature']
    )

    # 2. Generate the random melody
    current_time = 0.0
    # Start the melody in the middle of the available note palette
    current_scale_index = len(note_palette) // 2
    generated_note_count = 0

    print("Generating notes...")
    while current_time < CONFIG['total_duration_beats']:
        
        # --- Check if this event should be a rest ---
        if random.random() < CONFIG['rest_chance'] and current_time > 0:
            duration = random.choice(CONFIG['rest_duration_choices'])
            if current_time + duration > CONFIG['total_duration_beats']:
                duration = CONFIG['total_duration_beats'] - current_time
            if duration > 0:
                track.add_element(Rest(start_time=current_time, duration=duration))
                current_time += duration
            continue # Skip to the next event

        # --- If not a rest, generate a note ---
        
        # 1. Get rhythm
        duration = random.choice(CONFIG['rhythm_choices'])
        if current_time + duration > CONFIG['total_duration_beats']:
            duration = CONFIG['total_duration_beats'] - current_time
        if duration <= 0:
            break

        # 2. Get pitch (random walk)
        step = random.randint(-CONFIG['max_step_size'], CONFIG['max_step_size'])
        current_scale_index += step
        
        # Clamp the index to stay within the bounds of the note_palette
        current_scale_index = max(0, min(len(note_palette) - 1, current_scale_index))
        
        pitch = note_palette[current_scale_index]

        # 3. Create Note
        velocity = random.randint(85, 115)
        note = Note(
            pitch=pitch,
            start_time=current_time,
            duration=duration,
            velocity=velocity
        )
        track.add_element(note)
        
        generated_note_count += 1
        current_time += duration

    # 3. Finalize and export
    song.add_track(track)
    
    print("=" * 40)
    print(f"✅ Generated {generated_note_count} notes over {CONFIG['total_duration_beats']} beats.")
    print("=" * 40)

    exporter = MidiExporter(ticks_per_beat=480)
    try:
        exporter.export(song, CONFIG['output_filename'])
        print(f"✅ Success! Song exported to '{CONFIG['output_filename']}'")
    except Exception as e:
        print(f"❌ An error occurred during export: {e}")

# ----------------------------------------------------------------------
# %% --- Script Execution ---
# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()