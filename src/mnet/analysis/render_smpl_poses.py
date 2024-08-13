import numpy as np
import json
import pickle as pkl
from smplx import SMPL
import torch

from utils.video import render_video

if __name__ == "__main__":
    with open("./out_pregen_4.json", "r") as f:
        dance_poses = json.loads(f.read())
        np_dance = np.array(dance_poses['smpl_poses']).reshape(-1, 72) * 0.8
        # np_trans = np.array(dance_poses['smpl_trans'])
    with open("./motion.pkl", "rb") as f:
        dance_poses = pkl.loads(f.read())
        # np_dance = np.array(dance_poses['smpl_poses']).reshape(-1, 72)
        np_trans = np.array(dance_poses['smpl_trans'] / dance_poses['smpl_scaling'])

    dance = torch.from_numpy(np_dance).float()
    trans = torch.from_numpy(np_trans).float()

    motion = torch.cat([dance, trans], dim=1).unsqueeze(0).to(torch.device('mps'))
    smpl = SMPL(model_path='../../data', gender='MALE', batch_size=1).eval().to(torch.device('mps'))
    with torch.no_grad():
        render_video(motion, smpl, "./output", "../app/mBR0.wav")
