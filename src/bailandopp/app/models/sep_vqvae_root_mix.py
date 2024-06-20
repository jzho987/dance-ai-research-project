import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from smplx import SMPL
from utils.torch_utils import matrix_to_axis_angle
from models.vqvae_mix import VQVAEmix
from models.vqvae_root_mix import VQVAERmix
import torch as t

smpl_down = [0, 1, 2, 4,  5, 7, 8, 10, 11]
smpl_up = [3, 6, 9, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]

def _loss_fn(x_target, x_pred):
    return torch.mean(torch.abs(x_pred - x_target)) 

def rotation_6d_to_matrix(d6: torch.Tensor) -> torch.Tensor:
    """
    Converts 6D rotation representation by Zhou et al. [1] to rotation matrix
    using Gram--Schmidt orthogonalization per Section B of [1].
    Args:
        d6: 6D rotation representation, of size (*, 6)

    Returns:
        batch of rotation matrices of size (*, 3, 3)

    [1] Zhou, Y., Barnes, C., Lu, J., Yang, J., & Li, H.
    On the Continuity of Rotation Representations in Neural Networks.
    IEEE Conference on Computer Vision and Pattern Recognition, 2019.
    Retrieved from http://arxiv.org/abs/1812.07035
    """

    a1, a2 = d6[..., :3], d6[..., 3:]
    b1 = F.normalize(a1, dim=-1)
    b2 = a2 - (b1 * a2).sum(-1, keepdim=True) * b1
    b2 = F.normalize(b2, dim=-1)
    b3 = torch.cross(b1, b2, dim=-1)
    return torch.stack((b1, b2, b3), dim=-2)


def matrix_to_rotation_6d(matrix: torch.Tensor) -> torch.Tensor:
    """
    Converts rotation matrices to 6D rotation representation by Zhou et al. [1]
    by dropping the last row. Note that 6D representation is not unique.
    Args:
        matrix: batch of rotation matrices of size (*, 3, 3)

    Returns:
        6D rotation representation, of size (*, 6)

    [1] Zhou, Y., Barnes, C., Lu, J., Yang, J., & Li, H.
    On the Continuity of Rotation Representations in Neural Networks.
    IEEE Conference on Computer Vision and Pattern Recognition, 2019.
    Retrieved from http://arxiv.org/abs/1812.07035
    """
    batch_dim = matrix.size()[:-2]
    return matrix[..., :2, :].clone().reshape(batch_dim + (6,))

