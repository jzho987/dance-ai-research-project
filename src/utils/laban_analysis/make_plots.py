import os
import polars as pl
import numpy as np
from tqdm import tqdm

from matplotlib import cm
import matplotlib.pyplot as plt
from sklearn.manifold import Isomap


def plot_polars_dataframe(dfs: list[pl.DataFrame], names):
    df_dicts = []
    for df in dfs:
        df_dict = df.to_dict()
        i_time = df_dict["i_time"]
        df_dict.pop("i_time")
        df_dicts.append(df_dict)
        keys = df_dict.keys()
    
    fig, axs = plt.subplots(nrows=len(keys), constrained_layout=True)
    for ax, key in zip(axs, keys):
        for df_dict, name in zip(df_dicts, names):
            ax.plot(i_time, df_dict[key], label=f'{name}')
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        ax.set_title(f'feature: {key} Comparison')
        ax.legend()
    plt.show()


def plot_and_save_isomaps(isomaps, names, title: str, save_path: str = None):
    # Plot the results
    plt.figure(figsize=(8, 6))
    colors = cm.rainbow(np.linspace(0, 1, isomaps.shape[0]))

    for i, isomap, color in zip(names, isomaps, colors):
        plt.plot(isomap[:, 0], isomap[:, 1], c=color, marker=".", label=i)

    plt.title(title)
    plt.legend()
    plt.show()


def generate_isomap(np_data: np.ndarray):
    # Initialize Isomap and fit the model
    n_neighbors = 30
    n_components = 2
    isomap = Isomap(n_neighbors=n_neighbors, n_components=n_components, eigen_solver="auto")
    out_isomap = isomap.fit_transform(np_data)

    return out_isomap


def main(input_dir: str, output_dir: str):
    out_dirs = os.listdir(input_dir)   

    bc_dfs: list[pl.DataFrame] = []
    ec_dfs: list[pl.DataFrame] = []
    sc_dfs: list[pl.DataFrame] = []
    pc_dfs: list[pl.DataFrame] = []
    for out_dir in tqdm(out_dirs):
        bc_df_path = os.path.join(input_dir, out_dir, "bc.parquet")
        ec_df_path = os.path.join(input_dir, out_dir, "ec.parquet")
        sc_df_path = os.path.join(input_dir, out_dir, "sc.parquet")
        pc_df_path = os.path.join(input_dir, out_dir, "pc.parquet")
        bc_df = pl.read_parquet(bc_df_path).fill_nan(0)
        ec_df = pl.read_parquet(ec_df_path).fill_nan(0)
        sc_df = pl.read_parquet(sc_df_path).fill_nan(0)
        pc_df = pl.read_parquet(pc_df_path).fill_nan(0)
        bc_dfs.append(bc_df)
        ec_dfs.append(ec_df)
        sc_dfs.append(sc_df)
        pc_dfs.append(pc_df)

    # NOTE: names will be used to track the name and index of the motion pieces.
    names = out_dirs

    bc_maps = []
    ec_maps = []
    sc_maps = []
    pc_maps = []
    for i in tqdm(range(len(names)), desc="generating isomaps"):
        bc_df = bc_dfs[i]
        ec_df = ec_dfs[i]
        sc_df = sc_dfs[i]
        pc_df = pc_dfs[i]
        bc_map = generate_isomap(bc_df.to_numpy())
        ec_map = generate_isomap(ec_df.to_numpy())
        sc_map = generate_isomap(sc_df.to_numpy())
        pc_map = generate_isomap(pc_df.to_numpy())
        bc_maps.append(bc_map)
        ec_maps.append(ec_map)
        sc_maps.append(sc_map)
        pc_maps.append(pc_map)
    # plot_and_save_isomaps(np.array(bc_maps), names, "Body Component")
    # plot_and_save_isomaps(np.array(ec_maps), names, "Effort Component")
    # plot_and_save_isomaps(np.array(sc_maps), names, "Space Component")
    # plot_and_save_isomaps(np.array(pc_maps), names, "Shape Component")

    plot_polars_dataframe(bc_dfs, names)
    plot_polars_dataframe(ec_dfs, names)
    plot_polars_dataframe(sc_dfs, names)
    plot_polars_dataframe(pc_dfs, names)


if __name__ == "__main__":
    main("./comp", "./img")
    
