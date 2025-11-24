import librosa
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    audio_path = "test.wav"
    y, sample_rate = librosa.load(audio_path, sr=None)

    tempo, beats = librosa.beat.beat_track(y=y, sr=sample_rate)

    print("Tempo (BPM):", tempo)
    print("Number of beats:", len(beats))

    print("Sample rate:", sample_rate)
    print("Duration (sec):", librosa.get_duration(y=y, sr=sample_rate))
    print("Number of samples:", len(y))

    n_fft = 2048  # Window size: 2048 samples (adjust based on frequency resolution)  
    stft_result = librosa.stft(y, n_fft=n_fft)
    magnitude_spectrogram = np.abs(stft_result) # Compute magnitude spectrogram (absolute value of STFT result)
    db_spectrogram = librosa.amplitude_to_db(magnitude_spectrogram, ref=np.max) # Convert to dB scale (logarithmic)

    fig, ax = plt.subplots(figsize=(12, 6))
    a = librosa.display.specshow(
        db_spectrogram,
        ax=ax,
        sr=sample_rate,
        x_axis="time",  # Label x-axis as time  
        y_axis="hz",    # Label y-axis as frequency (Hz)  
        cmap="viridis"  # Colormap (try "magma" or "plasma" for different looks)
    )
    fig.colorbar(a, ax=ax, format="%+2.0f dB") # Show amplitude in dB
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title("Spectrogram (dB Scale)")

    fig.show()
