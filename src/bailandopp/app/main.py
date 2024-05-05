from models.bailando import Bailando
import argparse
import os
import yaml
from pprint import pprint
from easydict import EasyDict
import json
import numpy as np

import config.config as cf
import config.gpt_config as gpt_cf
import config.vqvae_config as vq_cf


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pytorch implementation of Music2Dance"
    )
    parser.add_argument("--config", default="")
    parser.add_argument("--data_dir")
    parser.add_argument("--music_name")
    parser.add_argument("--weight_dir")

    return parser.parse_args()


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

    vq_ckpt_dir = os.path.join(args.weight_dir, "vqvae.pt")
    gpt_ckpt_dir = os.path.join(args.weight_dir, "gpt.pt")
    agent.eval_raw_visualize(
        music, dance, args.music_name, vq_ckpt_dir, gpt_ckpt_dir, cf.music_config
    )


def main():
    # parse arguments and load config
    args = parse_args()

    # build agent
    agent = Bailando(vq_cf, gpt_cf, cf, "mps")

    # start eval
    eval(agent, args)


if __name__ == "__main__":
    main()
