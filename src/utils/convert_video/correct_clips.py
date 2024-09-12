import os
import json
import argparse

import numpy as np
from tqdm import tqdm


def main(input_dir: str, output_dir: str):
    # pre
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    fnames = os.listdir(input_dir)

    for fname in tqdm(fnames):
        # load
        full_load_path = os.path.join(input_dir, fname)
        with open(full_load_path) as f:
            data = json.loads(f.read())
        data = np.array(data)

        # transform
        t, j = data.shape
        # NOTE: squeeze is for repeat later, adding in the 0th dim.
        root = data[0:1, :3]
        root_mask = np.tile(root, (t, j // 3))
        data = data - root_mask

        
        # flip
        # NOTE: recorded data is flipped, so we have to flip back
        data = data.reshape(t, j // 3, 3)
        data[:, :, 2] *= -1
        data = data.reshape(t, j)

        # save
        # NOTE: this is expecting <pure_name>.<extension>
        # NOTE: like: input_clip.json
        [pure_name, extension] = fname.split(".")
        save_name = f'{pure_name}_corrected.{extension}'
        full_save_path = os.path.join(output_dir, save_name)
        with open(full_save_path, "w") as f:
            json_str = json.dumps(data.tolist())
            f.write(json_str) 


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", default='input_clips')
    parser.add_argument("--output_dir", default='output_clips')
    args = parser.parse_args()

    main(args.input_dir, args.output_dir)