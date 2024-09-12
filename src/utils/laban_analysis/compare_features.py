import argparse
import polars as pl
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr


def main(feature_1_path: str, feature_2_path: str):
    feat_1_bc_np = pl.read_parquet(os.path.join(feature_1_path, "bc.parquet")).to_numpy()
    feat_1_ec_np = pl.read_parquet(os.path.join(feature_1_path, "ec.parquet")).to_numpy()
    feat_1_sc_np = pl.read_parquet(os.path.join(feature_1_path, "sc.parquet")).to_numpy()
    feat_1_pc_np = pl.read_parquet(os.path.join(feature_1_path, "pc.parquet")).to_numpy()
    feat_2_bc_np = pl.read_parquet(os.path.join(feature_2_path, "bc.parquet")).to_numpy()
    feat_2_ec_np = pl.read_parquet(os.path.join(feature_2_path, "ec.parquet")).to_numpy()
    feat_2_sc_np = pl.read_parquet(os.path.join(feature_2_path, "sc.parquet")).to_numpy()
    feat_2_pc_np = pl.read_parquet(os.path.join(feature_2_path, "pc.parquet")).to_numpy()

    windows = min(feat_1_bc_np.shape[0], feat_1_ec_np.shape[0], feat_1_sc_np.shape[0], feat_1_pc_np.shape[0],
                  feat_1_bc_np.shape[0], feat_1_ec_np.shape[0], feat_1_sc_np.shape[0], feat_1_pc_np.shape[0])
    bc_rs = []
    ec_rs = []
    sc_rs = []
    pc_rs = []
    for i in range(windows):
       bc_r = pearsonr(feat_1_bc_np[i], feat_2_bc_np[i], alternative="two-sided") 
       bc_rs.append(bc_r.statistic)
       ec_r = pearsonr(feat_1_ec_np[i], feat_2_ec_np[i]) 
       ec_rs.append(ec_r.statistic)
       sc_r = pearsonr(feat_1_sc_np[i], feat_2_sc_np[i]) 
       sc_rs.append(sc_r.statistic)
       pc_r = pearsonr(feat_1_pc_np[i], feat_2_pc_np[i]) 
       pc_rs.append(pc_r.statistic)
    all_rs = [bc_rs, ec_rs, sc_rs, pc_rs]
    names = ["Body Component R values", "Effort Component R values", "Shape Component R values", "Space Component R values"]
    
    fig, axs = plt.subplots(nrows=4, ncols=1, figsize=(10, 8), sharex=True)
    for ax, rs, name in zip(axs, all_rs, names):
        cax = ax.imshow([rs], aspect='auto', cmap='Greys', vmin=0, vmax=1)
        ax.set_yticks([])  # Remove y-axis ticks as we're using a single horizontal bar
        ax.set_title(name)

    plt.colorbar(cax, ax=ax, orientation='horizontal')
    plt.show()
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pytorch implementation of Music2Dance"
    )
    parser.add_argument("m1", default='./out/motion_1')
    parser.add_argument("m2", default='./out/motion_2')
    args = parser.parse_args()

    main(args.m1, args.m2)