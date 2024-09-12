import polars as pl
import numpy as np
import shapely

def magnitude(col: pl.Expr) -> pl.Expr: 
    squared = col.arr.get(0).pow(2) + col.arr.get(1).pow(2) + col.arr.get(2).pow(2)
    mag = squared.sqrt().abs()
    return mag


def features_from_df(df: pl.DataFrame, sum_cols: list[str] = None) -> pl.DataFrame:
    cols = df.columns
    cols.remove("i_time")
    out_dict = {}
    for col in cols:
        min = df.min()[col]
        max = df.max()[col]
        std = df.std()[col]
        mean = df.mean()[col]
        out_dict[f'{col}_min'] = min
        out_dict[f'{col}_max'] = max
        out_dict[f'{col}_std'] = std
        out_dict[f'{col}_mean'] = mean
    out_df = pl.from_dict(out_dict)
    
    return out_df


def features_from_df_over_time(df: pl.DataFrame, sum_cols: list[str] = None) -> pl.DataFrame:
    cols = df.columns
    cols.remove("i_time")
    out_df = df.group_by_dynamic("i_time", every="1i", period="35i").agg(
        i_grouped = pl.col("i_time"),
    ).select(
        pl.col("i_time"),
        pl.col("i_grouped"),
    )
    for col in cols:
        if sum_cols is not None and col in sum_cols:
            agg_df = df.group_by_dynamic("i_time", every="1i", period="35i").agg(
                pl.col(col).mean().alias(f'num_{col}'),
            ).select(
                pl.col(f'num_{col}')
            )
        else:
            agg_df = df.group_by_dynamic("i_time", every="1i", period="35i").agg(
                pl.col(col).min().alias(f'min_{col}'),
                pl.col(col).max().alias(f'max_{col}'),
                pl.col(col).mean().alias(f'mean_{col}'),
                pl.col(col).std().alias(f'std_{col}'),
            ).select(
                pl.col(f'min_{col}'),
                pl.col(f'max_{col}'),
                pl.col(f'mean_{col}'),
                pl.col(f'std_{col}'),
            )
        out_df = out_df.hstack(agg_df)
    out_df = out_df.filter(
        pl.col("i_grouped").list.len() >= 35
    ).drop("i_grouped")
    
    return out_df


# NOTE: the space component does not use the standard aggregation
# that other components use. The format is standardized so a tuple
# will be returned just like the other component functions.
def calculate_space_component(df: pl.DataFrame) -> pl.DataFrame:
    pc_df = df.with_columns(
        pelvis_x = pl.col("Pelvis").arr.get(0),
        pelvis_z = pl.col("Pelvis").arr.get(2),
    )
    pc_df = pc_df.with_columns(
        pelvis_x_diff = pl.col("pelvis_x").diff(),
        pelvis_z_diff = pl.col("pelvis_z").diff(),
    )
    pc_df = pc_df.with_columns(
        mag_f26 = (pl.col("pelvis_x_diff").pow(2) + pl.col("pelvis_z_diff").pow(2)).sqrt(),
        i_time = pl.col("i_time")
    )
    pc_df = pc_df.group_by_dynamic("i_time", every="1i", period="35i").agg(
        f26 = pl.mean("mag_f26"),
        pelvis_x_list = pl.col("pelvis_x"),
        pelvis_z_list = pl.col("pelvis_z"),
    ).filter(
        pl.col("pelvis_x_list").list.len() >= 35
    )
    x_list = pc_df["pelvis_x_list"].to_list()
    z_list = pc_df["pelvis_z_list"].to_list()
    areas = []
    for x, z in zip(x_list, z_list):
        points = list(zip(x, z))
        area = shapely.Polygon(points).area
        areas.append(area)
    area_df = pl.DataFrame({"area": areas, "i_time": range(len(areas))})
    pc_df = pc_df.join(area_df, on="i_time", how="inner")
    pc_df = pc_df.select(
        f26 = pl.col("f26"),   
        f27 = pl.col("area"),
        i_time = pl.col("i_time")
    )
    out_df = features_from_df(pc_df)
    
    return out_df


