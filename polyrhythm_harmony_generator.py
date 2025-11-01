# polyrhythm_harmony_generator.py
#
# This script generates a melody by:
# 1. Creating a complex rhythmic sequence from "flattened" polyrhythms.
# 2. Defining a specific chord progression.
# 3. For each rhythmic hit, it plays a random note from the currently active chord.
#
# This effectively creates a polyrhythmic arpeggiator.

import random
import math
from music_elements import Note, Rest, Chord
from track import Track
from composition import Composition
from midi_exporter import MidiExporter
from drum_patterns import create_drum_track_from_pattern 

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

# This is the core dictionary for your chord specification.
# It maps a symbol to a list of intervals (in semitones).
# Feel free to add any chord voicings you want here!
CHORD_INTERVALS = {
    # Basic Triads
    'maj': [0, 4, 7],
    'm': [0, 3, 7],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'sus4': [0, 5, 7],
    'sus2': [0, 2, 7],
    
    # Sevenths
    '7': [0, 4, 7, 10],         # Dominant 7th
    'maj7': [0, 4, 7, 11],    # Major 7th
    'm7': [0, 3, 7, 10],      # Minor 7th
    'm7b5': [0, 3, 6, 10],    # Half-diminished
    'dim7': [0, 3, 6, 9],     # Fully diminished
    
    # Extensions (Ninth)
    '9': [0, 4, 7, 10, 14],       # Dominant 9
    'm9': [0, 3, 7, 10, 14],      # Minor 9
    'maj9': [0, 4, 7, 11, 14],    # Major 9
    '7b9': [0, 4, 7, 10, 13],     # Dominant flat 9
    '7#9': [0, 4, 7, 10, 15],     # Dominant sharp 9 (Hendrix chord)

    # Extensions (Eleventh & Thirteenth)
    # Note: 11s and 13s usually imply 7s and 9s.
    '11': [0, 4, 7, 10, 14, 17],
    '#11': [0, 4, 7, 11, 14, 18], # Lydian dominant
    'm11': [0, 3, 7, 10, 14, 17],
    '13': [0, 4, 7, 10, 14, 21],   # Dominant 13
    'm13': [0, 3, 7, 10, 14, 21],  # Minor 13
    
    # Add chords
    'add9': [0, 4, 7, 14],
    'm(add9)': [0, 3, 7, 14],
}

# ----------------------------------------------------------------------
# %% --- Helper Functions ---
# ----------------------------------------------------------------------

def get_pitches_for_chord(root_name: str, quality: str, base_octave: int, inversion: int = 0) -> list[int]:
    """
    Converts a chord symbol (e.g., 'C#', 'm7b5', 4) into a list of MIDI pitches.
    """
    if root_name not in PITCH_MAP:
        raise ValueError(f"Root note '{root_name}' not in PITCH_MAP.")
    if quality not in CHORD_INTERVALS:
        raise ValueError(f"Chord quality '{quality}' not in CHORD_INTERVALS. Add it to the dictionary.")
        
    root_pitch = PITCH_MAP[root_name] + (base_octave * 12)
    pitches = [root_pitch + i for i in CHORD_INTERVALS[quality]]
    
    # Apply Inversions
    for i in range(inversion):
        if pitches:
            bass_note = pitches.pop(0)
            pitches.append(bass_note + 12) # Move bass note up one octave
            
    return pitches


def generate_polyrhythm_onsets(rhythms: list[int], cycle_duration_beats: float) -> list[float]:
    """
    "Flattens" multiple polyrhythms (e.g., [3, 2, 5]) into a single
    list of onset times in beats, all starting from 0.
    """
    onsets = set()
    
    for num_hits in rhythms:
        if num_hits <= 0:
            continue
            
        step_duration = cycle_duration_beats / num_hits
        for i in range(num_hits):
            # Use round to avoid floating point precision issues at the boundaries
            onsets.add(round(i * step_duration, 5))
            
    return sorted(list(onsets))

# ----------------------------------------------------------------------
# %% --- Generator Configuration ---
# ----------------------------------------------------------------------

