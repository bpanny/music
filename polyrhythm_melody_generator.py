# polyrhythm_melody_generator.py

import random
import math
from music_elements import Note, Rest
from track import Track
from composition import Composition
from midi_exporter import MidiExporter
# Import the drum pattern creator to add context
from drum_patterns import create_drum_track_from_pattern 

# ----------------------------------------------------------------------
# %% --- Music Theory Definitions ---
# ----------------------------------------------------------------------

# (PITCH_MAP and SCALES are copied from random_melody_generator.py)
PITCH_MAP = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

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

# (Copied from random_melody_generator.py)
def get_scale_notes(root_note_name: str, scale_type: str, min_octave: int, max_octave: int) -> list[int]:
    if scale_type not in SCALES:
        raise ValueError(f"Scale type '{scale_type}' not defined.")
    root_midi = PITCH_MAP[root_note_name.upper()]
    intervals = SCALES[scale_type]
    note_palette = []
    for octave in range(min_octave, max_octave + 1):
        for interval in intervals:
            pitch = root_midi + (octave * 12) + interval
            if 0 <= pitch <= 127:
                note_palette.append(pitch)
    return sorted(list(set(note_palette)))

# ----------------------------------------------------------------------
# %% --- NEW: Polyrhythm Logic ---
# ----------------------------------------------------------------------

def generate_polyrhythm_onsets(r1_hits: int, r2_hits: int, cycle_duration_beats: float) -> list[float]:
    """
    "Flattens" a polyrhythm (e.g., 3:2) into a single list of
    onset times in beats, all starting from 0.
    
    Example: (3, 2, 4.0) -> 3 hits and 2 hits over 4 beats
             - 3 hits at: 0.0, 1.33, 2.66
             - 2 hits at: 0.0, 2.0
             - Returns: [0.0, 1.33, 2.0, 2.66]
    """
    onsets = set()
    
    # Calculate onsets for rhythm 1
    r1_step = cycle_duration_beats / r1_hits
    for i in range(r1_hits):
        # Use round to avoid floating point precision issues at the boundaries
        onsets.add(round(i * r1_step, 5))
        
    # Calculate onsets for rhythm 2
    r2_step = cycle_duration_beats / r2_hits
    for i in range(r2_hits):
        onsets.add(round(i * r2_step, 5))
        
    return sorted(list(onsets))

# ----------------------------------------------------------------------
# %% --- Generator Configuration ---
# ----------------------------------------------------------------------

CONFIG = {
    "title": "Polyrhythm Melody (3-over-2)",
    "output_filename": "polyrhythm_melody.mid",
    "tempo": 90,
    "time_signature": (4, 4),
    
    # --- Musical Context ---
    "key": "A",
    "scale_type": "pentatonic_minor",
    "total_duration_beats": 32, # 8 measures of 4/4
    "min_octave": 4,
    "max_octave": 6,

    # --- NEW: Polyrhythm Parameters ---
    # The rhythm of the melody will be 3 hits and 2 hits
    # spread across a 4-beat cycle (one measure).
    "polyrhythm": (3, 2),
    "polyrhythm_cycle_beats": 4.0, # 4.0 = one 4/4 measure
    
    # --- Melodic Parameters ---
    # The melody performs a "random walk" on the scale.
    "max_step_size": 3, # Max scale degrees to move up/down per note
    "melody_note_duration": 0.2, # Duration of each melodic note hit
    
    # --- Performance ---
    "instrument_program": 81, # 81: Lead 2 (sawtooth)
    "volume": 100,
}

# ----------------------------------------------------------------------
# %% --- Main Generation Logic (Modified) ---
# ----------------------------------------------------------------------

def main():
    print(f"Generating polyrhythm melody: '{CONFIG['title']}'")

    # 1. Set up note palette and track
    try:
        note_palette = get_scale_notes(
            CONFIG['key'], CONFIG['scale_type'],
            CONFIG['min_octave'], CONFIG['max_octave']
        )
        if not note_palette:
            print("Error: No notes generated.")
            return
    except Exception as e:
        print(f"Error setting up note palette: {e}")
        return

    melody_track = Track(
        name="Polyrhythm Melody",
        instrument_program=CONFIG['instrument_program'],
        volume=CONFIG['volume']
    )
    song = Composition(
        title=CONFIG['title'],
        tempo=CONFIG['tempo'],
        time_signature=CONFIG['time_signature']
    )

    # 2. NEW: Add a simple drum beat for context
    drum_pattern = {
        'kick':  [120, 0, 0, 0,   0, 0, 0, 0,   110, 0, 0, 0,   0, 0, 0, 0], # 1 and 3
        'snare': [0, 0, 0, 0,   100, 0, 0, 0,   0, 0, 0, 0,   100, 0, 0, 0], # 2 and 4
    }
    num_measures = int(CONFIG['total_duration_beats'] / CONFIG['time_signature'][0])
    drum_track = create_drum_track_from_pattern(
        name="Context Beat",
        patterns=drum_pattern,
        measures=num_measures,
        beats_per_measure=CONFIG['time_signature'][0],
        subdivisions_per_beat=4
    )
    song.add_track(drum_track)


    # 3. Generate the melody using the polyrhythm
    
    # Get the "flattened" rhythmic pattern for one cycle
    r1_hits, r2_hits = CONFIG["polyrhythm"]
    cycle_beats = CONFIG["polyrhythm_cycle_beats"]
    
    rhythmic_onsets_one_cycle = generate_polyrhythm_onsets(r1_hits, r2_hits, cycle_beats)
    print(f"Generated {r1_hits}:{r2_hits} polyrhythm onsets per {cycle_beats} beats: {rhythmic_onsets_one_cycle}")

    current_scale_index = len(note_palette) // 2
    note_duration = CONFIG["melody_note_duration"]
    max_step = CONFIG["max_step_size"]
    total_beats = CONFIG["total_duration_beats"]
    
    current_cycle = 0
    generated_note_count = 0
    
    # Loop over each cycle (e.g., each measure)
    while (current_cycle * cycle_beats) < total_beats:
        measure_start_time = current_cycle * cycle_beats
        
        # For each hit in our flattened rhythm...
        for onset_in_cycle in rhythmic_onsets_one_cycle:
            note_start_time = measure_start_time + onset_in_cycle
            
            # Stop if we go over the total song duration
            if note_start_time >= total_beats:
                break
                
            # Get pitch using the random walk logic
            step = random.randint(-max_step, max_step)
            current_scale_index = max(0, min(len(note_palette) - 1, current_scale_index + step))
            pitch = note_palette[current_scale_index]
            
            # Create the note
            velocity = random.randint(90, 115)
            melody_track.add_element(Note(
                pitch=pitch,
                start_time=note_start_time,
                duration=note_duration,
                velocity=velocity
            ))
            generated_note_count += 1
            
        current_cycle += 1

    # 4. Finalize and export
    song.add_track(melody_track)
    
    print("=" * 40)
    print(f"✅ Generated {generated_note_count} notes using the polyrhythm.")
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