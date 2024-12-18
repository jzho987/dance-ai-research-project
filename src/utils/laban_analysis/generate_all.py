import generate_features
from tqdm import tqdm
import json
import numpy as np
import polars as pl
import os


def main(input_dir: str):
    fnames = os.listdir(input_dir)
    df = pl.DataFrame()
    for name in tqdm(fnames):
        full_path = os.path.join(input_dir, name)
        with open(full_path) as f:
            result = json.loads(f.read())
            result = np.array(result)
        feat_df = generate_features.main(result, name.split(".")[0])
        df = df.vstack(feat_df)
    
    print(df)
    df.write_csv("./input_features_nm.csv")
    

if __name__ == "__main__":
    main("./data/input_data")