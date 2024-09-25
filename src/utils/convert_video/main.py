import torch
import numpy as np
import json
from smplx import SMPL
from PIL import Image
from multiprocessing import Pool
from functools import partial
from easydict import EasyDict
from scipy.spatial.transform import Rotation as R
import os
import shutil
import argparse

from keypoint2img import read_keypoints

TMP_DIR_JSON = "./.tmp_json"
TMP_DIR_IMAGE =  "./.tmp_img"

def eye(n, batch_shape):
    iden = np.zeros(np.concatenate([batch_shape, [n, n]]))
    iden[..., 0, 0] = 1.0
    iden[..., 1, 1] = 1.0
    iden[..., 2, 2] = 1.0
    return iden


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


pose_keypoints_num = 25
face_keypoints_num = 70
hand_left_keypoints_num = 21
hand_right_keypoints_num = 21



def generate(model, src_aud, src_aud_pos, src_pos, src_pos_pos):
    """ Generate dance pose in one batch """
    with torch.no_grad():

        # attention: AIST++这篇paper将2s的动作也作为输入，所以需要滚动预测

        bsz, src_seq_len, _ = src_aud.size()
        _, _ , pose_dim = src_pos.size()

        # 前120帧作为输入
        generated_frames_num = src_seq_len - 120
        
        # 像后面补充120帧保证预测完整
        # for ii in range(120):
        src_aud = torch.cat([src_aud, src_aud[:, :120]], dim=1)
        
        # 输出motion先加上前120帧motion
        out_seq = src_pos.clone()

        


        for i in range(0, generated_frames_num, 1):

            output = model(src_aud[:, i:i+240], src_aud_pos[:, :240], out_seq[:, i:i+120], src_pos_pos[:, :240])

            if generated_frames_num - i < 1:
                print('the last frame!')
                output = output[:, :1]
            else:
                output = output[:, :1]
            out_seq = torch.cat([out_seq, output], 1)

    out_seq = out_seq[:, :].view(bsz, -1, pose_dim)

    return out_seq

def img_to_video_with_audio(input_dir, output_dir, music_path, name="untitled_video"):
    if not (os.path.exists(output_dir) and os.path.isdir(output_dir)):
        os.makedirs(output_dir)

    # vars
    full_output_path_with_suffix_video = f'{output_dir}/{name}.mp4'
    full_output_path_with_suffix_video_with_music = f'{output_dir}/{name}_audio.mp4'
    
    # execute generate video shell command
    cmd = f"ffmpeg -r 60 -i {input_dir}/frame%06d.png -vb 20M -vcodec mpeg4 -y {full_output_path_with_suffix_video} -loglevel quiet"
    os.system(cmd)
    
    # execute shell command to append audio
    cmd_audio = f"ffmpeg -i {full_output_path_with_suffix_video} -i {music_path} -map 0:v -map 1:a -c:v copy -shortest -y {full_output_path_with_suffix_video_with_music } -loglevel quiet"
    os.system(cmd_audio)


def to_json(dance, output_dir, width, height, ):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    num_poses = dance.shape[0]
    dance = dance.reshape(num_poses, pose_keypoints_num, 2)

    for j in range(num_poses):
        frame_dict = {'version': 1.2}
        # 2-D key points
        pose_keypoints_2d = []
        # Random values for the below key points
        face_keypoints_2d = []
        hand_left_keypoints_2d = []
        hand_right_keypoints_2d = []
        # 3-D key points
        pose_keypoints_3d = []
        face_keypoints_3d = []
        hand_left_keypoints_3d = []
        hand_right_keypoints_3d = []

        keypoints = dance[j]
        for k, keypoint in enumerate(keypoints):
            x = (keypoint[0] + 1) * 0.5 * width
            y = (keypoint[1] + 1) * 0.5 * height
            score = 0.8
            if k < pose_keypoints_num:
                pose_keypoints_2d.extend([x, y, score])
            elif k < pose_keypoints_num + face_keypoints_num:
                face_keypoints_2d.extend([x, y, score])
            elif k < pose_keypoints_num + face_keypoints_num + hand_left_keypoints_num:
                hand_left_keypoints_2d.extend([x, y, score])
            else:
                hand_right_keypoints_2d.extend([x, y, score])

        people_dicts = []
        people_dict = {'pose_keypoints_2d': pose_keypoints_2d,
                        'face_keypoints_2d': face_keypoints_2d,
                        'hand_left_keypoints_2d': hand_left_keypoints_2d,
                        'hand_right_keypoints_2d': hand_right_keypoints_2d,
                        'pose_keypoints_3d': pose_keypoints_3d,
                        'face_keypoints_3d': face_keypoints_3d,
                        'hand_left_keypoints_3d': hand_left_keypoints_3d,
                        'hand_right_keypoints_3d': hand_right_keypoints_3d}
        people_dicts.append(people_dict)
        frame_dict['people'] = people_dicts
        frame_json = json.dumps(frame_dict)
        with open(os.path.join(output_dir, f'frame{j:06d}_kps.json'), 'w') as f:
            f.write(frame_json)


