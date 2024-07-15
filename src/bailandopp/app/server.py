from sanic import Sanic, HTTPResponse
from easydict import EasyDict
import json

from utils.extractor import FeatureExtractor
import numpy as np
import base64
import essentia
from essentia.standard import *
from smplx import SMPL
import os
import torch

from models.bailando import Bailando
import config.config as cf
import config.gpt_config as gpt_cf
import config.vqvae_config as vq_cf
from utils.format import format_rotmat_output
from sanic.worker.manager import WorkerManager

# global
WorkerManager.THRESHOLD = 600 # Value is in 0.1s
DEFAULT_SAMPLING_RATE = 15360*2
app = Sanic("ai_agent_server")

# boostrap
@app.before_server_start
async def boostrap(app, loop):
    print("Initializing Boostrap.")

    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"use device: {device}")

    app.ctx.agent = Bailando(vq_cf, gpt_cf, cf, device, "./weight/vqvae.pt", "./weight/gpt.pt")
    app.ctx.smpl = SMPL(model_path=cf.smpl_model_path, gender='MALE', batch_size=1)
    app.ctx.cache = {}
    app.ctx.prev = []

    print("Finished Boostrap.")


# routes
@app.post("/music")
async def send_music(request):
    print("received send music request")
    request = EasyDict(request.json)
    musicID = request.musicID
    payload = request.payload
    await handle_send_music(music_id=musicID, payload=payload)
    return HTTPResponse(status=200)


@app.post("/dance-sequence")
async def generate_dance_sequence(request):
    print("received generate dance sequence request")
    request = EasyDict(request.json)
    musicID = request.musicID
    startFrameIndex = request.startFrameIndex
    payload = request.payload
    length = request.length # how long of a clip to generate.
    shift = request.shift # amount of seed from previous motion clip to take.
    seed = request.seed # amount of user input to generate from, this will override user input from pos 0.

    result, quant = await handle_generate_dance_sequence(music_id=musicID, start_frame_index=startFrameIndex, payload=payload, length=length, shift=shift, seed=seed)
    result = result.squeeze(0).cpu().numpy().tolist()
    result = format_rotmat_output(result, app.ctx.smpl)
    print(np.shape(result))
    app.ctx.prev = result
    quant_up, quant_down = quant
    quant = [quant_up.tolist(), quant_down.tolist()]

    response = {
        'result': result,
        'quant': quant
    }
    response = json.dumps(response)
    return HTTPResponse(body=response, status=200)


# handlers
async def handle_send_music(music_id, payload):
    print("handling send music request")
    # load to disk
    data = base64.b64decode(payload)
    file_name = f'{music_id}.wav'
    with open(file_name, 'wb') as f:
        f.write(data)

    # load with essentia
    sampling_rate = DEFAULT_SAMPLING_RATE
    loader = essentia.standard.MonoLoader(filename=file_name, sampleRate=sampling_rate)
    audio = loader()
    audio_file = np.array(audio).T

    # process audio file
    extractor = FeatureExtractor()
    melspe_db = extractor.get_melspectrogram(audio_file, sampling_rate)
    mfcc = extractor.get_mfcc(melspe_db)
    mfcc_delta = extractor.get_mfcc_delta(mfcc)
    audio_harmonic, audio_percussive = extractor.get_hpss(audio_file)
    if sampling_rate == 15360 * 2:
        octave = 7
    else:
        octave = 5
    chroma_cqt = extractor.get_chroma_cqt(audio_harmonic, sampling_rate, octave=octave)
    onset_env = extractor.get_onset_strength(audio_percussive, sampling_rate)
    tempogram = extractor.get_tempogram(onset_env, sampling_rate)
    onset_beat = extractor.get_onset_beat(onset_env, sampling_rate)[0]
    onset_env = onset_env.reshape(1, -1)

    # save to cache
    feature = np.concatenate([
        mfcc, # 20
        mfcc_delta, # 20
        chroma_cqt, # 12
        onset_env, # 1
        onset_beat, # 1
        tempogram
    ], axis=0)
    feature = feature.transpose(1, 0)

    wav_padding = cf.wav_padding
    music_move = cf.move
    np_music = np.array(feature)

    # NOTE: transformation before store.
    # zero padding left
    for kk in range(wav_padding):
        np_music = np.append(np.zeros_like(np_music[-1:]), np_music, axis=0)
    # fully devisable
    for kk in range((len(np_music) // music_move + 1) * music_move - len(np_music) ):
        np_music = np.append(np_music, np_music[-1:], axis=0)
    # zero padding right
    for kk in range(wav_padding):
        np_music = np.append(np_music, np.zeros_like(np_music[-1:]), axis=0)
    feature = np_music

    key = f'{music_id}-processed'
    app.ctx.cache[key] = feature

    # post
    os.remove(file_name)


async def handle_generate_dance_sequence(music_id, start_frame_index, payload, length, shift, seed):
    print("handling generate dance sequence request")
    agent: Bailando = app.ctx.agent
    cache = app.ctx.cache
    music_input = torch.tensor(cache[f'{music_id}-processed']).unsqueeze(0)

    # transform
    np_dance = np.array(payload)
    print(np.shape(np_dance))
    if seed > 0 and app.ctx.prev != None and len(app.ctx.prev) >= seed:
        print(f"using seed motion; count: {seed}")
        input_seed = np.array(app.ctx.prev[:seed])
        np_dance = np.concatenate((input_seed, np_dance), axis=0)
    print(np.shape(np_dance))
    root = np_dance[:, :3]
    np_dance = np_dance - np.tile(root, (1, 24))
    np_dance[:, :3] = root
    for kk in range((len(np_dance) // 5 + 1) * 5 - len(np_dance) ):
        np_dance = np.append(np_dance, np_dance[-1:], axis=0)
    dance_input = torch.tensor(np_dance).unsqueeze(0)

    result, quants = agent.eval_raw(music_input, dance_input, cf.music_config, length, start_frame_index, shift)
    return result, quants
