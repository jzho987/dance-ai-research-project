import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import json
from smplx import SMPLH
from matplotlib.animation import FuncAnimation
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("file", type=str)
args = parser.parse_args()

with open(args.file) as f:
    keypoints_list = json.loads(f.read())
    print(np.shape(keypoints_list))
    # keypoints_list = np.load(f)

# smplh = SMPLH(model_path="./model.npz", batch_size=1)
# keypoints_list = smplh.forward(
#     global_orient=smpl_poses[:, 0:1],
#     body_pose=smpl_poses[:, 1:],
# ).joints.detach().numpy()

# Create a new figure for plotting
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Set labels for axes
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')

# Set the title
ax.set_title('3D Keypoints Animation')

# Initialize the scatter plot
sc = ax.scatter([], [], [], c='r', marker='o')

# Initialize the line plot
line, = ax.plot([], [], [], label='Keypoint Path')

# Initialize the text annotations
texts = []

def init():
    """Initialize the animation."""
    sc._offsets3d = ([], [], [])
    line.set_data([], [])
    line.set_3d_properties([])
    for text in texts:
        text.remove()
    texts.clear()
    return sc, line

def update(frame):
    print(frame)
    """Update the animation."""
    keypoints = np.array(keypoints_list[frame]).reshape(-1, 3)
    keypoints[:, 2] *= -1
    x = keypoints[:, 0]
    y = keypoints[:, 2]
    z = keypoints[:, 1]

    # Update scatter plot
    sc._offsets3d = (x, y, z)
    
    # Update text annotations
    for text in texts:
        text.remove()
    texts.clear()
    for i, (x_coord, y_coord, z_coord) in enumerate(keypoints):
        text = ax.text(x_coord, z_coord, y_coord, '%d' % i, size=10, zorder=1, color='k')
        texts.append(text)
    
    return sc, line

# Create the animation
anim = FuncAnimation(fig, update, frames=len(keypoints_list), init_func=init, blit=False, interval=30)
print("showing")
plt.show()
