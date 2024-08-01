import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import json
from matplotlib.animation import FuncAnimation

with open("results3.json") as f:
    keypoints_list = json.loads(f.read())
    keypoints_list = keypoints_list['result']

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
    """Update the animation."""
    keypoints = np.array(keypoints_list[frame]).reshape(-1, 3)
    x = keypoints[:, 0]
    y = keypoints[:, 1]
    z = keypoints[:, 2]

    # Update scatter plot
    sc._offsets3d = (x, y, z)
    
    # Update text annotations
    for text in texts:
        text.remove()
    texts.clear()
    for i, (x_coord, y_coord, z_coord) in enumerate(keypoints):
        text = ax.text(x_coord, y_coord, z_coord, '%d' % i, size=10, zorder=1, color='k')
        texts.append(text)
    
    return sc, line

# Create the animation
ani = FuncAnimation(fig, update, frames=len(keypoints_list), init_func=init, blit=False, interval=500)

# Show the plot
plt.show()