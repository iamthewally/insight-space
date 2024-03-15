
# transcript.py

class Transcript:
    def __init__(self, max_window_size=600):
        self.segments = []
        self.max_window_size = max_window_size

    def add_segment(self, segment):
        self.segments.append(segment)
        if len(self.segments) > self.max_window_size:
            self.segments = self.segments[-self.max_window_size:]

    def get_window(self, window_size):
        return ''.join(self.segments[-window_size:])

    def get_full_transcript(self):
        return ''.join(self.segments)