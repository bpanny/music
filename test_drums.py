# test_drums.py

from composition import Composition
from midi_exporter import MidiExporter
from drum_patterns import create_drum_track_from_pattern, GM_DRUM_MAP

def main():
    # Define a 1-measure pattern for a 4/4 beat with 16th note subdivisions
    # Each list has 4 beats * 4 subdivisions/beat = 16 slots
    # Value '1' means hit with default_velocity.
    # Value > 1 can mean specific velocity (e.g. 120).
    # Value 0 or None means no hit.

    basic_rock_pattern = {
        'kick':       [120, 0, 0, 0,   0, 0, 0, 0,   110, 0, 0, 0,   0, 0, 0, 0], # Kick on 1 and 3
        'snare':      [0, 0, 0, 0,   100, 0, 0, 0,   0, 0, 0, 0,   100, 0, 0, 0], # Snare on 2 and 4
        'closed_hat': [90, 0, 90, 0,   90, 0, 90, 0,   90, 0, 90, 0,   90, 0, 90, 0], # Eighth note hi-hats
        # 'open_hat':   [0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 70], # Open hat on the last 16th
    }
    
    funky_pattern = {
        'kick':       [120, 0, 80, 0,   0, 100, 0, 70,   110, 0, 0, 0,   0, 90, 0, 0],
        'snare':      [0, 0, 0, 0,   100, 0, 0, 0,   0, 0, 0, 60,   100, 0, 0, 0],
        'closed_hat': [90, 70, 90, 70,  90, 70, 90, 70,  90, 70, 90, 70,  90, 70, 90, 70],
        'open_hat':   [0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 80],
        'clap':       [0, 0, 0, 0,   100, 0, 0, 0,   0, 0, 0, 0,   100, 0, 0, 0], # Layer with snare
    }


    # Create the drum track using the pattern, repeated for 4 measures
    # drum_track = create_drum_track_from_pattern(
    #     patterns=basic_rock_pattern,
    #     measures=4,
    #     beats_per_measure=4,
    #     subdivisions_per_beat=4, # 16th notes
    #     default_velocity=100
    # )

    drum_track = create_drum_track_from_pattern(
        name="Funky Drums",
        patterns=funky_pattern,
        measures=8,
        beats_per_measure=4,
        subdivisions_per_beat=4,
        default_velocity=90
    )

    # Create a composition
    drum_composition = Composition(title="Test Drum Beat", tempo=100, time_signature=(4, 4))
    drum_composition.add_track(drum_track)

    # Export to MIDI
    exporter = MidiExporter()
    output_filename = "test_drum_beat.mid"
    try:
        exporter.export(drum_composition, output_filename)
    except Exception as e:
        print(f"An error occurred during MIDI export: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()