CONFIG = {
    "title": "Polyrhythm Harmony Generator",
    "output_filename": "polyrhythm_harmony.mid",
    "tempo": 110,
    "time_signature": (4, 4),
    "total_duration_beats": 64, # 16 measures of 4/4
    
    # --- Rhythm Configuration ---
    # A list of the number of hits to "flatten" into the rhythm.
    # [3, 2] = 3-against-2
    # [3, 4, 5] = 3:4:5
    "POLYRHYTHM_HITS": [2, 3],
    
    # The duration (in beats) over which the polyrhythm repeats.
    # 4.0 = one 4/4 measure
    "POLYRHYTHM_CYCLE_BEATS": 4.0,
    
    # Duration of each melodic note that is played.
    "MELODY_NOTE_DURATION": 0.25, # 16th note

    # --- Harmony Configuration ---
    # Define the chord progression. The arpeggiator will follow this.
    # 'chord': The root note (e.g., 'C', 'F#', 'Bb')
    # 'quality': The symbol from the CHORD_INTERVALS dictionary
    # 'octave': The base octave for the chord's root
    # 'inversion': 0 = Root, 1 = 1st, 2 = 2nd, etc.
    # 'duration_beats': How long this chord is active.
    "CHORD_PROGRESSION": [
        # Measures 1-2
        { 'chord': 'A', 'quality': 'm9', 'octave': 4, 'inversion': 0, 'duration_beats': 8.0 },
        # Measures 3-4
        { 'chord': 'D', 'quality': '7', 'octave': 4, 'inversion': 1, 'duration_beats': 4.0 },
        { 'chord': 'G', 'quality': 'maj7', 'octave': 4, 'inversion': 0, 'duration_beats': 4.0 },
        # Measures 5-6
        { 'chord': 'C', 'quality': 'maj7', 'octave': 4, 'inversion': 0, 'duration_beats': 8.0 },
        # Measures 7-8
        { 'chord': 'F', 'quality': 'maj7', 'octave': 4, 'inversion': 0, 'duration_beats': 4.0 },
        { 'chord': 'E', 'quality': 'm7b5', 'octave': 4, 'inversion': 1, 'duration_beats': 4.0 },
        
        # Repeat (Measures 9-16)
        { 'chord': 'A', 'quality': 'm9', 'octave': 4, 'inversion': 0, 'duration_beats': 8.0 },
        { 'chord': 'D', 'quality': '7', 'octave': 4, 'inversion': 1, 'duration_beats': 4.0 },
        { 'chord': 'G', 'quality': 'maj7', 'octave': 4, 'inversion': 0, 'duration_beats': 4.0 },
        { 'chord': 'C', 'quality': 'maj7', 'octave': 4, 'inversion': 0, 'duration_beats': 8.0 },
        { 'chord': 'F', 'quality': 'maj7', 'octave': 4, 'inversion': 0, 'duration_beats': 4.0 },
        { 'chord': 'E', 'quality': '7b9', 'octave': 4, 'inversion': 1, 'duration_beats': 4.0 },
    ],

    # --- Track & Performance ---
    "MELODY_INSTRUMENT": 8, # 8: Celesta
    "CHORD_INSTRUMENT": 48, # 48: String Ensemble 1
    "MELODY_VOLUME": 100,
    "CHORD_VOLUME": 60,
    
    # Set to True to also generate a track of block chords for context.
    "ADD_BLOCK_CHORD_TRACK": True,
}

# ----------------------------------------------------------------------
# %% --- Main Generation Logic ---
# ----------------------------------------------------------------------

