import h5py
import os
import json
from tqdm import tqdm
import smplx
import numpy as np
import torch

from smplify import SMPLify3D


def main(input_file: str, output_path: str, smpl_model_path: str, smpl_mean_path: str, batch_size: int):
    device = torch.device("mps")
    with open(input_file) as f:
        data = json.loads(f.read())
    data = np.array(data)
    data = data.reshape(-1, 24, 3)
    smplmodel = smplx.create(
            smpl_model_path,
            model_type="smplx",
            gender="MALE",
            ext="pkl",
            batch_size=batch_size
        ).to(device)
    smplify = SMPLify3D(smplxmodel=smplmodel, batch_size=1, num_iters=1, device=device)

    # init values
    file = h5py.File(smpl_mean_path, 'r')
    init_mean_pose = torch.from_numpy(file['pose'][:]).unsqueeze(0).float()
    init_mean_shape = torch.from_numpy(file['shape'][:]).unsqueeze(0).float()
    cam_trans_zero = torch.Tensor([0.0, 0.0, 0.0]).to(device)
    pred_pose = torch.zeros(batch_size, 72).to(device)
    pred_betas = torch.zeros(batch_size, 10).to(device)
    pred_cam_t = torch.zeros(batch_size, 3).to(device)
    keypoints_3d = torch.zeros(batch_size, 24, 3).to(device)

    # process
    out_dict = {'beta':[], 'pose': [], 'cam': [], 'root': []}
    frames = data.shape[0]
    for i, _ in enumerate(tqdm(range(frames))):
        joints3d = data[i] #*1.2 #scale problem [check first]	
        keypoints_3d[0, :, :] = torch.Tensor(joints3d).to(device).float()

        if i == 0:
            pred_betas[0, :] = init_mean_shape
            pred_pose[0, :] = init_mean_pose
            pred_cam_t[0, :] = cam_trans_zero
        else:
            # param: set on 1st it, and can be used after
            pred_betas[0, :] = torch.from_numpy(param['beta']).unsqueeze(0).float()
            pred_pose[0, :] = torch.from_numpy(param['pose']).unsqueeze(0).float()
            pred_cam_t[0, :] = torch.from_numpy(param['cam']).unsqueeze(0).float()
            
        out = smplify( pred_pose.detach(),
                pred_betas.detach(),
                pred_cam_t.detach(),
                keypoints_3d,
                seq_ind=i
            )
        _, _, new_opt_pose, new_opt_betas, new_opt_cam_t, _ = out
        # save the pkl
        param = {}
        param['beta'] = new_opt_betas.detach().cpu().numpy()
        param['pose'] = new_opt_pose.detach().cpu().numpy()
        param['cam'] = new_opt_cam_t.detach().cpu().numpy()

        out_dict['beta'].append(new_opt_betas.detach().cpu().numpy().tolist())
        out_dict['pose'].append(new_opt_pose.detach().cpu().numpy().tolist())
        out_dict['cam'].append(new_opt_cam_t.detach().cpu().numpy().tolist())
        root_position = keypoints_3d[0, 0, :].detach().cpu().numpy().tolist()
        out_dict['root'].append(root_position)
	
    full_path = os.path.join(output_path, f'file_{i}.json')
    with open(full_path, "w") as f:
        f.write(json.dumps(out_dict))

if __name__ == "__main__":

    # param
    input_file = "pregen_1.json"
    output_path = "./output"
    smpl_model_path = "../app/SMPL_MALE.pkl"
    smpl_mean_path = "./smpl_models/neutral_smpl_mean_params.h5"
    batch_size = 1
    main(input_file,
        output_path,
        smpl_model_path,
        smpl_mean_path,
        batch_size)