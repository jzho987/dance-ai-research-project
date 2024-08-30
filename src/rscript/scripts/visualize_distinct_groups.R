library(jsonlite)
library(ggplot2)
library(reshape2)  # Needed for the melt function

# Loading the data
data <- fromJSON("data/raw/empty_generated_0_shift_28.json")

# Unpacking the result part of the data
result <- as.data.frame(data$result)  # Assuming this is the correct part to visualize

# Adding a time variable (Index) if it doesn't exist
result$Index <- 1:nrow(result)

# Reshaping the data using the melt function from reshape2
result_long <- melt(result, id.vars = "Index", variable.name = "Variable", value.name = "Value")

# Adding a grouping variable
result_long$Group <- as.factor((as.numeric(as.factor(result_long$Variable)) - 1) %% 3 + 1)

# Plotting all variables in three groups
ggplot(result_long, aes(x = Index, y = Value)) +
  geom_line() +
  facet_wrap(~Group + Variable, scales = "free_y", ncol = 1) +  # Grouping and plotting each variable in a separate panel
  labs(title = "Line Plots of All Variables", x = "Index", y = "Value")
