import generate_features
from tqdm import tqdm
import numpy as np
import json
import polars as pl
import os


def main(input_dir: str):
    fnames = os.listdir(input_dir)
    df = pl.DataFrame()
    out_path = "./data/generated_features_nm_roll"
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    chunk_size = 1000
    for i, name in enumerate(tqdm(fnames)):
        # if name.split("-")[2][0] != "3":
        #     continue
        # elif name.split("-")[3][0] != "0":
        #     continue

        full_path = os.path.join(input_dir, name)
        with open(full_path) as f:
            try:
                result = json.loads(f.read())
            except:
                print(full_path)
            result = np.array(result)
        feat_df = generate_features.main(result, name)
        df = df.vstack(feat_df)

        if i % chunk_size == 0 and i != 0:
            full_out_path = os.path.join(out_path, f"./generated_features_complete_{i // chunk_size}.parquet")
            df = df.with_columns(
                name_orig = pl.col("name").str.split(by=".").list.get(0),
                music = pl.col("name").str.split(by="-").list.get(1).str.split(".").list.get(0),
                win_c = pl.col("name").str.split(by="_").list.get(4).str.split(".").list.get(0),
            )
            df = df.drop(
                pl.col("name"),
            ).with_columns(
                name = pl.col("name_orig"),
            )
            df.write_parquet(full_out_path)
            df = pl.DataFrame()
    
    full_out_path = os.path.join(out_path, f"./generated_features_complete_{(i // chunk_size) + 1}.parquet")
    df = df.with_columns(
        name_orig = pl.col("name").str.split(by=".").list.get(0),
        music = pl.col("name").str.split(by="-").list.get(1).str.split(".").list.get(0),
        win_c = pl.col("name").str.split(by="_").list.get(4).str.split(".").list.get(0),
    )
    df = df.drop(
        pl.col("name"),
    ).with_columns(
        name = pl.col("name_orig"),
    )
    df.write_parquet(full_out_path)

if __name__ == "__main__":
    main("./data/generated_data_nm_roll")