import os
import yaml
import imageio
import argparse
import numpy as np

from tqdm import tqdm
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

from utils.renderer import get_renderer

import torch

def render_video(motion, smpl, save_path, audio_path):
    width = 1024
    height = 1024

    background = np.zeros((height, width, 3))
    renderer = get_renderer(width, height)

    for idx, motion_ in enumerate(motion):
        save_name = os.path.join(save_path, f'z{idx}.mp4')
        writer = imageio.get_writer(save_name, fps=60)

        pose, trans = motion_[:, :-3].view(-1, 24, 3), motion_[:, -3:]
        meshes = smpl.forward(
            global_orient=pose[:, 0:1],
            body_pose=pose[:, 1:],
            transl=trans
        ).vertices.cpu().numpy()
        faces = smpl.faces

        meshes = meshes - meshes[0].mean(axis=0)
        cam = (0.55, 0.55, 0, 0.10)
        color = (0.2, 0.6, 1.0)

        imgs = []
        for ii, mesh in enumerate(tqdm(meshes, desc=f"Visualize dance - z{idx}")):
            img = renderer.render(background, mesh, faces, cam, color=color)
            imgs.append(img)

        imgs = np.array(imgs)
        for cimg in imgs:
            writer.append_data(cimg)
        writer.close()

        video_with_music(save_name, audio_path)


def video_with_music(save_video, audio_path):
    videoclip = VideoFileClip(save_video)
    audioclip = AudioFileClip(audio_path)

    if os.path.isfile(save_video):
        os.remove(save_video)

    new_audioclip = CompositeAudioClip([audioclip])
    new_audioclip = new_audioclip.cutout(videoclip.duration, audioclip.duration)

    videoclip.audio = new_audioclip
    videoclip.write_videofile(save_video, logger=None)
