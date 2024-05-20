import torch
import torch.nn as nn
import torch.optim as optim
import itertools
import numpy as np

from models.sep_vqvae_root_mix import SepVQVAERmix
from models.cross_cond_gpt2_music_window_ac import CrossCondGPT2MWAC
from models.up_down_half_reward import UpDownReward

class Bailando():
    def __init__(self, vqvae_config, gpt_config, config, device_name, vq_ckpt_dir=None, gpt_ckpt_dir=None):
        self.device = torch.device(device_name)
        self.start_epoch = 0
        self._build_model(vqvae_config, gpt_config, config.reward_config, self.device)
        if vq_ckpt_dir is not None:
            vqvae = self.vqvae
            # load VQVAE
            checkpoint = torch.load(vq_ckpt_dir, map_location=self.device)
            vqvae.load_state_dict(checkpoint['model'], strict=False)
            vqvae.eval()
            self.vqvae = vqvae
            self.vqvae_loaded = True
        else:
            self.vqvae_loaded = False
            
        if gpt_ckpt_dir is not None:
            gpt = self.gpt
            # load gpt
            checkpoint = torch.load(gpt_ckpt_dir, map_location=self.device)
            gpt.load_state_dict(checkpoint['model'])
            gpt.eval()
            self.gpt = gpt
            self.gpt_loaded = True
        else:
            self.gpt_loaded = False

        # self._build_optimizer(config)

    # Run evaluation on adhoc batch size = 1 data, and visualize to video. Wrapper for eval raw.
    def eval_raw_visualize(self, music_input, dance_input, dance_name, vq_ckpt_dir, gpt_ckpt_dir, music_config):
        music_input, dance_input = torch.tensor(music_input).unsqueeze(0), torch.tensor(dance_input).unsqueeze(0)
        results, quants = self.eval_raw(music_input, dance_input, music_config, 100, 0, vq_ckpt_dir, gpt_ckpt_dir)
        quants_map = {}
        quants_map[dance_name] = quants
        print("DONE")
        # visualizeAndWrite([results], self.config, self.evaldir, [dance_name], self.config.testing.ckpt_epoch, quants_map, device=self.device)

    # Run evaluation on adhoc batch size = 1 data. Return output from inference.
    def eval_raw(self, music_input, dance_input, music_config, length, start_frame_index, shift, vq_ckpt_dir=None, gpt_ckpt_dir=None):
       with torch.no_grad():
            vqvae = self.vqvae
            gpt = self.gpt

            # load VQVAE
            if self.vqvae_loaded is not True:
                checkpoint = torch.load(vq_ckpt_dir, map_location=self.device)
                vqvae.load_state_dict(checkpoint['model'], strict=False)
                vqvae = vqvae.eval()
            # load gpt
            if self.gpt_loaded is not True:
                checkpoint = torch.load(gpt_ckpt_dir, map_location=self.device)
                gpt.load_state_dict(checkpoint['model'])
                gpt = gpt.eval()

            return self.eval_single_epoch(vqvae, gpt, music_config, music_input, dance_input, shift, length, start_frame_index)
    
    def encode(self, x):
        with torch.no_grad():
            vqvae = self.vqvae
            return vqvae.module.encode(x)
        
    def decode(self, up, down):
        with torch.no_grad():
            vqvae = self.vqvae
            pose_sample = vqvae.module.decode((up, down))
            print(pose_sample.shape)

            # NOTE: previously this was checking if the global_vel value was true, and only then, do we run the below block.
            global_vel = pose_sample[:, :, :3].clone()
            pose_sample[:, 0, :3] = 0
            for iii in range(1, pose_sample.size(1)):
                pose_sample[:, iii, :3] = pose_sample[:, iii-1, :3] + global_vel[:, iii-1, :]

            return pose_sample

    def eval_single_epoch(self, vqvae, gpt, music_config, music_seq:torch.Tensor, pose_seq:torch.Tensor=None, shift=0, length=None, start_frame_index=0):
        # mps does not support float 64, so we cast to float32
        if self.device == torch.device('mps'):
            music_seq = music_seq.type(torch.float32)
        music_seq = music_seq.to(self.device)

        if pose_seq is not None:
            if self.device == torch.device('mps'):
                pose_seq = pose_seq.type(torch.float32)
            pose_seq = pose_seq.to(self.device)
            quants = vqvae.module.encode(pose_seq)
        else:
            quants = ([torch.ones(1, 1,).to(self.device).long() * 423], [torch.ones(1, 1,).to(self.device).long() * 12])
        if isinstance(quants, tuple):
            x = tuple(quants[i][0][:, :shift] for i in range(len(quants)))
        else:
            x = quants[0][:, :shift]

        music_ds_rate = music_config['ds_rate']
        music_relative_rate = music_config['relative_rate']

        music_seq = music_seq[:, :, :music_config['n_music'] // music_ds_rate ].contiguous().float()
        b, t, c = music_seq.size()
        music_seq = music_seq.view(b, t//music_ds_rate, c*music_ds_rate)
        music_seq = music_seq[:, music_ds_rate//music_relative_rate:]

        zs = gpt.module.sample(x, cond=music_seq, shift=shift, length=length)
        pose_sample = vqvae.module.decode(zs)

        # NOTE: previously this was checking if the global_vel value was true, and only then, do we run the below block.
        global_vel = pose_sample[:, :, :3].clone()
        pose_sample[:, 0, :3] = 0
        for iii in range(1, pose_sample.size(1)):
            pose_sample[:, iii, :3] = pose_sample[:, iii-1, :3] + global_vel[:, iii-1, :]

        if isinstance(zs, tuple):
            quants_out = tuple(zs[ii][0].cpu().data.numpy()[0] for ii in range(len(zs)))
        else:
            quants_out = zs[0].cpu().data.numpy()[0]
        return pose_sample, quants_out
        
    def _build_model(self, vqvae_config, gpt_config, reward_config, device=torch.device('cpu')):
        """ Define Model """
        vqvae = SepVQVAERmix(vqvae_config, device)
        gpt = CrossCondGPT2MWAC(gpt_config)
        reward = UpDownReward(reward_config)
        
        vqvae = nn.DataParallel(vqvae)
        gpt = nn.DataParallel(gpt)
        dance_reward = nn.DataParallel(reward)

        self.dance_reward = dance_reward.to(device)
        self.gpt = gpt.to(device)
        self.vqvae = vqvae.to(device)

    def _build_optimizer(self, config):
        try:
            optim = getattr(torch.optim, config.optimizer_type)
        except Exception:
            raise NotImplementedError(f"not implemented optim method { config.optimizer_type}")

        self.optimizer = optim(itertools.chain(self.gpt.module.parameters()) **config.optimizer_kwargs)
        self.schedular = torch.optim.lr_scheduler.MultiStepLR(self.optimizer, **config.optimizer_schedular_kwargs)
