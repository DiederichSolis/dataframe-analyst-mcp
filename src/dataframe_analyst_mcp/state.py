from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import pandas as pd

@dataclass
class SessionState:
    df: Optional[pd.DataFrame] = None
    source_meta: Dict[str, Any] = field(default_factory=dict)
    cache: Dict[str, Any] = field(default_factory=dict)

    def set_df(self, df: pd.DataFrame, source_meta: Dict[str, Any]) -> None:
        self.df = df
        self.source_meta = source_meta
        self.cache.clear()

    def require_df(self) -> pd.DataFrame:
        if self.df is None:
            raise RuntimeError("No dataset loaded. Call load_data first.")
        return self.df

STATE = SessionState()
