import os
import numpy as np
from tqdm import tqdm
import json


def main():
    input_dir = "./data/generated_data_nm"
    for name in tqdm(os.listdir(input_dir)):

        full_path = os.path.join(input_dir, name)
        with open(full_path) as f:
            result = json.loads(f.read())
            result = np.array(result)
        
        t, j = result.shape
        step = 58
        frame_size = 232
        frame_count = (t - frame_size) // step + 1
        results=[]
        for start_i in range(0, frame_count):
            i = start_i * step
            # NOTE: add 1 since the end of slice is non-inclusive
            end_i = i + frame_size
            new = result[i: end_i, :] 
            results.append(new)


        for i, res in enumerate(results):
            full_out_path = os.path.join("./data/generated_data_nm_roll", f"{name}_{i}.json")
            with open(full_out_path, "w") as f:
                f.write(json.dumps(res.tolist()))


if __name__ == "__main__":
    main()