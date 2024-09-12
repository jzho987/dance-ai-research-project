import argparse
import polars as pl

# NOTE: used to find all features in a component
BC_FEATS = [
    f'f{x}' for x in range(1, 8)
]
EC_FEATS = [
    f'f{x}' for x in range(9, 17)
]
SC_FEATS = [
    f'f{x}' for x in range(18, 25)
]
PC_FEATS = [
    f'f{x}' for x in range(26, 27)
]


def main(feature_1_path: str, feature_2_path: str):
    feat_1_df = pl.read_parquet(feature_1_path)
    feat_2_df = pl.read_parquet(feature_2_path)

    f1_bc_df = feat_1_df.select(pl.selectors.contains())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pytorch implementation of Music2Dance"
    )
    parser.add_argument("--file", default='results.json')
    group = parser.add_argument_group()
    group.add_argument("--json", action='store_true')
    args = parser.parse_args()

    is_json = False
    if args.json != None:
        is_json = True
    main(args.file, is_json)