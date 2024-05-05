from sanic import Sanic, HTTPResponse
from easydict import EasyDict
import json

from utils.extractor import FeatureExtractor
import numpy as np
import base64
import essentia
from essentia.standard import *
import os
import torch

from models.bailando import Bailando
import config.config as cf
import config.gpt_config as gpt_cf
import config.vqvae_config as vq_cf

# global
DEFAULT_SAMPLING_RATE = 15360*2/8
app = Sanic("ai_agent_server")

# boostrap
@app.before_server_start
async def boostrap(app, loop):
    print(">init boostrap")
    device = "gpu" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"use device: {device}")
    app.ctx.agent = Bailando(vq_cf, gpt_cf, cf, device)
    app.ctx.cache = {"hello": "world"}
    print(">finished boostrap")

# routes
@app.post("/music")
async def send_music(request):
    print("received send music request")
    request = EasyDict(request.json)
    musicID = request.musicID
    payload = request.payload
    await handle_send_music(music_id=musicID, payload=payload)
    return HTTPResponse(status=200)

@app.websocket("/socket")
async def handler(request, ws):
    while True:
        message = await ws.recv()
        print(message)
        await ws.send(message)

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
    key = f'{music_id}-processed'
    app.ctx.cache[key] = feature

    # post
    os.remove(file_name)
