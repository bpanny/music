# create_test_song.py

from music_elements import Note, Chord, Rest
from track import Track
from composition import Composition
from midi_exporter import MidiExporter

def main():
    # 1. Create musical elements
    # Notes: pitch (0-127), start_time (in beats), duration (in beats), velocity (0-127)

    # Melody notes for Track 1
    melody_notes = [
        Note(pitch=60, start_time=0, duration=1, velocity=100),  # C4
        Note(pitch=62, start_time=1, duration=0.5, velocity=105), # D4
        Note(pitch=64, start_time=1.5, duration=1.5, velocity=110), # E4
        Note(pitch=62, start_time=3, duration=1, velocity=100),  # D4
        Note(pitch=60, start_time=4, duration=2, velocity=90),   # C4
    ]

    # Chord for Track 2
    # Using the add_pitches helper in Chord, assuming all notes in the chord share properties
    # For a simple C Major chord (C4, E4, G4)
    c_major_chord_notes = [
        Note(pitch=60, start_time=0, duration=4, velocity=80), # C4
        Note(pitch=64, start_time=0, duration=4, velocity=80), # E4
        Note(pitch=67, start_time=0, duration=4, velocity=80)  # G4
    ]
    main_chord = Chord(notes=c_major_chord_notes)
    
    # A rest for Track 1
    a_rest = Rest(start_time=6, duration=2) # Rest for 2 beats after the last note

    # Some higher notes for melody track after rest
    melody_notes_part2 = [
        Note(pitch=67, start_time=8, duration=1, velocity=100),   # G4
        Note(pitch=69, start_time=9, duration=1, velocity=105),   # A4
        Note(pitch=71, start_time=10, duration=2, velocity=110),  # B4
    ]


    # 2. Create Tracks
    # Track(name, instrument_program (0-127 for General MIDI), channel (0-15))
    piano_track = Track(name="Piano Melody", instrument_program=0, channel=0, volume=100) # 0: Acoustic Grand Piano
    for note in melody_notes:
        piano_track.add_element(note)
    piano_track.add_element(a_rest)
    for note in melody_notes_part2:
        piano_track.add_element(note)

    strings_track = Track(name="String Pad", instrument_program=48, channel=1, volume=70) # 48: String Ensemble 1
    strings_track.add_element(main_chord)

    # A simple bass line for another track
    bass_track = Track(name="Simple Bass", instrument_program=33, channel=2, volume=90) # 33: Electric Bass (finger)
    bass_notes = [
        Note(pitch=36, start_time=0, duration=2, velocity=90), # C2
        Note(pitch=43, start_time=2, duration=2, velocity=85), # G2
        Note(pitch=36, start_time=4, duration=2, velocity=90), # C2
        Note(pitch=41, start_time=6, duration=2, velocity=80), # F2
        Note(pitch=36, start_time=8, duration=4, velocity=90), # C2
    ]
    for note in bass_notes:
        bass_track.add_element(note)


    # 3. Create Composition
    # Composition(title, tempo (BPM), time_signature (tuple))
    test_song = Composition(title="My Test Song", tempo=120, time_signature=(4, 4))
    test_song.add_track(piano_track)
    test_song.add_track(strings_track)
    test_song.add_track(bass_track)

    # 4. Export to MIDI
    exporter = MidiExporter(ticks_per_beat=480) # Default is 480, can be specified
    output_filename = "my_test_song.mid"
    try:
        exporter.export(test_song, output_filename)
    except Exception as e:
        print(f"An error occurred during MIDI export: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()