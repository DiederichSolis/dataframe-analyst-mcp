import pandas as pd
from src.tools.outliers import detect_outliers

def test_outliers_iqr():
    df = pd.DataFrame({"x":[1,2,3,4,5,1000]})
    out = detect_outliers(df, column="x", method="iqr", factor=1.5)
    assert out["count"] == 1
    assert out["outliers"][0]["value"] == 1000.0
