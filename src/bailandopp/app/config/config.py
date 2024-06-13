reward_config = {"rate": 0}
optimizer_type = "Adam"
wav_padding = 5
move = 5
smpl_model_path = "./SMPL_MALE.pkl"
optimizer_kwargs = {
    "lr": 0.00001,
    "betas": [0.5, 0.999],
    "weight_decay": 0,
}
optimizer_schedular_kwargs = {
    "milestones": [40],
    "gamma": 1,
}
music_config = {
    "ds_rate": 1,
    "relative_rate": 1,
    "n_music": 55,
}
