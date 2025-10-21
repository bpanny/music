# generative_music_creator.py

import random
from music_elements import Note, Chord, Rest
from track import Track
from composition import Composition
from midi_exporter import MidiExporter

# --- GLOBAL MAPPINGS ---
# Maps note names to their MIDI pitch value in octave 0
PITCH_MAP = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 
             'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}

# Defines scales as intervals from the root note (in semitones)
SCALES = {
    'major': [0, 2, 4, 5, 7, 9, 11],
    'minor_natural': [0, 2, 3, 5, 7, 8, 10],
    'minor_harmonic': [0, 2, 3, 5, 7, 8, 11],
    'pentatonic_major': [0, 2, 4, 7, 9],
    'blues': [0, 3, 5, 6, 7, 10]
}

#======================================================================#
#               🎵 EDIT YOUR SONG PARAMETERS HERE 🎵                 #
#======================================================================#
SONG_CONFIG = {
    "title": "My Generative Song",
    "tempo": 100,
    "time_signature": (4, 4),
    "duration_beats": 64,  # Total length of the song in beats (e.g., 16 measures of 4/4 is 64 beats)
    "output_filename": "generative_song.mid",
    
    # --- Musical Key and Scale ---
    "key": "C",
    "scale_type": "major", # Options: 'major', 'minor_natural', 'minor_harmonic', 'pentatonic_major', 'blues'
    
    # --- Melody Track Configuration ---
    "melody": {
        "instrument_program": 80,  # 80: Lead 1 (square)
        "channel": 0,
        "volume": 100,
        "octave_range": (4, 5),    # Generate notes in octaves 4 and 5
        "start_beat": 0,
        
        # Define a sequence of high-level actions to guide the melody
        # ('WALK', steps, direction): Move stepwise up/down the scale. direction=1 for up, -1 for down.
        # ('JUMP', steps, max_jump_size): Jump around the scale randomly for a number of steps.
        # ('REST', steps): Add a number of rests.
        "actions": [
            ('WALK', 8, 1),      # Walk up the scale for 8 notes
            ('JUMP', 4, 5),      # Jump around for 4 notes (max jump size of 5 scale degrees)
            ('WALK', 8, -1),     # Walk down for 8 notes
            ('REST', 2),         # Rest for 2 rhythmic steps
            ('JUMP', 8, 3),      # Jump around for 8 notes (smaller jumps)
        ],

        # The pool of possible note durations (in beats) to choose from randomly
        "rhythm_choices": [0.5, 0.5, 0.5, 1.0, 1.0, 1.5], # More 0.5s makes it more likely
        "rest_duration": 1.0, # Duration of a single rest step
    },
    
    # --- Chords Track Configuration ---
    "chords": {
        "instrument_program": 48, # 48: String Ensemble 1
        "channel": 1,
        "volume": 70,
        "octave": 3,
        "rhythm_beats": 4, # How often the chord changes (e.g., 4 beats = 1 whole note chord per measure)
        "voicing_intervals": [0, 2, 4], # Build chords using the 1st, 3rd, and 5th notes from the scale root (a triad)
    },
    
    # --- Bass Track Configuration ---
    "bass": {
        "instrument_program": 33, # 33: Electric Bass (finger)
        "channel": 2,
        "volume": 90,
        "octave_offset": -2, # Play the chord root note, but down this many octaves
        "rhythm_pattern": [0, 2], # Play on the 0th and 2nd beat of each chord change
    }
}
#======================================================================#
#                        END OF CONFIGURATION                          #
#======================================================================#


def get_scale_notes(root_note_name, scale_type, octave_range):
    """Generates a list of all valid MIDI pitches for a given scale and octave range."""
    root_midi = PITCH_MAP[root_note_name.upper()]
    intervals = SCALES[scale_type]
    
    scale_notes = []
    for octave in range(octave_range[0], octave_range[1] + 1):
        for interval in intervals:
            scale_notes.append(root_midi + (octave * 12) + interval)
            
    return sorted(list(set(scale_notes)))

