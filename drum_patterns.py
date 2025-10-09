# drum_patterns.py

from music_elements import Note
from track import Track

# General MIDI Drum Map (common sounds, all on Channel 9 (0-indexed))
# Pitches for common drum sounds
GM_DRUM_MAP = {
    'kick': 36,         # Bass Drum 1
    'acoustic_kick': 35,# Acoustic Bass Drum
    'side_stick': 37,
    'snare': 38,        # Acoustic Snare
    'electric_snare': 40,
    'clap': 39,
    'closed_hat': 42,
    'pedal_hat': 44,
    'open_hat': 46,
    'low_tom': 45,
    'mid_tom': 47,      # Low-Mid Tom
    'high_tom': 50,
    'crash1': 49,
    'crash2': 57,
    'ride1': 51,
    'ride_bell': 53,
    'cowbell': 56,
}

# Standard MIDI Drum Channel (0-indexed)
DRUM_CHANNEL = 9

def create_drum_track_from_pattern(
    name = "Drums",
    patterns = {},
    measures = 1,
    beats_per_measure = 4,
    subdivisions_per_beat = 4,
    default_velocity = 100,
    note_duration = 0.1  # Short duration for drum hits
) -> Track:
    """
    Creates a drum Track from a pattern definition.

    Args:
        name: Name of the drum track.
        patterns: A dictionary where keys are drum names (from GM_DRUM_MAP)
                  and values are lists representing the pattern for one measure.
                  The list length should be beats_per_measure * subdivisions_per_beat.
                  A value > 0 in the list means a hit with that velocity,
                  0 or None means no hit.
                  Example: {'kick': [100, 0, 0, 0, 100, 0, 0, 0, ...], 'snare': [0,0,0,0,100,0,0,0,...]}
        measures: Number of times to repeat the one-measure pattern.
        beats_per_measure: Typically 4 for 4/4 time.
        subdivisions_per_beat: How many slots per beat (e.g., 4 for 16th notes).
        default_velocity: Velocity used if pattern value is 1 (can be overridden by pattern value if >1).
        note_duration: Duration of each drum note (usually short).

    Returns:
        A Track object populated with drum notes.
    """
    if not (0 <= default_velocity <= 127):
        raise ValueError("Default velocity must be between 0 and 127.")

    drum_track = Track(name=name, instrument_program=0, channel=DRUM_CHANNEL) # Program change is often ignored for drums
                                                                            # Channel 9 is key.
    
    total_subdivisions_per_measure = beats_per_measure * subdivisions_per_beat
    time_per_subdivision = 1.0 / subdivisions_per_beat # In beats

    for measure in range(measures):
        measure_start_time = measure * beats_per_measure
        for drum_name, pattern_list in patterns.items():
            if drum_name not in GM_DRUM_MAP:
                print(f"Warning: Drum name '{drum_name}' not found in GM_DRUM_MAP. Skipping.")
                continue
            
            pitch = GM_DRUM_MAP[drum_name]

            if len(pattern_list) != total_subdivisions_per_measure:
                raise ValueError(
                    f"Pattern length for '{drum_name}' ({len(pattern_list)}) "
                    f"does not match total subdivisions per measure ({total_subdivisions_per_measure})."
                )

            for i, hit_velocity_marker in enumerate(pattern_list):
                if hit_velocity_marker and hit_velocity_marker > 0:
                    current_beat_in_measure = i / subdivisions_per_beat
                    start_time = measure_start_time + current_beat_in_measure
                    
                    velocity = default_velocity
                    if isinstance(hit_velocity_marker, (int, float)) and hit_velocity_marker > 1:
                        # Allow pattern to specify velocity directly if > 1
                        velocity = min(127, int(hit_velocity_marker)) 
                    
                    note = Note(
                        pitch=pitch,
                        start_time=start_time,
                        duration=note_duration,
                        velocity=velocity
                    )
                    drum_track.add_element(note)
    
    return drum_track