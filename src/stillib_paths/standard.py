from pathlib import Path

from .core import AttriPathsBase, attripath

"""
Small class definitions for standardized data I/O interaction paths.

1. A basic blueprint for I/O folders in a project

project/
├── config.json
├── data/
│   ├── sources/
│   └── derivatives/
└── figures/
    ├── dev/
    └── pub/

2. A basic blueprint for provenance files in relation to derived outputs

output/
├── provenance/
│   ├── config.json
│   └── manifest.json
└── ...

"""


class StandardProvenancePaths(AttriPathsBase):
    @attripath("dir")
    def provenance(self) -> Path:
        """Path to the provenance folder."""
        return self.base / "provenance"

    @attripath("file")
    def config(self) -> Path:
        """Path to the provenance config file."""
        return self.provenance / "config.json"

    @attripath("file")
    def manifest(self) -> Path:
        """Path to the provenance manifest file."""
        return self.provenance / "manifest.json"


class StandardFiguresPaths(AttriPathsBase):
    @attripath("dir")
    def dev(self) -> Path:
        """Path to the development figures folder."""
        return self.base / "dev"

    @attripath("dir")
    def pub(self) -> Path:
        """Path to the publication figures folder."""
        return self.base / "pub"


class StandardDataPaths(AttriPathsBase):
    @attripath("dir")
    def sources(self) -> Path:
        """Path to the sources data folder."""
        return self.base / "sources"

    @attripath("dir")
    def derivatives(self) -> Path:
        """Path to the derivatives data folder."""
        return self.base / "derivatives"


class StandardProjectPaths(AttriPathsBase):
    """Standard paths for a typical project."""

    @attripath("file")
    def config(self) -> Path:
        """Path to the global config file."""
        return self.base / "config.json"

    @property
    def figures(self) -> StandardFiguresPaths:
        """Path to the figures folder."""
        return StandardFiguresPaths(self.base / "figures")

    @property
    def data(self) -> StandardDataPaths:
        """Path to the data folder."""
        return StandardDataPaths(self.base / "data")

    def initialize(self) -> None:
        """Initialize the standard project structure."""
        self.figures.dev.path.mkdir(parents=True, exist_ok=True)
        self.figures.pub.path.mkdir(parents=True, exist_ok=True)
        self.data.sources.path.mkdir(parents=True, exist_ok=True)
        self.data.derivatives.path.mkdir(parents=True, exist_ok=True)
        self.config.path.touch(exist_ok=True)
