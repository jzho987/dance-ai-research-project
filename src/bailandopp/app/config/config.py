reward_config = {"rate": 0}
optimizer_type = "Adam"
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
