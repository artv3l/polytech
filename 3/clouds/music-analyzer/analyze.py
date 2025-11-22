import librosa

if __name__ == "__main__":
    audio_path = "test.wav"
    y, sr = librosa.load(audio_path, sr=None)

    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

    print("Tempo (BPM):", tempo)
    print("Number of beats:", len(beats))

    print("Sample rate:", sr)
    print("Duration (sec):", librosa.get_duration(y=y, sr=sr))
    print("Number of samples:", len(y))
