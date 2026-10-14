"""
Make a synthetic QC data set (no real or company data).

Imagine daily check-standard results for one element on an ICP-MS:
target 10.0 ppb, normal scatter about 0.2 ppb. Three problems are planted
so the checker has something to find:
  - samples 31-40: a sustained upward shift (e.g. a new standard lot)
  - samples 46-51: a steady upward drift (e.g. cone or tube wear)
  - sample 58:      one gross outlier (e.g. a contaminated vial)
"""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
TARGET, SD = 10.0, 0.2

x = rng.normal(TARGET, SD, 65)
x[30:40] = rng.normal(TARGET + 1.3 * SD, 0.5 * SD, 10)                 # shift
x[45:51] = TARGET + SD * np.array([-0.4, 0.1, 0.6, 1.1, 1.6, 2.1])       # drift
x[57] = TARGET + 3.6 * SD                                                 # outlier

Path("data").mkdir(exist_ok=True)
pd.DataFrame({"sample": np.arange(1, 66), "value": x.round(3)}).to_csv(
    "data/sample_qc.csv", index=False)
print("wrote data/sample_qc.csv")
