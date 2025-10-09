# music_elements.py

class Note:
    def __init__(self, pitch: int, start_time: float, duration: float, velocity: int = 100):
        if not (0 <= pitch <= 127):
            raise ValueError("Pitch must be between 0 and 127.")
        if not (0 <= velocity <= 127):
            raise ValueError("Velocity must be between 0 and 127.")
        if duration <= 0:
            raise ValueError("Duration must be positive.")
        if start_time < 0:
            raise ValueError("Start time cannot be negative.")

        self.pitch = pitch
        self.start_time = start_time
        self.duration = duration
        self.velocity = velocity

    def __repr__(self):
        return f"Note(pitch={self.pitch}, start_time={self.start_time}, duration={self.duration}, velocity={self.velocity})"

    def transpose(self, semitones: int):
        self.pitch = max(0, min(127, self.pitch + semitones))

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

class Chord:
    def __init__(self, notes: list[Note] = None):
        self._notes: list[Note] = []
        if notes:
            # Assuming all notes in a chord start at the same time and have the same duration
            # More complex chord structures might require different handling
            if not all(isinstance(n, Note) for n in notes):
                raise ValueError("All elements in notes list must be Note objects.")
            self._notes = sorted(notes, key=lambda n: n.pitch) # Store notes sorted by pitch

    @property
    def notes(self) -> list[Note]:
        return self._notes

    def add_note(self, note: Note):
        if not isinstance(note, Note):
            raise ValueError("Can only add Note objects to a Chord.")
        # Basic implementation: ensure all notes in a chord generally align in time if added this way
        # For simplicity, we'll assume a chord's properties are defined by its constituent notes
        self._notes.append(note)
        self._notes.sort(key=lambda n: n.pitch)

    def add_pitches(self, pitches: list[int], start_time: float, duration: float, velocity: int = 100):
        for pitch in pitches:
            self.add_note(Note(pitch, start_time, duration, velocity))

    @property
    def start_time(self) -> float | None:
        if not self._notes:
            return None
        # Assuming notes intended for a chord should share the same start time.
        # This could be enforced or be more flexible. For now, take the first note's.
        return self._notes[0].start_time

    @property
    def duration(self) -> float | None:
        if not self._notes:
            return None
        # Assuming notes intended for a chord should share the same duration.
        return self._notes[0].duration

    def __repr__(self):
        note_reprs = ", ".join(repr(n) for n in self._notes)
        return f"Chord(notes=[{note_reprs}])"

    def transpose(self, semitones: int):
        for note in self._notes:
            note.transpose(semitones)


class Rest:
    def __init__(self, start_time: float, duration: float):
        if duration <= 0:
            raise ValueError("Duration must be positive.")
        if start_time < 0:
            raise ValueError("Start time cannot be negative.")

        self.start_time = start_time
        self.duration = duration

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

    def __repr__(self):
        return f"Rest(start_time={self.start_time}, duration={self.duration})"