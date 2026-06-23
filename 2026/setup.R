# BIOS 667 (2026) materials: one-shot dependency installer.
# Run once before rendering any lecture/homework/quiz:  Rscript 2026/setup.R
# Installs every package the materials use that is not already present.
# Target: R 4.5.1, Quarto >= 1.5.

pkgs <- c(
  "broom", "broom.mixed", "clubSandwich", "dplyr", "emmeans", "geepack",
  "ggplot2", "glmmTMB", "kableExtra", "knitr", "lme4", "lmerTest", "lmtest",
  "MASS", "mice", "multgee", "nlme", "nnet", "patchwork", "pbkrtest", "plm",
  "pROC", "pscl", "purrr", "reshape2", "ResourceSelection", "RLRsim",
  "rmarkdown", "sandwich", "scales", "strucchange", "survival", "tibble", "tidyr"
)

missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]

if (length(missing) == 0) {
  message("All ", length(pkgs), " required packages are already installed.")
} else {
  message("Installing ", length(missing), " missing package(s): ",
          paste(missing, collapse = ", "))
  install.packages(missing, repos = "https://cloud.r-project.org")
  still <- missing[!vapply(missing, requireNamespace, logical(1), quietly = TRUE)]
  if (length(still) > 0) {
    stop("Failed to install: ", paste(still, collapse = ", "),
         "\nInstall these manually, then re-run.")
  }
  message("Done. All required packages are now installed.")
}
