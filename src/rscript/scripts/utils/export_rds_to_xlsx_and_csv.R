library(writexl)

filename <- "data/metrics/combined_metrics"
df_filename <- paste0(filename, ".rds")
xlsx_filename <- paste0(filename, ".xlsx")
csv_filename <- paste0(filename, ".csv")

df <- readRDS(df_filename)
write_xlsx(df, xlsx_filename)
write.csv(df, csv_filename, row.names=FALSE)
