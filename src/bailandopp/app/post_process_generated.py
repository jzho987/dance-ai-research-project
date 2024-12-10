from smplx import SMPL
import torch
import numpy as np
import config.config as cf
from tqdm import tqdm
from utils.format import format_rotmat_output
import json
import os


if __name__ == "__main__":
    smpl = SMPL(model_path=cf.smpl_model_path, gender='MALE', batch_size=1).to(torch.device("cuda"))

    out_path = "./data/generated_data"
    processed_path = "./data/generated_post_data"
    if not os.path.exists(processed_path):
        os.makedirs(processed_path)
    fnames = os.listdir(out_path)
    for name in tqdm(fnames):
        full_path = os.path.join(out_path, name)
        with open(full_path) as f:
            results = json.loads(f.read())

        results = format_rotmat_output(results, smpl)
        full_out_path = os.path.join(processed_path, name)
        with open(full_out_path, "w") as f:
            f.write(json.dumps(results))