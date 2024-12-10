# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this open-source project.


""" This script handling the training process. """
import os
import random
import torch
import torch.nn as nn
import torch.utils.data
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm
import itertools
import numpy as np
import models
import datetime
from models_v1.sep_vqvae_root import SepVQVAER
from models_v1.cross_cond_gpt2_nm import CrossCondGPT2NoMusic
import torch.nn.functional as F
import matplotlib.pyplot as plt



class BailandoV1():
    def __init__(self, vqvae_cfg, gpt_cfg, cfg, device, vq_ckpt_dir, gpt_ckpt_dir):
        self.config = cfg
        self.device = torch.device(device)
        torch.backends.cudnn.benchmark = True

        vqvae = SepVQVAER(vqvae_cfg)
        vqvae = nn.DataParallel(vqvae)
        checkpoint = torch.load(vq_ckpt_dir, map_location=self.device)
        vqvae.load_state_dict(checkpoint['model'], strict=False)
        self.vqvae = vqvae.to(self.device).eval()
        
        gpt = CrossCondGPT2NoMusic(gpt_cfg)
        gpt = nn.DataParallel(gpt)
        checkpoint = torch.load(gpt_ckpt_dir, map_location=self.device)
        gpt.load_state_dict(checkpoint['model'])
        self.gpt = gpt.to(self.device).eval()


    # Run evaluation on adhoc batch size = 1 data. Return output from inference.
    def eval_raw(self, dance_input, length, start_frame_index, shift):
       with torch.no_grad():
            vqvae = self.vqvae
            gpt = self.gpt
            return self.eval_single_epoch(vqvae, gpt, dance_input, shift, length, start_frame_index)


    def eval_single_epoch(self, vqvae, gpt, pose_seq:torch.Tensor, shift=0, length=None, start_frame_index=0):
        # mps does not support float 64, so we cast to float32
        if self.device == torch.device('mps'):
            pose_seq = pose_seq.type(torch.float32)
        pose_seq = pose_seq.to(self.device)
        quants = vqvae.module.encode(pose_seq)
        
        if isinstance(quants, tuple):
            x = tuple(quants[i][0][:, :shift] for i in range(len(quants)))
        else:
            x = quants[0][:, :shift]

        zs = gpt.module.sample(x, shift=shift, length=length)
        pose_sample = vqvae.module.decode(zs)
        print(f"pose sample shape {pose_sample.shape}")

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


    def analyze_code(self,):
        config = self.config
        print("Analyzing codebook")

        epoch_tested = config.testing.ckpt_epoch
        ckpt_path = os.path.join(self.ckptdir, f"epoch_{epoch_tested}.pt")
        checkpoint = torch.load(ckpt_path)
        self.vqvae.load_state_dict(checkpoint['model'])
        model = self.vqvae.eval()

        training_data = self.training_data
        all_quants = None

        torch.cuda.manual_seed(config.seed)
        self.device = torch.device('cuda' if config.cuda else 'cpu')
        random_id = 0  # np.random.randint(0, 1e4)
        
        for i_eval, batch_eval in enumerate(tqdm(self.training_data, desc='Generating Dance Poses')):
            # Prepare data
            # pose_seq_eval = map(lambda x: x.to(self.device), batch_eval)
            pose_seq_eval = batch_eval.to(self.device)

            quants = model.module.encode(pose_seq_eval)[0].cpu().data.numpy()
            all_quants = np.append(all_quants, quants.reshape(-1)) if all_quants is not None else quants.reshape(-1)

        print(all_quants)
                    # exit()
        # visualizeAndWrite(results, config,self.gtdir, self.dance_names, 0)
        plt.hist(all_quants, bins=config.structure.l_bins, range=[0, config.structure.l_bins])

        #图片的显示及存储
        #plt.show()   #这个是图片显示
        log = datetime.datetime.now().strftime('%Y-%m-%d')
        plt.savefig(self.histdir1 + '/hist_epoch_' + str(epoch_tested)  + '_%s.jpg' % log)   #图片的存储
        plt.close()

    def sample(self,):
        config = self.config
        print("Analyzing codebook")

        epoch_tested = config.testing.ckpt_epoch
        ckpt_path = os.path.join(self.ckptdir, f"epoch_{epoch_tested}.pt")
        checkpoint = torch.load(ckpt_path)
        self.vqvae.load_state_dict(checkpoint['model'])
        model = self.vqvae.eval()

        quants = {}

        results = []

        if hasattr(config, 'analysis_array') and config.analysis_array is not None:
            # print(config.analysis_array)
            names = [str(ii) for ii in config.analysis_array]
            print(names)
            for ii in config.analysis_array:
                print(ii)
                zs =  [(ii * torch.ones((1, self.config.sample_code_length), device='cuda')).long()]
                print(zs[0].size())
                pose_sample = model.module.decode(zs)
                if config.global_vel:
                    global_vel = pose_sample[:, :, :3]
                    pose_sample[:, 0, :3] = 0
                    for iii in range(1, pose_sample.size(1)):
                        pose_sample[:, iii, :3] = pose_sample[:, iii-1, :3] + global_vel[:, iii-1, :]

                quants[str(ii)] = zs[0].cpu().data.numpy()[0]

                results.append(pose_sample)
        else:
            names = ['rand_seq_' + str(ii) for ii in range(10)]
            for ii in range(10):
                zs = [torch.randint(0, self.config.structure.l_bins, size=(1, self.config.sample_code_length), device='cuda')]
                pose_sample = model.module.decode(zs)
                quants['rand_seq_' + str(ii)] = zs[0].cpu().data.numpy()[0]
                if config.global_vel:
                    global_vel = pose_sample[:, :, :3]
                    pose_sample[:, 0, :3] = 0
                    for iii in range(1, pose_sample.size(1)):
                        pose_sample[:, iii, :3] = pose_sample[:, iii-1, :3] + global_vel[:, iii-1, :]
                results.append(pose_sample)
        visualizeAndWrite(results, config, self.sampledir, names, epoch_tested, quants)


    def _build_train_loader(self):
        data = self.config.data
        print("building training set")
        fnames = os.listdir(data.train_dir)
        train_dance_data = []
        for name in tqdm(fnames):
            path = os.path.join(data.train_dir, name)
            np_dance = np.load(path)
            train_dance_data.append(np_dance)
        print(f"data loaded: {len(train_dance_data)}")

        self.training_data = prepare_dataloader(train_dance_data, self.config.batch_size)



    def _build_test_loader(self):
        data = self.config.data
        print("building testing set")
        fnames = os.listdir(data.test_dir)
        test_dance_data = []
        for name in tqdm(fnames):
            path = os.path.join(data.test_dir, name)
            np_dance = np.load(path)[:896]
            test_dance_data.append(np_dance)
        print(f"data loaded: {len(test_dance_data)}")

        self.testing_data = prepare_dataloader(test_dance_data, self.config.batch_size)


    def _build_optimizer(self):
        #model = nn.DataParallel(model).to(device)
        config = self.config.optimizer
        try:
            optim = getattr(torch.optim, config.type)
        except Exception:
            raise NotImplementedError('not implemented optim method ' + config.type)

        self.optimizer = optim(itertools.chain(self.gpt.module.parameters(),
                                             ),
                                             **config.kwargs)


    def _dir_setting(self):
        data = self.config.data
        self.expname = self.config.expname
        self.experiment_dir = os.path.join("./", "experiments")
        self.expdir = os.path.join(self.experiment_dir, self.expname)

        if not os.path.exists(self.expdir):
            os.mkdir(self.expdir)

        self.visdir = os.path.join(self.expdir, "vis")  # -- imgs, videos, jsons
        if not os.path.exists(self.visdir):
            os.mkdir(self.visdir)

        self.jsondir = os.path.join(self.visdir, "jsons")  # -- imgs, videos, jsons
        if not os.path.exists(self.jsondir):
            os.mkdir(self.jsondir)

        self.histdir = os.path.join(self.visdir, "hist")  # -- imgs, videos, jsons
        if not os.path.exists(self.histdir):
            os.mkdir(self.histdir)

        self.imgsdir = os.path.join(self.visdir, "imgs")  # -- imgs, videos, jsons
        if not os.path.exists(self.imgsdir):
            os.mkdir(self.imgsdir)

        self.videodir = os.path.join(self.visdir, "videos")  # -- imgs, videos, jsons
        if not os.path.exists(self.videodir):
            os.mkdir(self.videodir)
        
        self.ckptdir = os.path.join(self.expdir, "ckpt")
        if not os.path.exists(self.ckptdir):
            os.mkdir(self.ckptdir)

        self.evaldir = os.path.join(self.expdir, "eval")
        if not os.path.exists(self.evaldir):
            os.mkdir(self.evaldir)

        self.gtdir = os.path.join(self.expdir, "gt")
        if not os.path.exists(self.gtdir):
            os.mkdir(self.gtdir)

        self.jsondir1 = os.path.join(self.evaldir, "jsons")  # -- imgs, videos, jsons
        if not os.path.exists(self.jsondir1):
            os.mkdir(self.jsondir1)

        self.histdir1 = os.path.join(self.evaldir, "hist")  # -- imgs, videos, jsons
        if not os.path.exists(self.histdir1):
            os.mkdir(self.histdir1)

        self.imgsdir1 = os.path.join(self.evaldir, "imgs")  # -- imgs, videos, jsons
        if not os.path.exists(self.imgsdir1):
            os.mkdir(self.imgsdir1)

        self.videodir1 = os.path.join(self.evaldir, "videos")  # -- imgs, videos, jsons
        if not os.path.exists(self.videodir1):
            os.mkdir(self.videodir1)

        self.sampledir = os.path.join(self.evaldir, "samples")  # -- imgs, videos, jsons
        if not os.path.exists(self.sampledir):
            os.mkdir(self.sampledir)


def prepare_dataloader(dance_data, batch_size):
    modata = MoSeq(dance_data)
    sampler = torch.utils.data.RandomSampler(modata, replacement=True)
    data_loader = torch.utils.data.DataLoader(
        modata,
        num_workers=8,
        batch_size=batch_size,
        sampler=sampler,
        pin_memory=True
    )

    return data_loader
