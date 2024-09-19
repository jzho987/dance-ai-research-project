import subprocess
import argparse
import os
import polars as pl

def add_text_to_video(input_video, output_video, text):
    subprocess.run([
        'ffmpeg', '-i', input_video, '-vf', f"drawtext=text='{text}':x=(w-tw)/2:y=h-th-40:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=5",
        '-t', '20',  # Duration for the text overlay
        '-c:a', 'copy', output_video
    ], check=True)

def main(input_dir: str, clustering_file: str, output_file: str):
    df = pl.read_csv(clustering_file)
    df = df.select(
        pl.col("name"),
        pl.col("cluster"),
    )
    df = df.sort(by=["cluster"], descending=False)
    names = df["name"]
    clusters = df["cluster"]

    temp_files = []
    for name, cluster in zip(names, clusters):
        temp_file = f'.tmp_{name}.mp4'
        path = os.path.join(input_dir, f'{name}.mp4')
        if not os.path.exists(path):
            continue

        text = f'{name} - cluster {cluster}'

        add_text_to_video(path, temp_file, text)
        temp_files.append(temp_file)

    with open('filelist_with_text.txt', 'w') as file:
        for temp_file in temp_files:
            file.write(f"file '{temp_file}'\n")

    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'filelist_with_text.txt', '-c', 'copy', output_file
    ], check=True)

    os.remove('filelist_with_text.txt')
    for temp_file in temp_files:
        os.remove(temp_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", default='./input')
    parser.add_argument("--cluster_file", default='./clustering_output')
    parser.add_argument("--output_file", default='./output.mp4')
    args = parser.parse_args()
    main(args.input_dir, args.cluster_file, args.output_file)