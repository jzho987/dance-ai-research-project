import generate_features
from tqdm import tqdm
import polars as pl
import os


def main(input_dir: str):
    fnames = os.listdir(input_dir)
    df = pl.DataFrame()
    for name in tqdm(fnames):
        full_path = os.path.join(input_dir, name)
        feat_df = generate_features.main(full_path, True)
        df = df.vstack(feat_df)
    
    print(df)
    df.write_csv("./features_complete.csv")
    

if __name__ == "__main__":
    main("./data/raw/complete")