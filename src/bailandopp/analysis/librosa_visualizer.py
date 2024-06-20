import matplotlib.pyplot as plt
import matplotlib.axis as axis
import librosa
import essentia
from essentia.standard import *
import argparse
from extractor import FeatureExtractor
import numpy as np
import os

DEFAULT_SAMPLING_RATE = 15360*2

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", default='music.wav')
    parser.add_argument("--in_dir", default='inputs')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--out_dir")
    group.add_argument("--out_name")
    args = parser.parse_args()

    # load with essentia
    sampling_rate = DEFAULT_SAMPLING_RATE
    loader = essentia.standard.MonoLoader(filename=args.file, sampleRate=sampling_rate)
    audio = loader()
    audio_file = np.array(audio).T

    # process audio file
    extractor = FeatureExtractor()
    melspe_db = extractor.get_melspectrogram(audio_file, sampling_rate)
    mfcc = extractor.get_mfcc(melspe_db)
    mfcc_delta = extractor.get_mfcc_delta(mfcc)
    audio_harmonic, audio_percussive = extractor.get_hpss(audio_file)
    if sampling_rate == 15360 * 2:
        octave = 7
    else:
        octave = 5
    chroma_cqt = extractor.get_chroma_cqt(audio_harmonic, sampling_rate, octave=octave)
    onset_env = extractor.get_onset_strength(audio_percussive, sampling_rate)
    tempogram = extractor.get_tempogram(onset_env, sampling_rate)
    onset_beat = extractor.get_onset_beat(onset_env, sampling_rate)[0]
    onset_env = onset_env.reshape(1, -1)

    fig, ax = plt.subplots(nrows=5, figsize=(10, 10))
    librosa.display.specshow(mfcc, y_axis='chroma', x_axis='time', ax=ax[0])
    ax[0].set(title='mfcc', ylim=(0, 10))
    ax[0].label_outer()
    librosa.display.specshow(mfcc_delta, y_axis='chroma', x_axis='time', ax=ax[1])
    ax[1].set(title='mfcc_delta', ylim=(0, 10))
    img = librosa.display.specshow(chroma_cqt, y_axis='chroma', x_axis='time', ax=ax[2])
    ax[2].set(title='chroma_cqt', ylim=(0, 10))

    times = librosa.times_like(onset_env, sr=sampling_rate)
    ax[3].plot(times, onset_env[0], label='Onset strength')
    ax[3].label_outer()
    ax[3].legend(frameon=True)
    librosa.display.specshow(tempogram, sr=sampling_rate, x_axis='time', y_axis='tempo', cmap='magma', ax=ax[4])
    tempo: np.ndarray = librosa.feature.tempo(onset_envelope=onset_env, sr=sampling_rate)[0]
    ax[4].axhline(tempo, color='w', linestyle='--', alpha=1,
                label='Estimated tempo={:g}'.format(tempo.item(0)))
    ax[4].legend(loc='upper right')
    ax[4].set(title='Tempogram')

    if hasattr(args, "out_dir") and args.out_dir != None:
        name = os.path.basename(args.file)
        name = name.split(".")[0]
        out_path = os.path.join(args.out_dir, f"{name}.jpg")
    elif hasattr(args, "out_name") and args.out_name != None:
        out_path = args.out_name
    plt.savefig(out_path)