def calculate_shape_component(df: pl.DataFrame) -> pl.DataFrame:
    cols = df.columns
    cols.remove("i_time")
    sc_df = df.select(
        pl.col("i_time")
    )
    for col in cols:
        extracted_df = df.select(
            pl.col(col).arr.get(0).alias(f'{col}_x'),
            pl.col(col).arr.get(1).alias(f'{col}_y'),
            pl.col(col).arr.get(2).alias(f'{col}_z'),
        )    
        sc_df = sc_df.hstack(extracted_df)
    sc_df = sc_df.with_columns(
        f18_max_x = pl.max_horizontal("Head_x", "LHand_x", "RHand_x", "LFoot_x", "RFoot_x"),
        f18_max_y = pl.max_horizontal("Head_y", "LHand_y", "RHand_y", "LFoot_y", "RFoot_y"),
        f18_max_z = pl.max_horizontal("Head_z", "LHand_z", "RHand_z", "LFoot_z", "RFoot_z"),
        f18_min_x = pl.min_horizontal("Head_x", "LHand_x", "RHand_x", "LFoot_x", "RFoot_x"),
        f18_min_y = pl.min_horizontal("Head_y", "LHand_y", "RHand_y", "LFoot_y", "RFoot_y"),
        f18_min_z = pl.min_horizontal("Head_z", "LHand_z", "RHand_z", "LFoot_z", "RFoot_z"),

        f19_max_x = pl.max_horizontal(pl.selectors.ends_with("_x")),
        f19_max_y = pl.max_horizontal(pl.selectors.ends_with("_y")),
        f19_max_z = pl.max_horizontal(pl.selectors.ends_with("_z")),
        f19_min_x = pl.min_horizontal(pl.selectors.ends_with("_x")),
        f19_min_y = pl.min_horizontal(pl.selectors.ends_with("_y")),
        f19_min_z = pl.min_horizontal(pl.selectors.ends_with("_z")),

        f20_max_x = pl.max_horizontal("Head_x", "Neck_x", "LShoulder_x", "RShoulder_x", "LCollar_x", "RCollar_x", "LElbow_x", "RElbow_x", "LWrist_x", "RWrist_x", "LHand_x", "RHand_x", "spine3_x", "spine2_x", "spine1_x"),
        f20_max_y = pl.max_horizontal("Head_y", "Neck_y", "LShoulder_y", "RShoulder_y", "LCollar_y", "RCollar_y", "LElbow_y", "RElbow_y", "LWrist_y", "RWrist_y", "LHand_y", "RHand_y", "spine3_y", "spine2_y", "spine1_y"),
        f20_max_z = pl.max_horizontal("Head_z", "Neck_z", "LShoulder_z", "RShoulder_z", "LCollar_z", "RCollar_z", "LElbow_z", "RElbow_z", "LWrist_z", "RWrist_z", "LHand_z", "RHand_z", "spine3_z", "spine2_z", "spine1_z"),
        f20_min_x = pl.min_horizontal("Head_x", "Neck_x", "LShoulder_x", "RShoulder_x", "LCollar_x", "RCollar_x", "LElbow_x", "RElbow_x", "LWrist_x", "RWrist_x", "LHand_x", "RHand_x", "spine3_x", "spine2_x", "spine1_x"),
        f20_min_y = pl.min_horizontal("Head_y", "Neck_y", "LShoulder_y", "RShoulder_y", "LCollar_y", "RCollar_y", "LElbow_y", "RElbow_y", "LWrist_y", "RWrist_y", "LHand_y", "RHand_y", "spine3_y", "spine2_y", "spine1_y"),
        f20_min_z = pl.min_horizontal("Head_z", "Neck_z", "LShoulder_z", "RShoulder_z", "LCollar_z", "RCollar_z", "LElbow_z", "RElbow_z", "LWrist_z", "RWrist_z", "LHand_z", "RHand_z", "spine3_z", "spine2_z", "spine1_z"),

        f21_max_x = pl.max_horizontal("Pelvis_x", "LHip_x", "RHip_x", "LKnee_x", "RKnee_x", "LAnkle_x", "RAnkle_x", "LFoot_x", "RFoot_x"),
        f21_max_y = pl.max_horizontal("Pelvis_y", "LHip_y", "RHip_y", "LKnee_y", "RKnee_y", "LAnkle_y", "RAnkle_y", "LFoot_y", "RFoot_y"),
        f21_max_z = pl.max_horizontal("Pelvis_z", "LHip_z", "RHip_z", "LKnee_z", "RKnee_z", "LAnkle_z", "RAnkle_z", "LFoot_z", "RFoot_z"),
        f21_min_x = pl.min_horizontal("Pelvis_x", "LHip_x", "RHip_x", "LKnee_x", "RKnee_x", "LAnkle_x", "RAnkle_x", "LFoot_x", "RFoot_x"),
        f21_min_y = pl.min_horizontal("Pelvis_y", "LHip_y", "RHip_y", "LKnee_y", "RKnee_y", "LAnkle_y", "RAnkle_y", "LFoot_y", "RFoot_y"),
        f21_min_z = pl.min_horizontal("Pelvis_z", "LHip_z", "RHip_z", "LKnee_z", "RKnee_z", "LAnkle_z", "RAnkle_z", "LFoot_z", "RFoot_z"),

        f22_max_x = pl.max_horizontal(pl.selectors.starts_with("R") & pl.selectors.ends_with("_x"), "Head_x", "spine3_x", "spine2_x", "spine1_x", "Pelvis_x"),
        f22_max_y = pl.max_horizontal(pl.selectors.starts_with("R") & pl.selectors.ends_with("_y"), "Head_y", "spine3_y", "spine2_y", "spine1_y", "Pelvis_y"),
        f22_max_z = pl.max_horizontal(pl.selectors.starts_with("R") & pl.selectors.ends_with("_z"), "Head_z", "spine3_z", "spine2_z", "spine1_z", "Pelvis_z"),
        f22_min_x = pl.min_horizontal(pl.selectors.starts_with("R") & pl.selectors.ends_with("_x"), "Head_x", "spine3_x", "spine2_x", "spine1_x", "Pelvis_x"),
        f22_min_y = pl.min_horizontal(pl.selectors.starts_with("R") & pl.selectors.ends_with("_y"), "Head_y", "spine3_y", "spine2_y", "spine1_y", "Pelvis_y"),
        f22_min_z = pl.min_horizontal(pl.selectors.starts_with("R") & pl.selectors.ends_with("_z"), "Head_z", "spine3_z", "spine2_z", "spine1_z", "Pelvis_z"),

        f23_max_x = pl.max_horizontal(pl.selectors.starts_with("L") & pl.selectors.ends_with("_x"), "Head_x", "spine3_x", "spine2_x", "spine1_x", "Pelvis_x"),
        f23_max_y = pl.max_horizontal(pl.selectors.starts_with("L") & pl.selectors.ends_with("_y"), "Head_y", "spine3_y", "spine2_y", "spine1_y", "Pelvis_y"),
        f23_max_z = pl.max_horizontal(pl.selectors.starts_with("L") & pl.selectors.ends_with("_z"), "Head_z", "spine3_z", "spine2_z", "spine1_z", "Pelvis_z"),
        f23_min_x = pl.min_horizontal(pl.selectors.starts_with("L") & pl.selectors.ends_with("_x"), "Head_x", "spine3_x", "spine2_x", "spine1_x", "Pelvis_x"),
        f23_min_y = pl.min_horizontal(pl.selectors.starts_with("L") & pl.selectors.ends_with("_y"), "Head_y", "spine3_y", "spine2_y", "spine1_y", "Pelvis_y"),
        f23_min_z = pl.min_horizontal(pl.selectors.starts_with("L") & pl.selectors.ends_with("_z"), "Head_z", "spine3_z", "spine2_z", "spine1_z", "Pelvis_z"),

        vec_f24_x = pl.col("Head_x") - pl.col("Pelvis_x"),
        vec_f24_y = pl.col("Head_y") - pl.col("Pelvis_y"),
        vec_f24_z = pl.col("Head_z") - pl.col("Pelvis_z"),

        avg_hand_y = pl.mean_horizontal("RHand_y", "LHand_y"),
    )
    sc_df = sc_df.select(
        f18 = (pl.col("f18_max_x") - pl.col("f18_min_x")) * (pl.col("f18_max_y") - pl.col("f18_min_y")) * (pl.col("f18_max_z") - pl.col("f18_min_z")),
        f19 = (pl.col("f19_max_x") - pl.col("f19_min_x")) * (pl.col("f19_max_y") - pl.col("f19_min_y")) * (pl.col("f19_max_z") - pl.col("f19_min_z")),
        f20 = (pl.col("f20_max_x") - pl.col("f20_min_x")) * (pl.col("f20_max_y") - pl.col("f20_min_y")) * (pl.col("f20_max_z") - pl.col("f20_min_z")),
        f21 = (pl.col("f21_max_x") - pl.col("f21_min_x")) * (pl.col("f21_max_y") - pl.col("f21_min_y")) * (pl.col("f21_max_z") - pl.col("f21_min_z")),
        f22 = (pl.col("f22_max_x") - pl.col("f22_min_x")) * (pl.col("f22_max_y") - pl.col("f22_min_y")) * (pl.col("f22_max_z") - pl.col("f22_min_z")),
        f23 = (pl.col("f23_max_x") - pl.col("f23_min_x")) * (pl.col("f23_max_y") - pl.col("f23_min_y")) * (pl.col("f23_max_z") - pl.col("f23_min_z")),
        f24 = (pl.col("vec_f24_x").pow(2) + pl.col("vec_f24_y").pow(2) + pl.col("vec_f24_z").pow(2)).sqrt(),
        f25_0 = pl.when(pl.col("avg_hand_y") > pl.col("Head_y")).then(pl.lit(1)).otherwise(0),
        f25_1 = pl.when(pl.col("avg_hand_y") < pl.col("Pelvis_y")).then(pl.lit(1)).otherwise(0),
        f25_2 = pl.when((pl.col("avg_hand_y") <= pl.col("Head_y")) & (pl.col("avg_hand_y") >= pl.col("Pelvis_y"))).then(pl.lit(1)).otherwise(0),
        i_time = pl.col("i_time")
    )
    out_df = features_from_df(sc_df, ["f25_0", "f25_1", "f25_2"])

    return out_df