class SepVQVAERmix(nn.Module):
    def __init__(self, hps, device_name):
        super().__init__()
        self.hps = hps
        self.device = torch.device(device_name)
        self.chanel_num = hps.joint_channel
        self.chanel_num_rot = hps.rot_channel
        print(self.chanel_num_rot, flush=True)
        self.vqvae_up = VQVAEmix(hps.up_half, len(smpl_up)*self.chanel_num, len(smpl_up)*self.chanel_num_rot)
        self.vqvae_down = VQVAERmix(hps.down_half, len(smpl_down)*self.chanel_num, len(smpl_down)*self.chanel_num_rot)
        self.use_6d_rotation = hps.use_6d_rotation if hasattr(hps, 'use_6d_rotation') else False
        if self.use_6d_rotation:
            assert(self.chanel_num_rot == 6)
        
        self.smpl_weight = hps.smpl_weight if hasattr(hps, 'smpl_weight') else 0
        if self.smpl_weight > 0:
            self.smpl = SMPL(model_path='/mnt/lustre/syli/dance/Bailando/smpl', gender='MALE', batch_size=1).eval()

    def matrix_to_smpl(self, matrix):
        n, t = matrix.size()[:2]
        matrix = matrix.view(n*t, 24, 3, 3)
        
        aa = matrix_to_axis_angle(matrix)

        pos3d = self.smpl.eval().forward(
            global_orient=aa[:, 0:1].float(),
            body_pose=aa[:, 1:].float(),
        ).joints[:, 0:24, :]

        return pos3d.view(n, t, 24, 3)

    def decode(self, zs, start_level=0, end_level=None, bs_chunks=1):
        """
        zs are list with two elements: z for up and z for down
        """
        if isinstance(zs, tuple):
            zup = zs[0]
            zdown = zs[1]
        else:
            zup = zs
            zdown = zs
        xup = self.vqvae_up.decode(zup)
        xdown, xvel = self.vqvae_down.decode(zdown)
        b, t, cup = xup.size()
        _, _, cdown = xdown.size()
        x = torch.zeros(b, t, (cup+cdown)//self.chanel_num_rot, self.chanel_num_rot, device=self.device)
        x[:, :, smpl_up] = xup.view(b, t, cup//self.chanel_num_rot, self.chanel_num_rot)
        x[:, :, smpl_down] = xdown.view(b, t, cdown//self.chanel_num_rot, self.chanel_num_rot)

        if self.use_6d_rotation:
            x = rotation_6d_to_matrix(x)
        
        return torch.cat([xvel, x.view(b, t, -1)], dim=2)

    def encode(self, x, start_level=0, end_level=None, bs_chunks=1):
        x[:, :, :3] = 0
        b, t, c = x.size()
        zup = self.vqvae_up.encode(x.view(b, t, c//self.chanel_num, self.chanel_num)[:, :, smpl_up].view(b, t, -1), start_level, end_level, bs_chunks)
        zdown = self.vqvae_down.encode(x.view(b, t, c//self.chanel_num, self.chanel_num)[:, :, smpl_down].view(b, t, -1), start_level, end_level, bs_chunks)
        return (zup, zdown)

    def sample(self, n_samples):
        xup = self.vqvae_up.sample(n_samples)
        xdown, xvel = self.vqvae_down.sample(n_samples)
        b, t, cup = xup.size()
        _, _, cdown = xdown.size()
        x = torch.zeros(b, t, (cup+cdown)//self.chanel_num_rot, self.chanel_num_rot, device=self.device)
        x[:, :, smpl_up] = xup.view(b, t, cup//self.chanel_num_rot, self.chanel_num_rot)
        x[:, :, smpl_down] = xdown.view(b, t, cdown//self.chanel_num_rot, self.chanel_num_rot)

        return torch.cat([xvel, xdown.view(b, t, -1)], dim=2)

    def forward(self, x, x_rot):
        b, t, c = x.size()

        x_vel = x_rot[:, :, :3]
        x[:, :, :3] = 0
        x_rot = x_rot[:, :, 3:]

        x = x.view(b, t, c//self.chanel_num, self.chanel_num)
        xup = x[:, :, smpl_up, :].view(b, t, -1)
        xdown = x[:, :, smpl_down, :].view(b, t, -1)

        b, t, c = x_rot.size()
        
        x_rot = x_rot.view(b, t, c//9, 3, 3)
        x_rot33 = x_rot.view(b, t, c//9, 3, 3).clone().detach()
        if self.use_6d_rotation:
            x_rot = matrix_to_rotation_6d(x_rot)
    
        xup_rot = x_rot[:, :, smpl_up, :].view(b, t, -1)
        xdown_rot = x_rot[:, :, smpl_down, :].view(b, t, -1)

        x_out_up, loss_up, metrics_up = self.vqvae_up(xup, xup_rot)
        x_out_down, x_out_vel, loss_down , metrics_down  = self.vqvae_down(xdown, xdown_rot, x_vel)

        _, _, cup = x_out_up.size()
        _, _, cdown = x_out_down.size()

        xout = torch.zeros(b, t, (cup+cdown)//self.chanel_num_rot, self.chanel_num_rot, device=self.device).float()
        xout[:, :, smpl_up] = xout[:, :, smpl_up] + x_out_up.view(b, t, cup//self.chanel_num_rot, self.chanel_num_rot)
        xout[:, :, smpl_down] = xout[:, :, smpl_down] + x_out_down.view(b, t, cdown//self.chanel_num_rot, self.chanel_num_rot)

        if self.use_6d_rotation:
            xout_mat = rotation_6d_to_matrix(xout)
        else:
            xout_mat = xout
        
        loss = (loss_up + loss_down)*0.5
        if self.smpl_weight > 0:
            self.smpl.eval()
            with torch.no_grad():
                pos3d_gt = self.matrix_to_smpl(x_rot33)
            pos3d = self.matrix_to_smpl(xout_mat)
            loss += self.smpl_weight * _loss_fn(pos3d_gt, pos3d)
            
        xout_mat = torch.cat([x_out_vel, xout_mat.view(b, t , -1)], dim=2)

        return xout_mat.view(b, t, -1), loss, [metrics_up, metrics_down] 
