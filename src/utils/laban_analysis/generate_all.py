import generate_features
from tqdm import tqdm
import polars as pl
import argparse
import os


def main(input_dir: str, output_file: str):
    fnames = os.listdir(input_dir)
    df = pl.DataFrame()
    for name in tqdm(fnames):
        full_path = os.path.join(input_dir, name)
        feat_df = generate_features.main(full_path, True)
        df = df.vstack(feat_df)
    
    print(df)
    df.write_parquet(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str)
    parser.add_argument("--output", type=str)
    args = parser.parse_args()
    main(args.input, args.output)