from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Tuple
import pandas as pd


class BaseStrategy(ABC):
    def name(self) -> str:
        return self.__class__.__name__


    @abstractmethod
    def evaluate_opening_bar(self, df5: pd.DataFrame) -> Tuple[bool, str]:
        """Return (should_signal, reason). Requires first 5m bar of today + prior history."""
        raise NotImplementedError