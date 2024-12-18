from models_v1.bailando_v1 import BailandoV1 as Altlando
import argparse
import os
from tqdm import tqdm
from essentia.standard import *
from utils.extractor import FeatureExtractor
from utils.format import format_output
import json
import numpy as np
import torch
import math

import config.config as cf
import config.gpt_config_lb as gpt_cf
import config.vqvae_config_lb as vq_cf

DEFAULT_SAMPLING_RATE = 15360*2
SHIFT_WIN = 29
GENERATION_LENGTH = SHIFT_WIN * 4


def eval_all(agent: Altlando, dance_dir: str, output_dir: str):
    dances = os.listdir(dance_dir)

    dance_dict = {}
    # make dict
    for dance in tqdm(dances, desc=f"loading dance data"):
        dance_data_path = os.path.join(dance_dir, dance)
        with open(dance_data_path) as f:
            json_obj = json.loads(f.read())
        dance_data_list = np.array(json_obj)
        dance_dict[dance] = dance_data_list
    
    # batching
    batch_size = 30
    batch_count = math.ceil(len(dances) / batch_size)

    for i in tqdm(range(batch_count), desc=f"generating"):
        batch_start = i * batch_size
        batch_end = (i + 1) * batch_size
        dance_data_list = []
        dance_names_list = dances[batch_start: batch_end]
        for dance in dance_names_list:
            cur_dance_data = dance_dict[dance]
            dance_data_list.append(cur_dance_data)

        dance_data_list = torch.tensor(dance_data_list)
        result, _ = agent.eval_raw(
            dance_data_list, GENERATION_LENGTH, 0, SHIFT_WIN
        )
        np_dance = result.cpu().numpy()

        root = np_dance[:, :, :3]
        np_dance = np_dance + np.tile(root, (1, 1, 24))
        np_dance[:, :, :3] = root
        result = np_dance.tolist()

        for i, dance_name in enumerate(dance_names_list):
            dance_results = result[i]
            name = f"{dance_name}-NoMusic.json"
            output_path = os.path.join(output_dir, name)
            with open(output_path, "w") as f:
                f.write(json.dumps(dance_results))


def main():
    # parse arguments and load config
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
    args = parser.parse_args()

    # build agent
    agent = Altlando(vq_cf, gpt_cf, cf, "cuda", "./weight/vqvae_lb.pt", "./weight/gpt_lb.pt")

    # start eval
    if args.eval:
        print("not implemented") 
    if args.eval_all:
        eval_all(agent, args.dance_dir, args.output_dir)
    if args.decode:
        print("not implemented") 
    if args.endec:
        print("not implemented") 


if __name__ == "__main__":
    main()
