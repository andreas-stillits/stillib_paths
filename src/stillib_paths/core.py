from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from os import PathLike as OSPathLike
from pathlib import Path
from typing import Any, Literal, overload

type PathLike = str | OSPathLike[str]
type FieldKind = Literal["dir", "file", "child"]
type PathKind = Literal["dir", "file"]

# -------------------------------------------------------
# Definition of error types
# -------------------------------------------------------


class PathsError(Exception):
    """Base class for all path-related errors."""


class MissingPathError(PathsError):
    """Raised when a required path does not exist."""


class WrongPathKindError(PathsError):
    """Raised when a path exists but is of the wrong kind (file vs directory)."""


# -------------------------------------------------------
# Definition of ensure/require behavior
# -------------------------------------------------------


def ensure(path: PathLike, kind: PathKind = "dir", touch: bool = False) -> Path:
    """
    Ensure that a path exists.

    Behavior:
        - If kind is "dir", create the directory and any necessary parent directories.
        - If kind is "file", create the parent directories. Touching the file is disabled by default

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
        if touch:
            path.touch(exist_ok=True)
    else:
        raise ValueError(f"Invalid kind: {kind}. Choose 'dir' or 'file'.")
    return path


def require(path: PathLike, kind: PathKind = "dir") -> Path:
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
    if kind not in ("dir", "file"):
        raise ValueError(f"Invalid kind: {kind}. Choose 'dir' or 'file'.")
    if kind == "dir" and not path.is_dir():
        raise WrongPathKindError(f"Path is not a directory: {path}")
    if kind == "file" and not path.is_file():
        raise WrongPathKindError(f"Path is not a file: {path}")

    return path


# -------------------------------------------------------
# Basic object definitions
# -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ManagedPath:
    """
    Basic data class. A ManagedPath holds a pathlib.Path object and a kind (either "dir" or "file").
    It provides methods to ensure or require the path, as well as mirroring some of the pathlib.Path methods for ease of use.
    """

    path: Path
    kind: PathKind

    # adopt ensure/require policies as methods
    def ensure(self, touch: bool = False) -> Path:
        return ensure(self.path, self.kind, touch=touch)

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
        if self.kind != "dir":
            raise TypeError("Cannot join a path onto a file-type path")
        return self.path / other

    # Allow passing the object to be understood as its path as a string in file system operations
    def __fspath__(self) -> str:
        return str(self.path)

    # Adopt the str representation of the path for easy printing
    def __str__(self) -> str:
        return str(self.path)


class PathsBase:
    """
    Base class for file tree declaration.
    Introduces the convention that path at any given level is enconded in the 'base' attribute.
    """

    def __init__(self, base: PathLike) -> None:
        self.base = Path(base)


# -------------------------
# Parameterized Decorator
# -------------------------


# Encode typing for 'file' and 'dir' behavior
@overload
def managed_path[T](
    kind: PathKind,
) -> Callable[[Callable[[T], Path]], ManagedPathField[T]]: ...


# Encode typing for 'child' behavior
@overload
def managed_path[T, P: PathsBase](
    kind: Literal["child"],
) -> Callable[[Callable[[T], P]], ManagedChildPathsField[T, P]]: ...


# Actual decorator definition
def managed_path(kind: FieldKind) -> Callable[[Callable[..., Any]], Any]:
    if kind == "child":
        return lambda factory: ManagedChildPathsField(factory)

    if kind in ("file", "dir"):
        return lambda factory: ManagedPathField(factory, kind)

    # Fail at runtime if an invalid field type is passed
    raise ValueError(
        f"Unknown managed path kind: {kind}. Choose from: 'file', 'dir', 'child'"
    )


# --------------------------
# Descriptors
# --------------------------


@dataclass(frozen=True)
class ManagedPathField[T]:
    """
    A field is born with a factory function and a kind indication.
    The factory should return a pathlib.Path object.
    """

    factory: Callable[[T], Path]
    kind: PathKind

    # overloading __get__ method for accurate typing
    @overload
    def __get__(self, obj: None, owner: type[T] | None = None) -> ManagedPathField: ...

    @overload
    def __get__(self, obj: T, owner: type[T] | None = None) -> ManagedPath: ...

    # definition. Conform to convention that the descriptor itself is returned if accessed through the class and not an instance
    def __get__(
        self, obj: T | None, owner: type[T] | None = None
    ) -> ManagedPathField | ManagedPath:
        # If class access:
        if obj is None:
            return self
        # If instance access:
        return ManagedPath(self.factory(obj), self.kind)

    # preventing accidental shadowing. Declarations should be immutable
    def __set__(self, obj: object, value: object) -> None:
        raise AttributeError("ManagedPath fields are read-only once declared")


@dataclass(frozen=True)
class ManagedChildPathsField[T, P]:
    factory: Callable[[T], P]

    # overloading __get__ method for accurate typing
    @overload
    def __get__(
        self, obj: None, owner: type[T] | None = None
    ) -> ManagedChildPathsField: ...

    @overload
    def __get__(self, obj: T, owner: type[T] | None = None) -> P: ...

    # definition. Conform to convention that the descriptor itself is returned if accessed through the class and not an instance
    def __get__(
        self, obj: T | None, owner: type[T] | None = None
    ) -> ManagedChildPathsField | P:
        # If class access:
        if obj is None:
            return self
        # If instance access:
        return self.factory(obj)

    # preventing accidental shadowing. Declarations should be immutable
    def __set__(self, obj: object, value: object) -> None:
        raise AttributeError("ManagedPath fields are read-only once declared")
