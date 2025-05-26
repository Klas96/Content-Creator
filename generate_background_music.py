import numpy as np
from scipy.io import wavfile

def generate_background_music(duration, output_path, test=False):
    if test:
        # Dummy music generation
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        note = np.zeros_like(t)
        wavfile.write(output_path, sample_rate, note.astype(np.float32))
    else:
        # Simple sine wave generation for demonstration
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        note = np.sin(2 * np.pi * 440 * t)
        wavfile.write(output_path, sample_rate, note.astype(np.float32))