def calculate_effort_component(df: pl.DataFrame) -> pl.DataFrame:
    ec_df = df.with_columns(
        pelvis_x = pl.col("Pelvis").arr.get(0),
        pelvis_y = pl.col("Pelvis").arr.get(1),
        pelvis_z = pl.col("Pelvis").arr.get(2),
        spine3_x = pl.col("spine3").arr.get(0),
        spine3_y = pl.col("spine3").arr.get(1),
        spine3_z = pl.col("spine3").arr.get(2),
        lhand_x = pl.col("LHand").arr.get(0),
        lhand_y = pl.col("LHand").arr.get(1),
        lhand_z = pl.col("LHand").arr.get(2),
        rhand_x = pl.col("RHand").arr.get(0),
        rhand_y = pl.col("RHand").arr.get(1),
        rhand_z = pl.col("RHand").arr.get(2),
        lfoot_x = pl.col("LFoot").arr.get(0),
        lfoot_y = pl.col("LFoot").arr.get(1),
        lfoot_z = pl.col("LFoot").arr.get(2),
        rfoot_x = pl.col("RFoot").arr.get(0),
        rfoot_y = pl.col("RFoot").arr.get(1),
        rfoot_z = pl.col("RFoot").arr.get(2),
    )
    ec_df = ec_df.with_columns(
        diff_pelvis_x = pl.col("pelvis_x").diff(),
        diff_pelvis_y = pl.col("pelvis_y").diff(),
        diff_pelvis_z = pl.col("pelvis_z").diff(),
        diff_spine3_x = pl.col("spine3_x").diff(),
        diff_spine3_y = pl.col("spine3_y").diff(),
        diff_spine3_z = pl.col("spine3_z").diff(),
        diff_lhand_x = pl.col("lhand_x").diff(),
        diff_lhand_y = pl.col("lhand_y").diff(),
        diff_lhand_z = pl.col("lhand_z").diff(),
        diff_rhand_x = pl.col("rhand_x").diff(),
        diff_rhand_y = pl.col("rhand_y").diff(),
        diff_rhand_z = pl.col("rhand_z").diff(),
        diff_lfoot_x = pl.col("lfoot_x").diff(),
        diff_lfoot_y = pl.col("lfoot_y").diff(),
        diff_lfoot_z = pl.col("lfoot_z").diff(),
        diff_rfoot_x = pl.col("rfoot_x").diff(),
        diff_rfoot_y = pl.col("rfoot_y").diff(),
        diff_rfoot_z = pl.col("rfoot_z").diff(),
    )
    ec_df = ec_df.with_columns(
        pelvis_dist = (pl.col("diff_pelvis_x").pow(2) + pl.col("diff_pelvis_y").pow(2) + pl.col("diff_pelvis_z").pow(2)).sqrt().abs(),
        spine3_dist = (pl.col("diff_spine3_x").pow(2) + pl.col("diff_spine3_y").pow(2) + pl.col("diff_spine3_z").pow(2)).sqrt().abs(),
        lhand_dist = (pl.col("diff_lhand_x").pow(2) + pl.col("diff_lhand_y").pow(2) + pl.col("diff_lhand_z").pow(2)).sqrt().abs(),
        rhand_dist = (pl.col("diff_rhand_x").pow(2) + pl.col("diff_rhand_y").pow(2) + pl.col("diff_rhand_z").pow(2)).sqrt().abs(),
        lfoot_dist = (pl.col("diff_lfoot_x").pow(2) + pl.col("diff_lfoot_y").pow(2) + pl.col("diff_lfoot_z").pow(2)).sqrt().abs(),
        rfoot_dist = (pl.col("diff_rfoot_x").pow(2) + pl.col("diff_rfoot_y").pow(2) + pl.col("diff_rfoot_z").pow(2)).sqrt().abs(),
    )
    ec_df = ec_df.group_by_dynamic("i_time", every="1i", period="10i").agg(
        f11 = pl.mean("pelvis_dist"),
        f12 = pl.mean("spine3_dist"),
        lf13 = pl.mean("lhand_dist"),
        rf13 = pl.mean("rhand_dist"),
        lf14 = pl.mean("lfoot_dist"),
        rf14 = pl.mean("rfoot_dist"),
    )
    ec_df = ec_df.with_columns(
        accel = pl.col("f11").diff(),
        f13 = pl.mean_horizontal("lf13", "rf13"),
        f14 = pl.mean_horizontal("lf14", "rf14"),
    )
    ec_df = ec_df.with_columns(
        f15 = pl.col("f11").diff(),
        f16 = pl.col("f12").diff(),
        f17 = pl.col("f13").diff(),
        f18 = pl.col("f14").diff(),
        f19 = pl.col("f11").diff().diff(),
    )
    ec_df = ec_df.filter(
        pl.col("f11").is_not_null(),
    )
    ec_df = ec_df.select(
        f11 = pl.col("f11"),
        f12 = pl.col("f12"),
        f13 = pl.col("f13"),
        f14 = pl.col("f14"),
        f15 = pl.col("f15"),
        f16 = pl.col("f16"),
        f17 = pl.col("f17"),
        f18 = pl.col("f18"),
        f19 = pl.col("f19"),
        i_time = pl.col("i_time"),
    )
    out_df = features_from_df(ec_df, [])

    return out_df


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
        i_time = pl.col("i_time")
    )
    out_df = features_from_df(bc_df)

    return out_df