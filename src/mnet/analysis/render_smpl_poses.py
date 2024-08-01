import numpy as np
import json
import pickle as pkl
from smplx import SMPL
import torch

from utils.video import render_video

if __name__ == "__main__":
    with open("./motion.json", "r") as f:
        dance_poses = json.loads(f.read())
    dance = torch.from_numpy(np.array(dance_poses['pose']).reshape(-1, 72)).float()
    trans = torch.from_numpy(np.array(dance_poses['root'])).float()
    motion = torch.cat([dance, trans], dim=1).unsqueeze(0).to(torch.device('mps'))
    print(motion.shape)
    smpl = SMPL(model_path='../app/', gender='MALE', batch_size=1).eval().to(torch.device('mps'))
    with torch.no_grad():
        render_video(motion, smpl, "./output", "../app/mBR0.wav")
