from models.bailando import Bailando
import argparse
import os
import yaml
from pprint import pprint
from easydict import EasyDict
import json
import numpy as np
import torch

import config.config as cf
import config.gpt_config as gpt_cf
import config.vqvae_config as vq_cf


def parse_args():
    parser = argparse.ArgumentParser(
        description="Pytorch implementation of Music2Dance"
    )
    parser.add_argument("--data_dir")
    parser.add_argument("--music_name")
    parser.add_argument("--weight_dir")
    parser.add_argument("--input_dir")
    parser.add_argument("--output_dir")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--eval", action='store_true')
    group.add_argument("--decode", action='store_true')
    group.add_argument("--endec", action='store_true')

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

    result, quant = agent.eval_raw(
        torch.tensor(music).unsqueeze(0), torch.tensor(dance).unsqueeze(0), cf.music_config, 55, 0
    )
    result = result.squeeze(0).cpu().numpy().tolist()
    quant_up, quant_down = quant
    quant = [quant_up.tolist(), quant_down.tolist()]
    json_dict = {'result': result, 'quant': quant}
    with open("results.json", "w") as f:
        f.write(json.dumps(json_dict))

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
    agent = Bailando(vq_cf, gpt_cf, cf, "mps", vq_ckpt_dir="./weight/vqvae.pt", gpt_ckpt_dir="./weight/gpt.pt")

    # start eval
    if args.eval:
        eval(agent, args)
    if args.decode:
        decode(agent, args.input_dir, args.output_dir)
    if args.endec:
        endec(agent, args.input_dir, args.output_dir, "mps")


if __name__ == "__main__":
    main()