def generate_melody_track(config, scale_notes, total_duration):
    """Generates a melody track based on a sequence of high-level actions."""
    cfg = config['melody']
    track = Track(name="Melody", instrument_program=cfg['instrument_program'], channel=cfg['channel'], volume=cfg['volume'])
    
    current_time = float(cfg['start_beat'])
    # Start the melody in the middle of the available notes
    current_scale_index = len(scale_notes) // 2 

    for action in cfg['actions']:
        action_type = action[0]
        steps = action[1]
        
        for _ in range(steps):
            if current_time >= total_duration:
                break

            if action_type == 'WALK':
                direction = action[2]
                duration = random.choice(cfg['rhythm_choices'])
                
                current_scale_index += direction
                # Clamp index to stay within the list bounds
                current_scale_index = max(0, min(len(scale_notes) - 1, current_scale_index))
                
                pitch = scale_notes[current_scale_index]
                track.add_element(Note(pitch, current_time, duration, velocity=random.randint(90, 115)))
                current_time += duration

            elif action_type == 'JUMP':
                max_jump = action[2]
                duration = random.choice(cfg['rhythm_choices'])

                jump_amount = random.randint(-max_jump, max_jump)
                current_scale_index += jump_amount
                current_scale_index = max(0, min(len(scale_notes) - 1, current_scale_index))

                pitch = scale_notes[current_scale_index]
                track.add_element(Note(pitch, current_time, duration, velocity=random.randint(95, 120)))
                current_time += duration
                
            elif action_type == 'REST':
                duration = cfg['rest_duration']
                track.add_element(Rest(current_time, duration))
                current_time += duration

    return track


def generate_chord_and_bass_tracks(config, scale_notes, total_duration):
    """Generates diatonic chords and a corresponding bassline."""
    chord_cfg = config['chords']
    bass_cfg = config['bass']
    
    chord_track = Track("Chords", chord_cfg['instrument_program'], chord_cfg['channel'], volume=chord_cfg['volume'])
    bass_track = Track("Bass", bass_cfg['instrument_program'], bass_cfg['channel'], volume=bass_cfg['volume'])
    
    # Use a smaller pool of notes for the chord roots to keep them sounding grounded
    chord_root_notes = get_scale_notes(config['key'], config['scale_type'], (chord_cfg['octave'], chord_cfg['octave']))
    
    current_time = 0.0
    while current_time < total_duration:
        duration = chord_cfg['rhythm_beats']
        
        # 1. Choose a root note for the chord from the scale
        root_note_index = random.randrange(len(chord_root_notes))
        
        # 2. Build the chord notes using diatonic intervals (from the main scale_notes list)
        chord_pitches = []
        try:
            # Find the root note in the full scale list to build the chord from
            scale_start_index = scale_notes.index(chord_root_notes[root_note_index])
            for interval in chord_cfg['voicing_intervals']:
                chord_pitches.append(scale_notes[scale_start_index + interval])
        except (ValueError, IndexError):
            # If we go out of bounds, just repeat the root note
            chord_pitches.append(chord_root_notes[root_note_index])

        # 3. Create the Chord object
        chord_notes = [Note(p, current_time, duration, velocity=80) for p in chord_pitches]
        chord_track.add_element(Chord(notes=chord_notes))
        
        # 4. Create the corresponding Bass notes
        bass_root_pitch = chord_notes[0].pitch + (bass_cfg['octave_offset'] * 12)
        for beat_offset in bass_cfg['rhythm_pattern']:
            if beat_offset < duration:
                bass_note = Note(
                    pitch=bass_root_pitch,
                    start_time=current_time + beat_offset,
                    duration=1, # simple duration, can be customized
                    velocity=random.randint(85, 100)
                )
                bass_track.add_element(bass_note)
        
        current_time += duration
        
    return chord_track, bass_track


def main():
    """Main function to generate and export the song."""
    print(f"Generating song '{SONG_CONFIG['title']}'...")
    
    # 1. Create the palette of notes based on key and scale
    all_scale_notes = get_scale_notes(
        SONG_CONFIG['key'], 
        SONG_CONFIG['scale_type'], 
        SONG_CONFIG['melody']['octave_range']
    )
    
    # 2. Generate Tracks
    print("Generating melody...")
    melody_track = generate_melody_track(SONG_CONFIG, all_scale_notes, SONG_CONFIG['duration_beats'])
    
    print("Generating chords and bassline...")
    chord_track, bass_track = generate_chord_and_bass_tracks(SONG_CONFIG, all_scale_notes, SONG_CONFIG['duration_beats'])

    # 3. Create Composition
    song = Composition(
        title=SONG_CONFIG['title'],
        tempo=SONG_CONFIG['tempo'],
        time_signature=SONG_CONFIG['time_signature']
    )
    song.add_track(melody_track)
    song.add_track(chord_track)
    song.add_track(bass_track)
    
    # 4. Export to MIDI
    exporter = MidiExporter(ticks_per_beat=480)
    output_filename = SONG_CONFIG['output_filename']
    try:
        exporter.export(song, output_filename)
        print(f"✅ Success! Song exported to '{output_filename}'")
    except Exception as e:
        print(f"❌ An error occurred during MIDI export: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()