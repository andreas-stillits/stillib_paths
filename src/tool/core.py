from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, overload

type PathLike = str | Path
type Kind = Literal["dir", "file"]
