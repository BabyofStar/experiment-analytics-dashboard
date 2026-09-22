"""Export helpers for Streamlit download buttons."""

from __future__ import annotations

import pandas as pd


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    """Return UTF-8 CSV bytes compatible with spreadsheet applications."""

    return dataframe.to_csv(index=False).encode("utf-8-sig")
