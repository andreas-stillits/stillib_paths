from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

type PathLike = str | Path
type Kind = Literal["dir", "file"]

# -------------------------------------------------------
# Definition of error types
# -------------------------------------------------------


class PathsError(Exception):
    """Base class for all path-related errors."""


class MissingPathError(PathsError):
    """Raised when a required path does not exist."""


class WrongPathKindError(PathsError):
    """Raised when a path exists but is of the wrong kind (file vs directory)."""


def ensure(path: PathLike, kind: Kind = "dir") -> Path:
    """
    Ensure that a path exists.

    Behavior:
        - If kind is "dir", create the directory and any necessary parent directories.
        - If kind is "file", create the parent directories and an empty file at the specified path.
    If the path already exists, do nothing.

    Args:
        path: The path to ensure.
        kind: The kind of the path (either "dir" or "file").

    Raise:
        - ValueError: If specified kind is not "dir" or "file".

    Return:
        - The pathlib.Path object corresponding to the specified path.
    """

    path = Path(path)
    if kind == "dir":
        path.mkdir(parents=True, exist_ok=True)
    elif kind == "file":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
    else:
        message: str = f"Invalid kind: {kind}. Choose 'dir' or 'file'."
        raise ValueError(message)
    return path


def require(path: PathLike, kind: Kind = "dir") -> Path:
    """
    Require that a path exists.

    Behavior:
        - If kind is "dir", check if the directory exists.
        - If kind is "file", check if the file exists.
    If the path does not exist, raise an exception.

    Args:
        path: The path to require.
        kind: The kind of the path (either "dir" or "file").
    Raises:
        MissingPathError: If the path does not exist.
        WrongPathKindError: If the path exists but is of the wrong kind.
    Return:
        The pathlib.Path object corresponding to the specified path.
    """
    path = Path(path)
    if not path.exists():
        raise MissingPathError(f"Path does not exist: {path}")
    if kind == "dir" and not path.is_dir():
        raise WrongPathKindError(f"Path is not a directory: {path}")
    if kind == "file" and not path.is_file():
        raise WrongPathKindError(f"Path is not a file: {path}")

    return path


# -------------------------------------------------------
# Basic object definitions
# -------------------------------------------------------


@dataclass(frozen=True)
class ManagedPath:
    """
    Basic data class. A ManagedPath holds a pathlib.Path object and a kind (either "dir" or "file").
    It provides methods to ensure or require the path, as well as mirroring some of the pathlib.Path methods for ease of use.
    """

    path: Path
    kind: Kind = "dir"

    # adopt ensure/require policies as methods
    def ensure(self) -> Path:
        return ensure(self.path, self.kind)

    def require(self) -> Path:
        return require(self.path, self.kind)

    # mirror pathlib.Path methods for ease of use
    def exists(self) -> bool:
        return self.path.exists()

    def is_file(self) -> bool:
        return self.path.is_file()

    def is_dir(self) -> bool:
        return self.path.is_dir()

    def joinpath(self, *other: PathLike) -> Path:
        return self.path.joinpath(*other)

    def with_suffix(self, suffix: str) -> Path:
        return self.path.with_suffix(suffix)

    def relative_to(self, other: PathLike) -> Path:
        return self.path.relative_to(other)

    # Adopt the / operation for joining paths
    def __truediv__(self, other: PathLike) -> Path:
        return self.path / other

    # Adopt under the hood conversion of Path to str in file system operations
    def __fspath__(self) -> str:
        return str(self.path)

    # Adopt the str representation of the path for easy printing
    def __str__(self) -> str:
        return str(self.path)


class PathsBase:
    def __init__(self, base: PathLike) -> None:
        self.base = Path(base)


@dataclass(frozen=True)
class ManagedPathField[T]:
    """
    A field is born with a factory function and a kind indication.
    The factory should return a Path object.
    """

    factory: Callable[[T], Path]
    kind: Kind = "dir"

    # define action for . notation on the field
    def __get__(self, obj: T, owner: type | None = None) -> ManagedPath:
        return ManagedPath(self.factory(obj), self.kind)


# decorator to create a ManagedPathField with a factory function and kind
def pathfield[T](
    *, kind: Kind = "dir"
) -> Callable[[Callable[[T], Path]], ManagedPathField[T]]:
    if kind not in ("dir", "file"):
        message: str = f"Invalid kind: {kind}. Choose 'dir' or 'file'."
        raise ValueError(message)

    def wrapper(factory: Callable[[T], Path]) -> ManagedPathField[T]:
        return ManagedPathField(factory, kind)

    return wrapper


@dataclass(frozen=True)
class ManagedChildPathsField[T, P]:
    factory: Callable[[T], P]

    def __get__(self, obj: T, owner: type | None = None) -> P:
        return self.factory(obj)


# decorator to create a ManagedChildPathsField with a factory function
def childpaths[T, P: PathsBase](func: Callable[[T], P]) -> ManagedChildPathsField[T, P]:
    return ManagedChildPathsField(func)
