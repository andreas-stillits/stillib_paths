from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from os import PathLike as OSPathLike
from pathlib import Path
from typing import Literal, overload

type PathLike = str | OSPathLike[str]
type Kind = Literal["dir", "file"]

# -------------------------------------------------------
# Definition of error types
# -------------------------------------------------------


class PathsError(Exception):
    """Base class for all managed-path-related errors."""


class MissingPathError(PathsError):
    """Raised when a required path does not exist."""


class WrongPathKindError(PathsError):
    """Raised when a path exists but is of the wrong kind (file vs directory)."""


# -------------------------------------------------------
# Definition of prepare/require behavior
# -------------------------------------------------------


def prepare(path: PathLike, kind: Kind = "dir", touch: bool = False) -> Path:
    """
    Prepare a path by ensuring that the necessary directories exist.

    Behavior:
        - If kind is "dir", create the directory and its parent directories.
        - If kind is "file", create the parent directories. By default, do not create the file itself unless touch is True.

    Args:
        path: The path to prepare.
        kind: The kind of the path (either "dir" or "file").
        touch: Whether to touch the file if it doesn't exist.
               WARNING: creating an empty file before computation risks a misleading state if the computation fails. Use with caution.
    Raises:
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
    if kind not in ("dir", "file"):
        raise ValueError(f"Invalid kind: {kind}. Choose 'dir' or 'file'.")
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


class AttriPathsBase:
    """
    Base class for file tree declaration.
    Defines the convention that the base path for a given instance is stored in the attribute `base`.
    This base path is used as the root for all managed paths declared in the class.
    """

    def __init__(self, base: PathLike) -> None:
        self.base = Path(base)


@dataclass(frozen=True, slots=True)
class AttriPath:
    """
    Basic data class that allows method-style access to a path and typical pathlib operations.
    It holds a pathlib.Path object and a kind indication (either "dir" or "file").
    The added value is that navigating the file tree and acting on it is all oneline attribute/method access syntax
    """

    path: Path
    kind: Kind

    # adopt the defined prepare/require behavior for ease of use
    def prepare(self, touch: bool = False) -> Path:
        """
        touch (bool) is a flag that indicates whether to create an empty file if the path is of kind "file" and does not exist.
        Default setting is not to touch.
        WARNING: creating an empty file before computation risks a misleading state if the computation fails. Use with caution.
        """
        return prepare(self.path, self.kind, touch=touch)

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
            raise TypeError("Cannot join a path onto a non-dir type path")
        return self.path / other

    # Allow passing the object to be directly understood as its path attribute as a string in file system operations
    def __fspath__(self) -> str:
        return str(self.path)

    # Adopt the str representation of the path for easy printing
    def __str__(self) -> str:
        return str(self.path)


# --------------------------
# Descriptor
# --------------------------


@dataclass(frozen=True)
class AttriPathDescriptor[T]:
    """
    Descriptor class for AttriPath. It allows the declaration of an AttriPath by decorating a generator function.
    The generator function must take an object and return a simple pathlib.Path
    """

    generator: Callable[[T], Path]
    kind: Kind

    # overloading __get__ method for accurate typing
    # by python convention, if the descriptor is accessed through the class and not an instance (obj = None), the descriptor itself is returned
    @overload
    def __get__(
        self, obj: None, owner: type[T] | None = None
    ) -> AttriPathDescriptor[T]: ...

    @overload
    def __get__(self, obj: T, owner: type[T] | None = None) -> AttriPath: ...

    # definition. Conform to convention that the descriptor itself is returned if accessed through the class and not an instance
    def __get__(
        self, obj: T | None, owner: type[T] | None = None
    ) -> AttriPathDescriptor[T] | AttriPath:
        # If class access:
        if obj is None:
            return self
        # If instance access:
        return AttriPath(self.generator(obj), self.kind)

    # preventing accidental shadowing. Declarations should be immutable
    # i.e. it should not be possible to later assign new attribute values to the descriptor.
    def __set__(self, obj: object, value: object) -> None:
        raise AttributeError("Path fields are read-only once declared")


# -------------------------
# Parameterized Decorator
# -------------------------


def attripath[T](
    kind: Kind,
) -> Callable[[Callable[[T], Path]], AttriPathDescriptor[T]]:
    """
    Decorator for file and directory paths.
    Define the derived path by decorating a function that returns a pathlib.Path object.
    Example:

        class MyPaths(AttriPathsBase):
            @attripath(kind="dir")
            def my_dir(self) -> Path:
                return self.base / "my_dir"

            @attripath(kind="file")
            def my_file(self) -> Path:
                return self.base / "my_file.txt"

    Args:
        kind: The kind of the path (either "dir" or "file").
    Raises:
        ValueError: If specified kind is not "dir" or "file".

    Note:
        Generators that return new AttriPathsBase subclasses should be decorated with a plain @property instead.

    """
    if kind not in ("file", "dir"):
        # Fail at runtime if an invalid field type is passed
        raise ValueError(
            f"Unknown attripath kind: {kind}. Choose from: 'file' or 'dir'"
        )
    return lambda generator: AttriPathDescriptor(generator, kind)
