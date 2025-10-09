# midi_exporter.py

import mido
from composition import Composition # type: ignore
from track import Track # type: ignore
from music_elements import Note, Chord, Rest # type: ignore

class MidiExporter:
    def __init__(self, ticks_per_beat: int = 480):
        self.ticks_per_beat = ticks_per_beat

    def export(self, composition: Composition, output_filepath: str):
        if not isinstance(composition, Composition):
            raise TypeError("Input must be a Composition object.")
        if not output_filepath.lower().endswith(".mid"):
            print(f"Warning: Output filepath '{output_filepath}' does not end with .mid. Appending .mid.")
            output_filepath += ".mid"

        midi_file = mido.MidiFile(ticks_per_beat=self.ticks_per_beat, type=1) # Type 1 for multi-track

        # Meta track (usually the first track) for tempo, time signature, etc.
        meta_track = mido.MidiTrack()
        midi_file.tracks.append(meta_track)

        meta_track.append(mido.MetaMessage('track_name', name=composition.title, time=0))
        meta_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(composition.tempo), time=0))
        meta_track.append(mido.MetaMessage('time_signature',
                                          numerator=composition.time_signature[0],
                                          denominator=composition.time_signature[1],
                                          clocks_per_click=24, # Standard
                                          notated_32nd_notes_per_beat=8, # Standard
                                          time=0))
        # Add key signature if implemented in Composition
        # if composition.key_signature:
        #     meta_track.append(mido.MetaMessage('key_signature', key=composition.key_signature, time=0))


        for track_obj in composition.tracks:
            if not isinstance(track_obj, Track):
                print(f"Skipping invalid object in composition.tracks: {track_obj}")
                continue

            mido_track = mido.MidiTrack()
            midi_file.tracks.append(mido_track)

            # Track-specific meta messages and initial setup messages
            mido_track.append(mido.MetaMessage('track_name', name=track_obj.name, time=0))
            mido_track.append(mido.Message('program_change', program=track_obj.instrument_program, channel=track_obj.channel, time=0))
            mido_track.append(mido.Message('control_change', control=10, value=track_obj.pan, channel=track_obj.channel, time=0)) # Pan
            mido_track.append(mido.Message('control_change', control=7, value=track_obj.volume, channel=track_obj.channel, time=0)) # Volume

            # Collect all events with their absolute tick times
            events = [] # List of (absolute_tick_time, mido_message)

            for element in track_obj.elements:
                start_ticks = int(element.start_time * self.ticks_per_beat)

                if isinstance(element, Note):
                    end_ticks = int((element.start_time + element.duration) * self.ticks_per_beat)
                    events.append((start_ticks, mido.Message('note_on', note=element.pitch, velocity=element.velocity, channel=track_obj.channel)))
                    events.append((end_ticks, mido.Message('note_off', note=element.pitch, velocity=0, channel=track_obj.channel)))
                elif isinstance(element, Chord):
                    # Assuming all notes in a chord share the same start_time and duration from the chord object perspective
                    # or derived from its first note (as per current music_elements.Chord logic)
                    chord_start_time = element.start_time
                    chord_duration = element.duration
                    if chord_start_time is None or chord_duration is None:
                        print(f"Warning: Chord {element} in track '{track_obj.name}' has no notes or calculable start/duration. Skipping.")
                        continue

                    chord_start_ticks = int(chord_start_time * self.ticks_per_beat)
                    chord_end_ticks = int((chord_start_time + chord_duration) * self.ticks_per_beat)

                    for note_in_chord in element.notes:
                        events.append((chord_start_ticks, mido.Message('note_on', note=note_in_chord.pitch, velocity=note_in_chord.velocity, channel=track_obj.channel)))
                        events.append((chord_end_ticks, mido.Message('note_off', note=note_in_chord.pitch, velocity=0, channel=track_obj.channel)))
                elif isinstance(element, Rest):
                    # Rests are implicitly handled by the delta times between other events.
                    # No direct MIDI message is needed for a Rest itself.
                    pass

            # Sort events by absolute time, then prioritize note_off if at the same time (helps with some players)
            events.sort(key=lambda x: (x[0], 0 if x[1].type == 'note_off' else 1))

            # Convert absolute times to delta times for Mido messages
            last_tick_time = 0
            for abs_time, msg in events:
                delta_ticks = abs_time - last_tick_time
                msg.time = delta_ticks
                mido_track.append(msg)
                last_tick_time = abs_time
            
            # Add an end of track meta message (optional but good practice)
            # Ensure its delta time is calculated correctly based on the last event.
            # If events is empty, time is 0. Otherwise, it's 0 if last_tick_time is the current time.
            # Mido might handle this automatically if track is empty, but explicit is fine.
            # We can set it to a small delta if needed to ensure it's after the last note_off.
            end_of_track_delta = 0
            if not events: # if track was empty except for initial messages
                 mido_track.append(mido.MetaMessage('end_of_track', time=1)) # Small delay
            else:
                 mido_track.append(mido.MetaMessage('end_of_track', time=0))


        try:
            midi_file.save(output_filepath)
            print(f"MIDI file saved to {output_filepath}")
        except Exception as e:
            print(f"Error saving MIDI file: {e}")