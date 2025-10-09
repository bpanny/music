
from track import Track # type: ignore

class Composition:
    def __init__(self, title: str = "Untitled Composition", tempo: int = 120, time_signature: tuple[int, int] = (4, 4)):
        if tempo <= 0:
            raise ValueError("Tempo must be positive.")
        if not (isinstance(time_signature, tuple) and len(time_signature) == 2 and
                all(isinstance(n, int) and n > 0 for n in time_signature)):
            raise ValueError("Time signature must be a tuple of two positive integers (e.g., (4, 4)).")

        self.title = title
        self.tracks: list[Track] = []
        self.tempo = tempo  # Beats Per Minute (BPM)
        self.time_signature = time_signature # e.g., (4, 4)
        # self.key_signature: str | None = None # Optional, can be added later

    def add_track(self, track: Track):
        if not isinstance(track, Track):
            raise TypeError("Can only add Track objects to a Composition.")
        # Ensure unique track channels if automatically assigning or managing
        # For now, we assume channels are managed by the user when creating Tracks
        # or could be assigned sequentially here if desired.
        if any(t.channel == track.channel for t in self.tracks):
            # This is a simple check. A more robust system might auto-assign
            # or provide more detailed warnings/errors.
            print(f"Warning: Channel {track.channel} is already in use by another track.")
        self.tracks.append(track)

    def set_tempo(self, tempo: int):
        if tempo <= 0:
            raise ValueError("Tempo must be positive.")
        self.tempo = tempo

    # def set_key_signature(self, key: str):
    #     # Basic implementation, could be expanded for validation
    #     self.key_signature = key

    def __repr__(self):
        return f"Composition(title='{self.title}', tempo={self.tempo}, tracks_count={len(self.tracks)})"