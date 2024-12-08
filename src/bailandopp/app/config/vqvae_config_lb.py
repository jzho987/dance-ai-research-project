up_half = {
    "levels": 1,
    "device": "cuda",
    "downs_t": [3,],
    "strides_t" : [2,],
    "emb_width" : 512,
    "l_bins" : 2048,
    "l_mu" : 0.99,
    "commit" : 0.02,
    "hvqvae_multipliers" : [1,],
    "width": 512,
    "depth": 3,
    "m_conv" : 1.0,
    "dilation_growth_rate" : 3,
    "sample_length": 240,
    "use_bottleneck": True,
    "joint_channel": 3,
    "vel": 1,
    "acc": 1,
    "vqvae_reverse_decoder_dilation": True,
    }
down_half = {
    "levels": 1,
    "device": "cuda",
    "downs_t": [3,],
    "strides_t" : [2,],
    "emb_width" : 512,
    "l_bins" : 2048,
    "l_mu" : 0.99,
    "commit" : 0.02,
    "hvqvae_multipliers" : [1,],
    "width": 512,
    "depth": 3,
    "m_conv" : 1.0,
    "dilation_growth_rate" : 3,
    "sample_length": 240,
    "use_bottleneck": True,
    "joint_channel": 3,
    "vel": 1,
    "acc": 1,
    "vqvae_reverse_decoder_dilation": True,
    }
use_bottleneck = True,
use_6d_rotation = False
device = "cuda"
joint_channel = 3
rot_channel = 9
l_bins = 2048