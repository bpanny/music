# Import necessary functions from musicpy
from musicpy import *
import random

# This script will create a simple generative piece in C Major.

## --- 1. Define Basic Musical Elements ---

# Let's define a scale to draw notes from.
# We'll use C Major.
key_note = 'C4' # C in the 4th octave as our starting point for the scale
current_scale_notes = scale(key_note, mode='major') # Get notes of C major scale for one octave

# You can print the scale to see the notes:
# print(f"Notes in C Major scale starting from {key_note}: {current_scale_notes.notes}")
# Output example: [C4, D4, E4, F4, G4, A4, B4]

## --- 2. Generate a Simple Melody ---

# Let's generate a short melody using random notes from our C Major scale
# and a predefined set of rhythms.

melody_notes = []
melody_durations = [1/4, 1/8, 1/8, 1/4, 1/2] # Beat durations (quarter, eighth, half)
num_melody_notes = 8 # Let's create 8 notes for our melody

for i in range(num_melody_notes):
    # Randomly pick a note from the scale
    # musicpy scales are 1-indexed for get_degree, or you can directly access .notes (0-indexed)
    random_degree = random.randint(1, len(current_scale_notes))
    note_pitch = current_scale_notes.get(str(random_degree)) # .get() can take degree strings

    # For simplicity, let's use the first note object if get() returns a chord/list
    if isinstance(note_pitch, (list, chord)):
        note_pitch = note_pitch[0]

    # Randomly pick a duration for this note
    # We'll cycle through melody_durations for simplicity here
    duration = melody_durations[i % len(melody_durations)]

    # Create a musicpy note (pitch, duration)
    # Note: musicpy's core note object is created via C(), N(), or note().
    # For a sequence, we often build a chord object where each "note" in the chord
    # is played sequentially.
    # Let's make a single note chord for each melodic element.
    # Note names like 'C4', 'D#5', 'Gb3' are directly usable.
    # We can also adjust octave here if needed.
    # Example: current_scale_notes.notes[random.randint(0, len(current_scale_notes.notes)-1)]
    # The .get() method is convenient for scale degrees.

    melodic_fragment = note_pitch % duration # Set duration for the note
    melody_notes.append(melodic_fragment)

# Combine the melodic fragments into a single 'chord' object (which represents a sequence here)
# The `+` operator for chords in musicpy concatenates them sequentially.
generative_melody = None
if melody_notes:
    generative_melody = melody_notes[0]
    for i in range(1, len(melody_notes)):
        generative_melody += melody_notes[i]

# You can print the generated melody to see its structure:
# if generative_melody:
#   print(f"Generated Melody: {generative_melody.notes} with intervals {generative_melody.interval}")

## --- 3. Create a Simple Chord Progression ---

# Let's create a I-V-vi-IV progression in C Major.
# C Major (I), G Major (V), A minor (vi), F Major (IV)
# Durations: let's make each chord last for 1 whole beat (or 4 quarter notes)

# C('Cmaj7', 3) creates a Cmaj7 chord with C3 as the lowest note.
# For simple triads:
chord1 = C('C4:major') % 1  # C Major chord, lasting 1 bar (default duration unit)
chord2 = C('G4:major') % 1  # G Major chord
chord3 = C('A4:minor') % 1  # A minor chord
chord4 = C('F4:major') % 1  # F Major chord

# Combine chords sequentially
backing_chords = chord1 + chord2 + chord3 + chord4

# You can make chords arpeggiated or change their rhythm.
# Example of a broken chord (arpeggio):
# C_broken = C('C4:major').arp(order=[0,1,2,1], duration=1/4) # Arpeggiate C E G E, each 1/4 beat
# For now, we'll stick to block chords.

## --- 4. Combine Melody and Chords into a Piece ---

# A 'piece' in musicpy can contain multiple tracks.
# Let's put our melody in one track and chords in another.

# Ensure the melody and chords are not None before creating tracks
if generative_melody and backing_chords:
    # Track 1: Melody
    # instrument=0 is Acoustic Grand Piano by default in General MIDI
    melody_track = track(generative_melody, instrument=0, channel=0)

    # Track 2: Chords
    # instrument=0 (Piano) or try another like 48 (String Ensemble)
    chords_track = track(backing_chords, instrument=48, channel=1)

    # Create the piece with these tracks
    # bpm (beats per minute)
    my_generative_piece = piece([melody_track, chords_track], bpm=120)

    ## --- 5. Play and Write to MIDI ---

    # Play the piece (requires pygame and a MIDI setup/soundfont for your OS)
    # This might not work in all environments directly (e.g., some online IDEs).
    print("Attempting to play the generated piece...")
    try:
        play(my_generative_piece, name='generative_kickstart.mid', wait=True)
        # 'wait=True' makes the script wait until playback is finished.
        # The 'name' argument here actually saves it as a MIDI file too.
        print("Playback finished. MIDI file 'generative_kickstart.mid' should be created.")
    except Exception as e:
        print(f"Could not play the piece directly: {e}")
        print("Saving to MIDI file instead.")
        # Write the piece to a MIDI file
        write(my_generative_piece, name='generative_kickstart.mid')
        print("Piece written to 'generative_kickstart.mid'")

else:
    if not generative_melody:
        print("Melody generation failed or resulted in an empty melody.")
    if not backing_chords:
        print("Chord generation failed.")
    print("Skipping piece creation and playback due to missing musical parts.")


## --- Further Generative Ideas to Explore ---

# - **Rhythmic Variation:** Generate more complex rhythms algorithmically.
# - **Chord Voicing & Inversions:** Use musicpy's functions to change how chords are played.
#   (e.g., `chord.inversion(1)`, `chord.drop(2)`)
# - **Melodic Contours:** Implement rules for generating melodies that move up or down in specific ways.
# - **Markov Chains:** Use Markov chains to decide the next note or chord based on the current one.
# - **L-Systems:** Generate musical structures using Lindenmayer systems.
# - **Different Scales & Modes:** Explore modes (Dorian, Phrygian, etc.) or other scales (pentatonic, blues).
# - **Dynamic Changes:** Program changes in volume (dynamics) or tempo.
# - **More Complex Harmony:** Generate more sophisticated chord progressions using music theory rules
#   (e.g., circle of fifths, secondary dominants).
#   `current_scale.get_chord_by_degree(degree_number, seventh=True)`
# - **Percussion:** Add a drum track using `drum_track = drum(...)`

print("\nScript finished. Explore the 'generative_kickstart.mid' file!")