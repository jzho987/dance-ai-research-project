import torch
import numpy as np
from scipy.spatial.transform import Rotation as R


def rotmat2aa(rotmats):
    """
    Convert rotation matrices to angle-axis using opencv's Rodrigues formula.
    Args:
        rotmats: A np array of shape (..., 3, 3)
    Returns:
        A np array of shape (..., 3)
    """
    assert rotmats.shape[-1] == 3 and rotmats.shape[-2] == 3 and len(rotmats.shape) >= 3, 'invalid input dimension'
    orig_shape = rotmats.shape[:-2]
    rots = np.reshape(rotmats, [-1, 3, 3])
    r = R.from_matrix(rots)  # from_matrix
    aas = r.as_rotvec()
    return np.reshape(aas, orig_shape + (3,))


def get_closest_rotmat(rotmats):
    """
    Finds the rotation matrix that is closest to the inputs in terms of the Frobenius norm. For each input matrix
    it computes the SVD as R = USV' and sets R_closest = UV'. Additionally, it is made sure that det(R_closest) == 1.
    Args:
        rotmats: np array of shape (..., 3, 3).
    Returns:
        A numpy array of the same shape as the inputs.
    """
    u, s, vh = np.linalg.svd(rotmats)
    r_closest = np.matmul(u, vh)

    # if the determinant of UV' is -1, we must flip the sign of the last column of u
    det = np.linalg.det(r_closest)  # (..., )
    iden = eye(3, det.shape)
    iden[..., 2, 2] = np.sign(det)
    r_closest = np.matmul(np.matmul(u, iden), vh)
    return r_closest


def eye(n, batch_shape):
    iden = np.zeros(np.concatenate([batch_shape, [n, n]]))
    iden[..., 0, 0] = 1.0
    iden[..., 1, 1] = 1.0
    iden[..., 2, 2] = 1.0
    return iden


def format_rotmat_output(result, smpl):
    np_dances_rotmat = []
    np_dance = np.array(result)
    np_dances_rotmat.append(np_dance)
    root = np_dance[:, :3]
    rotmat = np_dance[:, 3:].reshape([-1, 3, 3])

    rotmat = get_closest_rotmat(rotmat)
    smpl_poses = rotmat2aa(rotmat).reshape(-1, 24, 3)
    np_dance = smpl.forward(
        global_orient=torch.from_numpy(smpl_poses[:, 0:1]).float(),
        body_pose=torch.from_numpy(smpl_poses[:, 1:]).float(),
        transl=torch.from_numpy(root).float(),
    ).joints.detach().numpy()[:, 0:24, :]
    b = np_dance.shape[0]
    np_dance = np_dance.reshape(b, -1)

    nn, cc = np_dance.shape
    np_dance = np_dance.reshape((nn, cc//3, 3))
    roott = np_dance[:1, :1]  # the root
    np_dance = (np_dance - roott).reshape((nn, cc))
    
    return np_dance.tolist()