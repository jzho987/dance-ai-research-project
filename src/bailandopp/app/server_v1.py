from sanic import Sanic, HTTPResponse
from easydict import EasyDict
import json

from utils.extractor import FeatureExtractor
import numpy as np
from essentia.standard import *
from smplx import SMPL
import os
import torch

from models_v1.bailando_v1 import BailandoV1
import config.config as cf
import config.gpt_config_lb as gpt_cf
import config.vqvae_config_lb as vq_cf
from utils.format import format_output
from sanic.worker.manager import WorkerManager

# global
WorkerManager.THRESHOLD = 600 # Value is in 0.1s
DEFAULT_SAMPLING_RATE = 15360*2
DEFAULT_MUSIC_PATH = "../test_client/data/music/jazz_ballet.wav"
DEFAULT_MUSIC_ID = "jazz_ballet"
DEFAULT_SAVE_DIR = "./data"
app = Sanic("ai_agent_server")

# boostrap
@app.before_server_start
async def boostrap(app, loop):
    print("[BOOSTRAP] Initializing..")
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"use device: {device}")
    print(f"[BOOTSTRAP] Initializing AI Agent Model")
    app.ctx.agent = BailandoV1(vq_cf, gpt_cf, cf, device, "./weight/vqvae_lb.pt", "./weight/gpt_lb_l_240.pt")
    print(f"[BOOTSTRAP] Initializing SMPL Model")
    app.ctx.smpl = SMPL(model_path=cf.smpl_model_path, gender='MALE', batch_size=1).to(torch.device(device))
    app.ctx.prev = []
    app.ctx.index = 0
    print("[BOOSTRAP] Complete")


@app.post("/dance-sequence")
async def generate_dance_sequence(request):
    print("received generate dance sequence request")
    request = EasyDict(request.json)
    startFrameIndex = request.startFrameIndex
    payload = request.payload
    length = request.length # how long of a clip to generate.
    shift = request.shift # amount of seed from previous motion clip to take.
    seed = request.seed # amount of user input to generate from, this will override user input from pos 0.

    # save payload for analysis
    file = f"dance_{app.ctx.index}"
    path = os.path.join(DEFAULT_SAVE_DIR, file)
    with open(path, "w") as f:
        f.write(json.dumps(payload))

    result, quant = await handle_generate_dance_sequence(start_frame_index=startFrameIndex, payload=payload, length=length, shift=shift, seed=seed)
    result = result.squeeze(0).cpu().numpy().tolist()
    result = format_output(result)
    print(np.shape(result))
    app.ctx.prev = result
    quant_up, quant_down = quant
    quant = [quant_up.tolist(), quant_down.tolist()]

    response = {
        'result': result,
        'quant': quant
    }
    response = json.dumps(response)
    print("completed generate dance sequence request")
    return HTTPResponse(body=response, status=200)


async def handle_generate_dance_sequence(start_frame_index, payload, length, shift, seed):
    print("handling generate dance sequence request")
    agent: BailandoV1 = app.ctx.agent

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

    result, quants = agent.eval_raw(dance_input, length, start_frame_index, shift)
    return result, quants
