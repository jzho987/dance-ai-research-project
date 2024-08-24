import pickle as pkl
import numpy as np
import polars as pl
import json
import os

import argparse
import matplotlib.pyplot as plt
from sklearn.manifold import Isomap

from feature_utils import calculate_body_component, calculate_effort_component, calculate_shape_component, calculate_space_component


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
'RCollar': 13, 
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


def plot_isomap(np_data, save_path: str=None):
    # Initialize Isomap and fit the model
    n_neighbors = 30
    n_components = 2
    isomap = Isomap(n_neighbors=n_neighbors, n_components=n_components, eigen_solver="auto")
    X_isomap = isomap.fit_transform(np_data)

    # Plot the results
    plt.figure(figsize=(8, 6))
    plt.scatter(X_isomap[:, 0], X_isomap[:, 1], c=np_data[:, 0], cmap=plt.cm.viridis)
    plt.title("Isomap Visualization")
    plt.colorbar()
    # NOTE: this checks if the string is None.
    if not save_path: 
        plt.show()
    else:
        plt.savefig(save_path)


def plot_polars_dataframe(df: pl.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 8))
    df_dict = df.to_dict()
    i_time = df_dict["i_time"]
    df_dict.pop("i_time")

    for key in df_dict:
        col = df_dict[key]
        ax.plot(i_time, col, label=f'{key}')

    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.set_title('Laban Quantitative Analysis')
    ax.legend()
    plt.tight_layout()
    plt.show()



def main(input_file: str, is_json: bool):
    with open(input_file, 'r' if is_json else 'rb') as f:
        if is_json:
            data = json.loads(f.read())
        else:
            data = pkl.loads(f.read())
    if type(data) is dict:
        print("processing as dictionary")
        data = data["result"]
    data = np.array(data)
    data = data.reshape(-1, 24, 3)
    df_dict = {}
    for key in JOINT_MAP:
        index = JOINT_MAP[key]
        df_dict[key] = data[:, index, :]
    df_dict["i_time"] = range(data.shape[0])
    df = pl.DataFrame(df_dict)
    bc_df = calculate_body_component(df.clone())
    ec_df = calculate_effort_component(df.clone())
    sc_df = calculate_shape_component(df.clone())
    pc_df = calculate_space_component(df.clone())

    print("body component", bc_df)
    print("effort component", ec_df)
    print("shape component", sc_df)
    print("space component", pc_df)

    laban_df = bc_df.join(ec_df, on="i_time", how="inner"
        ).join(sc_df, on="i_time", how="inner"
        ).join(pc_df, on="i_time", how="inner")

    print(laban_df.columns)
    print(laban_df)
    # plot_polars_dataframe(bc_df)
    # plot_polars_dataframe(ec_df)
    # plot_polars_dataframe(sc_df)
    # plot_polars_dataframe(pc_df)
    # plot_polars_dataframe(laban_df)
    bc_df = bc_df.drop(pl.col("i_time"))
    ec_df = ec_df.drop(pl.col("i_time"))
    sc_df = sc_df.drop(pl.col("i_time"))
    pc_df = pc_df.drop(pl.col("i_time"))
    laban_df = laban_df.drop(pl.col("i_time"))

    # path
    basename = os.path.basename(input_file)
    basename = basename.split(".")[0]

    # store dataframe
    if not os.path.exists("./out") or not os.path.isdir("./out"):
        os.makedirs("./out")
    laban_df.write_parquet(f'./out/{basename}.parquet')
    
    # store output images
    base_img_path = f'./img/{basename}'
    if not os.path.exists(base_img_path) or not os.path.isdir(base_img_path):
        os.makedirs(base_img_path)
    plot_isomap(bc_df, f'{base_img_path}/body.png')
    plot_isomap(ec_df, f'{base_img_path}/effort.png')
    plot_isomap(sc_df, f'{base_img_path}/shape.png')
    plot_isomap(pc_df, f'{base_img_path}/space.png')
    plot_isomap(laban_df, f'{base_img_path}/all.png')


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