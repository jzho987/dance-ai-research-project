from models.bailando import Bailando
import argparse
import os
from tqdm import tqdm
import essentia
from smplx import SMPL
from essentia.standard import *
from utils.extractor import FeatureExtractor
from utils.format import format_rotmat_output
import json
import numpy as np
import torch
import math

import config.config as cf
import config.gpt_config as gpt_cf
import config.vqvae_config as vq_cf

DEFAULT_SAMPLING_RATE = 15360*2
SHIFT_WIN = 29
GENERATION_LENGTH = SHIFT_WIN * 4


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pytorch implementation of Music2Dance"
    )
    parser.add_argument("--data_dir")
    parser.add_argument("--music_dir")
    parser.add_argument("--dance_dir")
    parser.add_argument("--music_name")
    parser.add_argument("--input_dir")
    parser.add_argument("--output_dir")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--eval", action='store_true')
    group.add_argument("--eval_all", action='store_true')
    group.add_argument("--decode", action='store_true')
    group.add_argument("--endec", action='store_true')

    return parser.parse_args()


def handle_process_music(input_file: str):
    sampling_rate = DEFAULT_SAMPLING_RATE
    loader = essentia.standard.MonoLoader(filename=input_file, sampleRate=sampling_rate)
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

    feature = np.concatenate([
        mfcc, # 20
        mfcc_delta, # 20
        chroma_cqt, # 12
        onset_env, # 1
        onset_beat, # 1
        tempogram
    ], axis=0)
    feature = feature.transpose(1, 0)

    wav_padding = cf.wav_padding
    music_move = cf.move
    np_music = np.array(feature)

    # NOTE: transformation before store.
    # zero padding left
    for kk in range(wav_padding):
        np_music = np.append(np.zeros_like(np_music[-1:]), np_music, axis=0)
    # fully devisable
    for kk in range((len(np_music) // music_move + 1) * music_move - len(np_music) ):
        np_music = np.append(np_music, np_music[-1:], axis=0)
    # zero padding right
    for kk in range(wav_padding):
        np_music = np.append(np_music, np.zeros_like(np_music[-1:]), axis=0)
    return np_music


def eval(agent: Bailando, args):
    data_dir = args.data_dir
    music_data_file = os.path.join(data_dir, "music_data.json")
    dance_data_file = os.path.join(data_dir, "dance_data.json")
    with open(music_data_file) as f:
        json_obj = json.loads(f.read())
        music = np.array(json_obj)
    with open(dance_data_file) as f:
        json_obj = json.loads(f.read())
        dance = np.array(json_obj)
    assert music.all() != None, "music data is empty"
    assert dance.all() != None, "dance data is empty"

    result, quant = agent.eval_raw(
        torch.tensor(music).unsqueeze(0), torch.tensor(dance).unsqueeze(0), cf.music_config, 55, 0
    )
    result = result.squeeze(0).cpu().numpy().tolist()
    quant_up, quant_down = quant
    quant = [quant_up.tolist(), quant_down.tolist()]
    json_dict = {'result': result, 'quant': quant}
    with open("results.json", "w") as f:
        f.write(json.dumps(json_dict))

def eval_all(agent: Bailando, dance_dir: str, music_dir: str, output_dir: str):
    musics = os.listdir(music_dir)
    dances = os.listdir(dance_dir)

    music_dict = {}
    dance_dict = {}
    # make dict
    print("loading music data")
    for music in musics:
        music_path = os.path.join(music_dir, music)
        music_data = handle_process_music(music_path)
        music_dict[music] = music_data
    print("finished music data")
    for dance in tqdm(dances, desc=f"loading dance data"):
        dance_data_path = os.path.join(dance_dir, dance)
        with open(dance_data_path) as f:
            json_obj = json.loads(f.read())
        dance_data_list = np.array(json_obj)
        dance_dict[dance] = dance_data_list
    
    # batching
    batch_size = 30
    batch_count = math.ceil(len(dances) / batch_size)

    for music in music_dict:
        music_data = music_dict[music]
        for i in tqdm(range(batch_count), desc=f"generating with music: {music}"):
            batch_start = i * batch_size
            batch_end = (i + 1) * batch_size
            dance_data_list = []
            dance_names_list = dances[batch_start: batch_end]
            cur_batch_size = len(dance_names_list)
            for dance in dance_names_list:
                cur_dance_data = dance_dict[dance]
                dance_data_list.append(cur_dance_data)

            music_data_repeated = torch.tensor(music_data).unsqueeze(0).repeat_interleave(cur_batch_size, dim=0)
            dance_data_list = torch.tensor(dance_data_list)
            result, _ = agent.eval_raw(
                music_data_repeated, dance_data_list, cf.music_config, GENERATION_LENGTH, 0, SHIFT_WIN
            )
            result = result.cpu().numpy().tolist()

            for i, dance_name in enumerate(dance_names_list):
                dance_results = result[i]
                name = f"{dance_name}-{music}.json"
                output_path = os.path.join(output_dir, name)
                with open(output_path, "w") as f:
                    f.write(json.dumps(dance_results))


def decode(agent: Bailando, json_path, out_path):
    with open(json_path) as f:
        json_obj = json.loads(f.read())
        up, down = json_obj['up'], json_obj['down']
    out = agent.decode(up, down).cpu().numpy().tolist()
    with open(out_path, "w") as f:
        f.write(json.dumps(out))


def endec(agent: Bailando, json_path, out_path, device="cuda"):
    with open(json_path) as f:
        json_obj = json.loads(f.read())
    np_dance = np.array(json_obj)
    # transform for non rotmat data
    root = np_dance[:, :3]
    np_dance = np_dance - np.tile(root, (1, 24))
    np_dance[:, :3] = root
    for kk in range((len(np_dance) // 5 + 1) * 5 - len(np_dance) ):
        np_dance = np.append(np_dance, np_dance[-1:], axis=0)
    dance_input = torch.tensor(np_dance, dtype=torch.float32).unsqueeze(0).to(torch.device(device))
    up, down = agent.encode(dance_input)
    out = agent.decode(up, down).cpu().numpy().tolist()
    with open(out_path, "w") as f:
        f.write(json.dumps(out))


def main():
    # parse arguments and load config
    args = parse_args()

    # build agent
    agent = Bailando(vq_cf, gpt_cf, cf, "cuda", vq_ckpt_dir="./weight/vqvae.pt", gpt_ckpt_dir="./weight/gpt.pt")

    # start eval
    if args.eval:
        eval(agent, args)
    if args.eval_all:
        eval_all(agent, args.dance_dir, args.music_dir, args.output_dir)
    if args.decode:
        decode(agent, args.input_dir, args.output_dir)
    if args.endec:
        endec(agent, args.input_dir, args.output_dir, "mps")


if __name__ == "__main__":
    main()
