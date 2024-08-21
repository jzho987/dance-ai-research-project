import pickle as pkl
import numpy as np
import polars as pl
import json
import matplotlib.pyplot as plt
import argparse

JOINT_MAP = {
'Pelvis': 0,
'RHip': 1,
'LHip': 2,
'spine1': 3,
'RKnee': 4,
'LKnee': 5,
'spine2': 6,
'RAnkle': 7,
'LAnkle': 8,
'spine3': 9,
'RFoot': 10,
'LFoot': 11,
'Neck': 12,
'Rcollar': 13, 
'LCollar': 14,
'Head': 15,
'RShoulder': 16,
'LShoulder': 17,
'RElbow': 18,
'LElbow': 19,
'RWrist': 20, 
'LWrist': 21,  
'RHand': 22, 
'LHand': 23,  
}

def magnitude(col: pl.Expr) -> pl.Expr: 
    squared = col.arr.get(0).pow(2) + col.arr.get(1).pow(2) + col.arr.get(2).pow(2)
    mag = squared.sqrt().abs()
    return mag

def plot_polars_dataframe(df: pl.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 8))
    df_dict = df.to_dict()
    i_time = df_dict["i"]
    df_dict.pop("i")

    for key in df_dict:
        col = df_dict[key]
        ax.plot(i_time, col, label=f'{key}')

    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.set_title('Laban Quantitative Analysis')
    ax.legend()
    plt.tight_layout()
    plt.show()


def calculate_body_component(df: pl.DataFrame) -> pl.DataFrame:
    bc_df = df.with_columns(
        vec_lf1 = (pl.col("LFoot") - pl.col("LHip")),
        vec_rf1 = (pl.col("RFoot") - pl.col("RHip")),
        vec_lf2 = (pl.col("LHand") - pl.col("LShoulder")),
        vec_rf2 = (pl.col("RHand") - pl.col("RShoulder")),
        vec_f3 = (pl.col("RHand") - pl.col("LHand")),
        vec_lf4 = (pl.col("LHand") - pl.col("Head")),
        vec_rf4 = (pl.col("RHand") - pl.col("Head")),
        vec_lf5 = (pl.col("LHand") - pl.col("LHip")),
        vec_rf5 = (pl.col("RHand") - pl.col("RHip")),
        vec_f8 = (pl.col("LFoot") - pl.col("RFoot")),
    )
    bc_df = bc_df.with_columns(
        mag_lf1 = magnitude(pl.col("vec_lf1")),
        mag_rf1 = magnitude(pl.col("vec_rf1")),
        mag_lf2 = magnitude(pl.col("vec_lf2")),
        mag_rf2 = magnitude(pl.col("vec_rf2")),
        f3 = magnitude(pl.col("vec_f3")),
        mag_lf4 = magnitude(pl.col("vec_lf4")),
        mag_rf4 = magnitude(pl.col("vec_rf4")),
        mag_lf5 = magnitude(pl.col("vec_lf5")),
        mag_rf5 = magnitude(pl.col("vec_rf5")),
        root_height = pl.col("Pelvis").arr.get(1),
        lhip_height = pl.col("LHip").arr.get(1),
        rhip_height = pl.col("RHip").arr.get(1),
    )
    bc_df = bc_df.select(
        f1 = pl.mean_horizontal("mag_lf1", "mag_rf1"),
        f2 = pl.mean_horizontal("mag_lf2", "mag_rf2"),
        f3 = pl.col("f3"),
        f4 = pl.mean_horizontal("mag_lf4", "mag_rf4"),
        f5 = pl.mean_horizontal("mag_lf5", "mag_rf5"),
        f6 = pl.col("root_height"),
        f7 = pl.mean_horizontal("mag_lf1", "mag_rf1") - pl.mean_horizontal("lhip_height", "rhip_height"),
        f8 = magnitude(pl.col("vec_f8")),
        i = pl.col("i_time")
    )
    return bc_df
    

def main(input_file: str, is_json: bool):
    with open(input_file, 'r' if is_json else 'rb') as f:
        if is_json:
            data = json.loads(f.read())
        else:
            data = pkl.loads(f.read())
    data = np.array(data)
    data = data.reshape(-1, 24, 3)
    df_dict = {}
    for key in JOINT_MAP:
        index = JOINT_MAP[key]
        df_dict[key] = data[:, index, :]
    df_dict["i_time"] = range(data.shape[0])
    df = pl.DataFrame(df_dict)
    bc_df = calculate_body_component(df)
    plot_polars_dataframe(bc_df)



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