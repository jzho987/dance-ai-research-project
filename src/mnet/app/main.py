import os
import yaml
import librosa
from utils.feature_extrator import FeatureExtractor
from utils.video import render_video
import torch
import numpy as np
import json
import pickle as pkl

from smplx import SMPL

import configs.gen_config as gen_cf
from models.aist_module import DanceGenerator

Genres = {
    'gBR': 0,
    'gPO': 1,
    'gLO': 2,
    'gMH': 3,
    'gLH': 4,
    'gHO': 5,
    'gWA': 6,
    'gKR': 7,
    'gJS': 8,
    'gJB': 9,
}


def load_model(model_path, config: gen_cf, device_str: str):

    ckpt = torch.load(model_path, map_location=device_str)
    loaded_state_dict = ckpt['state_dict']
    model_state_dict = {}
    for key in loaded_state_dict:
        if key.split(".")[0] == "gen":
            new_key = key[4:]
            print(new_key)
            model_state_dict[new_key] = loaded_state_dict[key]
    
    agent = DanceGenerator(config.dim, config.depth, config.heads, config.mlp_dim, config.music_length, config.seed_m_length, config.predict_length, config.rot_6d)
    agent.load_state_dict(model_state_dict)
    agent.to(torch.device(device_str))

    return agent

def load_music(music_path: str):
    FPS = 60
    HOP_LENGTH = 512
    SR = FPS * HOP_LENGTH
    EPS = 1e-6

    extractor = FeatureExtractor()
    audio, _ = librosa.load(music_path, sr=SR)

    melspe_db = extractor.get_melspectrogram(audio, SR)
    mfcc = extractor.get_mfcc(melspe_db)
    mfcc_delta = extractor.get_mfcc_delta(mfcc)
    audio_harmonic, audio_percussive = extractor.get_hpss(audio)
    chroma_cqt = extractor.get_chroma_cqt(audio_harmonic, SR, octave=7 if SR == 15360 * 2 else 5)
    onset_env = extractor.get_onset_strength(audio_percussive, SR)
    tempogram = extractor.get_tempogram(onset_env, SR)
    onset_beat = extractor.get_onset_beat(onset_env, SR)[0]

    onset_env = onset_env.reshape(1, -1)

    feature = np.concatenate([
        mfcc,  # 20
        mfcc_delta,  # 20
        chroma_cqt,  # 12
        onset_env,  # 1
        onset_beat,  # 1
        tempogram
    ], axis=0)
    feature = feature.transpose(1, 0)
    audio_feature = torch.from_numpy(feature).float()[:660]

    return audio_feature.unsqueeze(0)


def load_motion(dance_path: str, seed_length = 60):
    with open(dance_path, 'rb') as f:
        dance_array = pkl.loads(f.read())
    dance = torch.from_numpy(np.array(dance_array['smpl_poses'])).float().view(-1, 72)
    trans = torch.from_numpy(np.array(dance_array['smpl_trans'] / dance_array['smpl_scaling'])).float()
    print(dance.shape)
    print(trans.shape)
    motion = torch.cat([dance, trans], dim=1)[:seed_length]
    motion = motion.unsqueeze(0)

    return motion

def eval(weight_path: str, music_path: str, dance_path: str):
    # load model
    device = torch.device('mps')
    mnet = load_model(weight_path, gen_cf, "mps")

    t_music = load_music(music_path)
    t_dance = load_motion(dance_path)
    if device == torch.device('mps'):
        t_music = t_music.type(torch.float32)
        t_dance = t_dance.type(torch.float32)
    t_music = t_music.to(device)
    t_dance = t_dance.to(device)
    noise = torch.randn(1, 256).to(device)
    genre = torch.tensor(3, dtype=torch.long).unsqueeze(0)
    
    # render video
    smpl = SMPL(model_path='./', gender='MALE', batch_size=1).eval().to(device)
    with torch.no_grad():
        print(t_dance.shape)
        mnet.eval()
        gen_dance = mnet.inference(t_music, t_dance, noise, genre)
        render_video(gen_dance, smpl, "./", "./mBR0.wav")



def main(weight_path: str, music_path: str, dance_path: str):
    eval(weight_path, music_path, dance_path)


if __name__ == "__main__":
    main("./weights/last.ckpt", "./mBR0.wav", "./motion2.pkl")