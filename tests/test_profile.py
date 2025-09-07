import pandas as pd
from src.tools.profile import profile

def test_profile_basic():
    df = pd.DataFrame({
        "precio": [1, 2, 3, 4, 5],
        "cantidad": [10, 10, 10, 20, 30],
        "categoria": ["A","A","B","B","C"]
    })
    out = profile(df, columns=["precio","cantidad"])
    assert "stats" in out
    assert "precio" in out["stats"]
    assert out["stats"]["precio"]["mean"] == 3.0
