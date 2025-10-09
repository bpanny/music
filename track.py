# track.py

from music_elements import Note, Chord, Rest # type: ignore # Add this if your linter complains before files are in same dir

class Track:
    def __init__(self, name: str, instrument_program: int = 0, channel: int = 0, pan: int = 64, volume: int = 100):
        if not (0 <= instrument_program <= 127):
            raise ValueError("Instrument program must be between 0 and 127.")
        if not (0 <= channel <= 15):
            raise ValueError("MIDI channel must be between 0 and 15.")
        if not (0 <= pan <= 127):
            raise ValueError("Pan must be between 0 and 127.")
        if not (0 <= volume <= 127):
            raise ValueError("Volume must be between 0 and 127.")

        self.name = name
        self.instrument_program = instrument_program
        self.channel = channel
        self.elements: list[Note | Chord | Rest] = []
        self.pan = pan # 0 (left) - 64 (center) - 127 (right)
        self.volume = volume # Track-level volume (often set by CC 7)

    def add_element(self, element: Note | Chord | Rest):
        if not isinstance(element, (Note, Chord, Rest)):
            raise TypeError("Element must be a Note, Chord, or Rest object.")
        self.elements.append(element)
        # Keep elements sorted by start_time for easier processing later
        self.elements.sort(key=lambda x: x.start_time)

    def add_notes(self, notes: list[Note]):
        for note in notes:
            if not isinstance(note, Note):
                raise TypeError("All items in notes list must be Note objects.")
            self.add_element(note)

    def set_instrument(self, instrument_program: int, name: str | None = None):
        if not (0 <= instrument_program <= 127):
            raise ValueError("Instrument program must be between 0 and 127.")
        self.instrument_program = instrument_program
        if name: # Optionally update track name if a new instrument implies a role change
            self.name = name

    def __repr__(self):
        return f"Track(name='{self.name}', instrument_program={self.instrument_program}, channel={self.channel}, elements_count={len(self.elements)})"