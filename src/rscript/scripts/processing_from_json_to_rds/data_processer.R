# Processes all the data from 'data/raw' -> 'data/processed'
# Converts all the .json files into .rds dataframes

library(jsonlite)

process_data <- function(data, name){
  # Number of iterations (rows)
  n_iterations <- nrow(data)
  
  # Number of coordinates per iteration
  n_coords_per_iteration <- ncol(data) / 3
  
  # Initialize vectors to store data
  iteration <- rep(1:n_iterations, each = n_coords_per_iteration)
  coord_index <- rep(1:n_coords_per_iteration, times = n_iterations)
  x <- numeric()
  y <- numeric()
  z <- numeric()
  
  # Loop through the matrix and extract x, y, z values
  for (i in 1:n_iterations) {
    x <- c(x, data[i, seq(1, ncol(data), by = 3)])
    y <- c(y, data[i, seq(2, ncol(data), by = 3)])
    z <- c(z, data[i, seq(3, ncol(data), by = 3)])
  }
  
  # Combine into a data frame
  df <- data.frame(Iteration = iteration, Coord_Index = coord_index, X = x, Y = y, Z = z)
  
  # Add new columns for original dance and music
  df$original_dance <- sub("\\..*", "", name)
  df$music <- sub(".*-(m[A-Z]{2}[0-9]).*", "\\1", name)
  
  # Print the data frame
  print(df)
  saveRDS(df, file = paste("data/processed/", name, ".rds", sep=""))
}

# process everything in the 'data/raw' directory
files <- list.files("data/raw")
for (file in files){
  file_name <- sub("\\.[^.]*$", "", file) # removes extension
  file_path = file.path("data/raw", file)

  data <- fromJSON(file_path)
  process_data(data, file_name)
}

# processes one hardcoded file
# json_data <- fromJSON("data/raw/empty_generated_0_shift_28.json")
# data <- json_data[["result"]]
# process_data(data, "empty_generated_0_shift_28")
