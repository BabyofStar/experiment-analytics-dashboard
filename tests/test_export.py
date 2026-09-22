import pandas as pd

from src.export import dataframe_to_csv_bytes


def test_dataframe_to_csv_bytes_preserves_headers_and_unicode():
    dataframe = pd.DataFrame({"指标": ["平均 IPC"], "值": [2.1]})

    exported = dataframe_to_csv_bytes(dataframe)

    assert exported.startswith(b"\xef\xbb\xbf")
    decoded = exported.decode("utf-8-sig")
    assert "指标,值" in decoded
    assert "平均 IPC,2.1" in decoded
