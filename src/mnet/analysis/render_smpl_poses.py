import numpy as np
import json
import pickle as pkl
from smplx import SMPL
import torch
import argparse
import os

from utils.video import render_video

def main(input_file: str, output_dir: str):
    with open(input_file, "r") as f:
        dance_poses = json.loads(f.read())
        np_dance = np.array(dance_poses['smpl_poses']).reshape(-1, 72)
        np_trans = np.array(dance_poses['smpl_trans'])
    # with open("./motion.pkl", "rb") as f:
    #     dance_poses = pkl.loads(f.read())
        # np_dance = np.array(dance_poses['smpl_poses']).reshape(-1, 72)
        # np_trans = np.array(dance_poses['smpl_trans'] / dance_poses['smpl_scaling'])

    dance = torch.from_numpy(np_dance).float()
    trans = torch.from_numpy(np_trans).float()

    motion = torch.cat([dance, trans], dim=1).unsqueeze(0).to(torch.device('mps'))
    smpl = SMPL(model_path='../../data', gender='MALE', batch_size=1).eval().to(torch.device('mps'))
    with torch.no_grad():
        if not (os.path.exists(output_dir) and os.path.isdir(output_dir)):
            os.mkdir(output_dir)
        render_video(motion, smpl, output_dir, "../app/mBR0.wav")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str)
    parser.add_argument("--output_dir", default="./outputs")
    args = parser.parse_args()

    main(args.file, args.output_dir)