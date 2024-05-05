block_size = 29
music_trans = {
    "window_size": 11,
    "n_music": 55,
    "embd_pdrop": 0.1,
    "resid_pdrop": 0.1,
    "attn_pdrop": 0.1,
    "n_layer": 3,
    "n_embd": 768,
    "downsample_rate": 8,
    "block_size": 29,
    "n_head": 12,
    "n_music_emb": 768,
    }
base = {
    "embd_pdrop": 0.1,
    "resid_pdrop": 0.1,
    "attn_pdrop": 0.1,
    "vocab_size_up": 512,
    "vocab_size_down": 512,
    "block_size": 29,
    "n_layer": 6,
    "n_head": 12,
    "n_embd": 768 ,
    "n_music": 768,
    "n_music_emb": 768,
    }
head = {
    "embd_pdrop": 0.1,
    "resid_pdrop": 0.1,
    "attn_pdrop": 0.1,
    "vocab_size": 512,
    "block_size": 29,
    "n_layer": 6,
    "n_head": 12,
    "n_embd": 768,
    "vocab_size_up": 512,
    "vocab_size_down": 512,
    }
critic_net = {
    "embd_pdrop": 0.,
    "resid_pdrop": 0.,
    "attn_pdrop": 0.,
    "block_size": 29,
    "n_layer": 3,
    "n_head": 12,
    "n_embd": 768,
    "vocab_size_up": 1,
    "vocab_size_down": 1,
    }
n_music: 55
n_music_emb: 768