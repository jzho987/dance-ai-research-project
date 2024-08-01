import json
import argparse
import numpy as np


CONTEXT_LENGTH = 28

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=""
    )
    parser.add_argument("--end", default='./generated')
    parser.add_argument("--start", default='./pregen')
    parser.add_argument("--out", default='./seed')
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--start_seed", type=int, default=14)
    args = parser.parse_args()

    end_full = f"{args.end}_{args.index}.json"
    start_full = f"{args.start}_{args.index}.json"

    with open(end_full) as f:
        json_obj = json.loads(f.read())
        end_res = json_obj["result"]
    with open(start_full) as f:
        json_obj = json.loads(f.read())
        start_res = json_obj
    
    end_res = np.array(end_res)
    start_res = np.array(start_res)

    start_seed = args.start_seed * 8
    end_seed = (CONTEXT_LENGTH - args.start_seed)  * 8

    end_res = end_res[-end_seed:, :]
    start_res = start_res[:start_seed, :]

    new_res = np.concatenate([end_res, start_res])
    new_path = f"{args.out}_{args.index}.json"
    with open(new_path, "w") as f:
        f.write(json.dumps(new_res.tolist()))