def visualize_json(fname_iter, dance_path, output_path, width, height):
    j, fname = fname_iter
    json_file = os.path.join(dance_path, fname)
    img = Image.fromarray(read_keypoints(json_file, (width, height),
                                         remove_face_labels=False, basic_point_only=False))
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img = np.asarray(img)
    # cv2.putText(img, str(quant[j]), (width-400, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    img = Image.fromarray(np.uint8(img))
    img.save(os.path.join(output_path, f'frame{j:06d}.png'))


def json_to_img(input_dir, output_dir, width, height, worker_num=16):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    fnames = sorted(os.listdir(input_dir))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Visualize json in parallel
    pool = Pool(worker_num)
    partial_func = partial(visualize_json, dance_path=input_dir, output_path=output_dir, width=width, height=height)
    pool.map(partial_func, enumerate(fnames))
    pool.close()
    pool.join()


def visualizeAndWrite(np_dance, output_dir, music_path, name):
    b, c = np_dance.shape
    np_dance = np_dance.reshape([b, c//3, 3])
    np_dance2 = np_dance[:, :, :2] / 1.5
    np_dance2[:, :, 0] /= 2.2
    # np_dance2[:, :, 1] -= 0.6
    np_dance_trans = np.zeros([b, 25, 2]).copy()
    
    # head
    np_dance_trans[:, 0] = np_dance2[:, 12]
    
    #neck
    np_dance_trans[:, 1] = np_dance2[:, 9]
    
    # left up
    np_dance_trans[:, 2] = np_dance2[:, 16]
    np_dance_trans[:, 3] = np_dance2[:, 18]
    np_dance_trans[:, 4] = np_dance2[:, 20]

    # right up
    np_dance_trans[:, 5] = np_dance2[:, 17]
    np_dance_trans[:, 6] = np_dance2[:, 19]
    np_dance_trans[:, 7] = np_dance2[:, 21]

    
    np_dance_trans[:, 8] = np_dance2[:, 0]
    
    np_dance_trans[:, 9] = np_dance2[:, 1]
    np_dance_trans[:, 10] = np_dance2[:, 4]
    np_dance_trans[:, 11] = np_dance2[:, 7]

    np_dance_trans[:, 12] = np_dance2[:, 2]
    np_dance_trans[:, 13] = np_dance2[:, 5]
    np_dance_trans[:, 14] = np_dance2[:, 8]

    np_dance_trans[:, 15] = np_dance2[:, 15]
    np_dance_trans[:, 16] = np_dance2[:, 15]
    np_dance_trans[:, 17] = np_dance2[:, 15]
    np_dance_trans[:, 18] = np_dance2[:, 15]

    np_dance_trans[:, 19] = np_dance2[:, 11]
    np_dance_trans[:, 20] = np_dance2[:, 11]
    np_dance_trans[:, 21] = np_dance2[:, 8]

    np_dance_trans[:, 22] = np_dance2[:, 10]
    np_dance_trans[:, 23] = np_dance2[:, 10]
    np_dance_trans[:, 24] = np_dance2[:, 7]

    np_dance_result = np_dance_trans.reshape([b, 25*2])
    # end of loop

    to_json(np_dance_result, TMP_DIR_JSON, width=960, height=540)
    json_to_img(TMP_DIR_JSON, TMP_DIR_IMAGE, width=960, height=540)
    img_to_video_with_audio(TMP_DIR_IMAGE, output_dir, music_path, name=name)

    # clean up temp folder
    if os.path.exists(TMP_DIR_JSON):
        shutil.rmtree(TMP_DIR_JSON)
    if os.path.exists(TMP_DIR_IMAGE):
        shutil.rmtree(TMP_DIR_IMAGE)

def process_generated(file, model_path):
    with open(file) as f:
        json_obj = json.loads(f.read())
        dict = EasyDict(json_obj)
        result, quant = dict.result, dict.quant
        # result = json_obj[0]
    print(np.shape(result))
    smpl = SMPL(model_path=model_path, gender='MALE', batch_size=1)
    np_dances_original = []
    dance_datas = []
    np_dances_rotmat = []

    # original loop data
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
    dance_datas.append(np_dance)

    nn, cc = np_dance.shape
    np_dance = np_dance.reshape((nn, cc//3, 3))
    roott = np_dance[:1, :1]  # the root
    np_dance = (np_dance - roott).reshape((nn, cc))
    
    root = np_dance[:, :3]
    np_dance[:, :3] = root
    np_dances_original.append(np_dance)
    return np_dance


def process_pregen(file):
    with open(file) as f:
        json_obj = json.loads(f.read())
        # result = json_obj['result']
        result = json_obj
        print(np.shape(result))
    np_dance = np.array(result)
    return np_dance


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pytorch implementation of Music2Dance"
    )
    parser.add_argument("--file", default='results.json')
    parser.add_argument("--name", default='untitled_video.json')
    parser.add_argument("--music", default='music.wav')
    parser.add_argument("--video_dir", default='./video')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pre", action='store_true') # generate video with simple processed smpl data
    group.add_argument("--post", action='store_true') # generate video with generated data from the model
    args = parser.parse_args()

    # temp vars
    model_path = "./SMPL_MALE.pkl"
    
    if args.pre:
        pregen = False
        result = process_pregen(args.file)
    elif args.post:
        pregen = True
        result = process_generated(args.file, model_path)

    visualizeAndWrite(result, args.video_dir, args.music, args.name)