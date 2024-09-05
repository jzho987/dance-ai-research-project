# Load the necessary libraries
library(dplyr)
library(plotly)
library(reshape2)

# Load the .rds file (make sure the path is correct)
df <- readRDS("data/processed/empty_generated_0_shift_28.rds")

# Filter data for one Coord_Index (e.g., Coord_Index == 1)
df <- df %>%
  filter(Coord_Index == 1)

# Calculate velocity components (X, Y, Z) if not already in the data
df <- df %>%
  group_by(Coord_Index) %>%
  arrange(Iteration) %>%
  mutate(
    velocity_X = X - lag(X),
    velocity_Y = Y - lag(Y),
    velocity_Z = Z - lag(Z),
    velocity_magnitude = sqrt(velocity_X^2 + velocity_Y^2 + velocity_Z^2)
  ) %>%
  filter(!is.na(velocity_X))  # Remove NA values caused by lag()

# Calculate acceleration components (X, Y, Z)
df <- df %>%
  mutate(
    acceleration_X = velocity_X - lag(velocity_X),
    acceleration_Y = velocity_Y - lag(velocity_Y),
    acceleration_Z = velocity_Z - lag(velocity_Z),
    acceleration_magnitude = sqrt(acceleration_X^2 + acceleration_Y^2 + acceleration_Z^2)
  ) %>%
  filter(!is.na(acceleration_X))  # Remove NA values caused by lag()

#### Section 1: 3D Scatter Plots with Trajectories ####

# 3D scatter plot with trajectory
plot_ly(df, x = ~X, y = ~Y, z = ~Z, type = "scatter3d", mode = "lines+markers",
        line = list(color = ~velocity_magnitude, colorscale = "Viridis"),
        marker = list(size = ~acceleration_magnitude)) %>%
  layout(scene = list(xaxis = list(title = 'X Axis'),
                      yaxis = list(title = 'Y Axis'),
                      zaxis = list(title = 'Z Axis')))


#### Section 2: Quiver/Vector Plots using Plotly ####

# Vector plot for velocity using plotly (replacing quiver3D)
plot_ly() %>%
  add_trace(
    type = "scatter3d", mode = "lines",
    x = df$X, y = df$Y, z = df$Z,
    u = df$velocity_X, v = df$velocity_Y, w = df$velocity_Z,
    line = list(color = df$velocity_magnitude, colorscale = "Viridis", width = 2),
    marker = list(size = 3)
  ) %>%
  layout(
    scene = list(
      xaxis = list(title = "X Axis"),
      yaxis = list(title = "Y Axis"),
      zaxis = list(title = "Z Axis")
    )
  )


#### Section 3: 2D Projections with Color Coding ####

# 2D projection (XY) with color representing velocity magnitude
ggplot(df, aes(x = X, y = Y, color = velocity_magnitude)) +
  geom_point() +
  scale_color_viridis_c() +
  labs(title = "2D XY Projection of Velocity Magnitude", x = "X", y = "Y") +
  theme_minimal()


#### Section 4: Animated Plots ####

# Animated plot showing changes in velocity magnitude over iterations
ggplot(df, aes(x = X, y = Y, color = velocity_magnitude)) +
  geom_point() +
  transition_time(Iteration) +
  labs(title = 'Iteration: {frame_time}', x = "X", y = "Y", color = "Velocity Magnitude")


#### Section 5: Heatmaps for Magnitude ####

# Heatmap of velocity magnitude over iterations and Coord_Index
ggplot(df, aes(x = Iteration, y = Coord_Index, fill = velocity_magnitude)) +
  geom_tile() +
  scale_fill_viridis_c() +
  labs(title = "Velocity Magnitude Heatmap", x = "Iteration", y = "Coord_Index") +
  theme_minimal()


#### Section 6: Histograms and Density Plots ####

# Histogram of velocity magnitude
ggplot(df, aes(x = velocity_magnitude)) +
  geom_histogram(bins = 30, fill = "blue", alpha = 0.7) +
  labs(title = "Velocity Magnitude Distribution", x = "Velocity Magnitude", y = "Count")


#### Section 7: Parallel Coordinate Plots ####

# Parallel coordinate plot for velocity and acceleration across X, Y, Z axes (assuming reshape2 is installed)

df_long <- melt(df, id.vars = c("Coord_Index", "Iteration"), measure.vars = c("velocity_X", "velocity_Y", "velocity_Z"))
ggplot(df_long, aes(x = variable, y = value, group = interaction(Iteration, Coord_Index), color = factor(Coord_Index))) +
  geom_line(alpha = 0.5) +
  labs(title = "Parallel Coordinate Plot for Velocity Components", x = "Axis", y = "Velocity")


#### Section 8: Polar/Compass Plots for Directions ####

# Polar plot for the direction of velocity in the XY plane
ggplot(df, aes(x = atan2(velocity_Y, velocity_X))) +
  geom_histogram(bins = 30, fill = "green", alpha = 0.7) +
  coord_polar() +
  labs(title = "Direction of Movement (XY Plane)", x = "Angle (radians)", y = "Frequency")