def main():
    print(f"Generating polyrhythm harmony: '{CONFIG['title']}'")

    # 1. Setup Composition
    song = Composition(
        title=CONFIG['title'],
        tempo=CONFIG['tempo'],
        time_signature=CONFIG['time_signature']
    )

    # 2. Add a simple drum beat for context
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

    # 3. Create Tracks for melody and optional chords
    melody_track = Track(
        name="Polyrhythm Arpeggio",
        instrument_program=CONFIG['MELODY_INSTRUMENT'],
        channel=0, # Melody on Channel 0
        volume=CONFIG['MELODY_VOLUME']
    )
    
    chord_pad_track = None
    if CONFIG['ADD_BLOCK_CHORD_TRACK']:
        chord_pad_track = Track(
            name="Chord Pads",
            instrument_program=CONFIG['CHORD_INSTRUMENT'],
            channel=1, # Chords on Channel 1
            volume=CONFIG['CHORD_VOLUME']
        )

    # 4. Get the "flattened" rhythmic pattern for one cycle
    cycle_beats = CONFIG["POLYRHYTHM_CYCLE_BEATS"]
    rhythmic_onsets_one_cycle = generate_polyrhythm_onsets(
        CONFIG["POLYRHYTHM_HITS"],
        cycle_beats
    )
    print(f"Generated {':'.join(map(str, CONFIG['POLYRHYTHM_HITS']))} polyrhythm onsets "
          f"per {cycle_beats} beats: {rhythmic_onsets_one_cycle}")

    # 5. --- Main Generation Loop ---
    generated_note_count = 0
    current_cycle = 0
    total_beats = CONFIG["total_duration_beats"]
    note_duration = CONFIG["MELODY_NOTE_DURATION"]
    
    # -- Harmony Progression State --
    progression = CONFIG['CHORD_PROGRESSION']
    progression_index = 0
    current_chord = progression[progression_index]
    current_chord_start_time = 0.0
    current_chord_end_time = current_chord['duration_beats']
    current_pitches = get_pitches_for_chord(
        current_chord['chord'], current_chord['quality'],
        current_chord['octave'], current_chord['inversion']
    )
    
    print(f"Beat 0.0: Starting with chord {current_chord['chord']}{current_chord['quality']} "
          f"(Pitches: {current_pitches})")

    # Add the first block chord
    if chord_pad_track:
        chord_pad_track.add_element(Chord(notes=[
            Note(p, current_chord_start_time, current_chord['duration_beats'], 80) for p in current_pitches
        ]))

    # Loop over each rhythmic cycle (e.g., each measure)
    while (current_cycle * cycle_beats) < total_beats:
        measure_start_time = current_cycle * cycle_beats
        
        # For each hit in our flattened rhythm...
        for onset_in_cycle in rhythmic_onsets_one_cycle:
            note_start_time = measure_start_time + onset_in_cycle
            
            if note_start_time >= total_beats:
                break
            
            # --- Check if the chord has changed ---
            if note_start_time >= current_chord_end_time:
                progression_index += 1
                if progression_index >= len(progression):
                    print("Reached end of progression.")
                    break # End of progression
                
                # Load the new chord
                current_chord = progression[progression_index]
                current_chord_start_time = current_chord_end_time
                current_chord_end_time += current_chord['duration_beats']
                
                try:
                    current_pitches = get_pitches_for_chord(
                        current_chord['chord'], current_chord['quality'],
                        current_chord['octave'], current_chord['inversion']
                    )
                    print(f"Beat {current_chord_start_time}: Changing to chord "
                          f"{current_chord['chord']}{current_chord['quality']} (Pitches: {current_pitches})")
                    
                    # Add the block chord for this new section
                    if chord_pad_track:
                        chord_pad_track.add_element(Chord(notes=[
                            Note(p, current_chord_start_time, current_chord['duration_beats'], 80) for p in current_pitches
                        ]))
                        
                except Exception as e:
                    print(f"Error parsing chord {current_chord}: {e}")
                    break
            
            # --- Select a note from the active chord ---
            if not current_pitches:
                continue # Skip if chord has no pitches

            pitch = random.choice(current_pitches)
            velocity = random.randint(90, 115)
            
            melody_track.add_element(Note(
                pitch=pitch,
                start_time=note_start_time,
                duration=note_duration,
                velocity=velocity
            ))
            generated_note_count += 1
            
        current_cycle += 1

    # 6. Finalize and export
    song.add_track(melody_track)
    if chord_pad_track:
        song.add_track(chord_pad_track)
    
    print("=" * 40)
    print(f"✅ Generated {generated_note_count} arpeggio notes.")
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