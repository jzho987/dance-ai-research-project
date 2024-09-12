import os
import generate_features
import polars as pl

input_dir = "./output_clips"
fnames = os.listdir(input_dir)
df = pl.DataFrame()
for fname in fnames:
    input_file = os.path.join(input_dir, fname)
    ext = fname.split(".")[-1]
    is_json = ext == "json"
    out_df = generate_features.main(input_file, is_json)
    df = df.vstack(out_df)


from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
df = df.select(
    pl.exclude("name")
)
df = pl.DataFrame(scaler.fit_transform(df))
data = df.to_numpy()
print(df)

from sklearn.cluster import KMeans

print(data.shape)
kmeans = KMeans(n_clusters=7)
kmeans.fit(data)
clusters = kmeans.predict(data)
print(clusters)

cluster_dict = {"cluster": clusters}
cluster_df = pl.from_dict(cluster_dict)

df = df.hstack(cluster_df)
print(df)

from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D

data = df.with_columns(
    pl.exclude("cluster")
    ).to_numpy()

clusters = df["cluster"]

# Initialize Isomap and fit the model
n_components = 3
pca = PCA(n_components=n_components)
X_pca = pca.fit_transform(data)

# Plot the results
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection="3d")
ax.scatter(X_pca[:, 0], X_pca[:, 1], X_pca[:, 2], c=clusters, cmap=plt.cm.rainbow)
plt.title("PCA Visualization")
plt.show()