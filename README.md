# stillib_paths - a path management utility built on pathlib

Centralization of project path derivations with ergonomic attribute/method style syntax.

## Why this exists
The utility makes it easier to transparently declare, maintain, and share path conventions used for project I/O. Specifically it:
- Requires the user to systematically declare how project paths are derived relative to an arbitrary file system root, preferably in a centralized paths.py file. 
- Eliminates magic strings from floating around the code base. Paths are always accessed programmatically through the single paths.py source. Adjust the definition at the source, and the change is globally adopted.
- Allows path derivation, navigation, and operations to exhibit an intuitive attribute/method style syntax.


## Installation 
From stillib_paths project root, run:

```bash
# regular install
pip install .

# editable and development tools install
pip install -e .[dev]
```

## Minimal example
Suppose we want to encode a project data folder which has the following structure:
```
project/ 
    data/
        run_00/
            output.npy
            config.json
            manifest.json
        run_01/
            ...
    config.json
```

Where each run_XX folder has the same conceptual structure but is distinct by its run ID.
Declare the structure as an AttriPathsBase class and use the @property or @attripath decorators for attribute/method style syntax:

```python
from stillib_paths import AttriPathsBase, attripath
from pathlib import Path

class RunPaths(AttriPathsBase):
    @attripath("file")
    def output_file(self,) -> Path:
        return self.base / "output.npy"

    @attripath("file")
    def manifest(self,) -> Path:
        return self.base / "manifest.json"

    @attripath("file")
    def config(self,) -> Path:
        return self.base / "config.json"


class ProjectPaths(AttriPathsBase):
    @attripath("file")
    def config(self,) -> Path:
        return self.base / "config.json" 

    @attripath("dir")
    def data(self,) -> Path:
        return self.base / "data"

    def run(self, runID: str) -> RunPaths:
        return RunPaths(self.data.prepare() / f"run_{runID}")    
        # The .prepare() call ensures that project/data/ exists if ever a RunPaths instance is invoked
        # Here it does not create the run_XX directory until a .prepare() is called from the RunPaths instance.
```

Then define the root of the project and navigate the structure programmatically, e.g. in a computation context:

```python
from project.paths import ProjectPaths
from pathlib import Path

def compute_something(config) -> something:
    paths = ProjectPaths(config.project_root_path)
    # Say we need the output of run_00 as an input. Get the path and raise if it doesn't exist:
    input_path: Path = paths.run("00").output_file.require()

    # some computation ...

    # Say we want to store a result as the output of run_01 and also emit the used config and a manifest:
    output_paths = paths.run("01")
    save_result(output_paths.output_file.prepare())
    emit_config(output_paths.config.path) # directory is prepared already. We can get the raw pathlib.Path using the .path attribute
    emit_manifest(output_paths.manifest.path)
    return something
```

If we later decide to rename, "data/" or swap to a "config.toml" instead, `compute_something()` doesn't have to change. Only the declaration. Additionally, a collaborator that received the "data/" folder can easily derive the path to the output file of the run with "runID" using the conceptual string: `paths.run(runID).output_file.require()` without worrying about your specific naming conventions, i.e. where names may include time stamps or opaque references to your lab or setup.

## Core Concepts and Abstractions

### AttriPathsBase

This class introduces the convention that a declaration instance stores its base path in the `self.base` attribute as a pathlib.Path object.
It adds consistency and avoids having to expose string to pathlib.Path conversion.

### AttriPath

The core class which stores path (pathlib.Path) and kind (Literal["dir", "file"]) objects, and adds pathlib.Path operations on the .path attribute as native methods. It further defines the behavior of .prepare() and .require() based on the kind. By default, prepare creates the parent directories but does not touch the filename.

### Use 
By defining the system of paths as decorated methods of classes, the user achieves the one-line attribute access syntax and can exploit parameterized path generation or inheritance between similar sub-directories. Methods that define file or folder names should be decorated using `@attripath("file"/"dir")` and methods that return new AttriPathsBase sub-classes using a regular `@property`. If the derivation is parameterized, e.g. depends on a "runID", just define a regular method without decoration.

## Main API
```python
# define classes in paths.py
from stillib_paths import AttriPathsBase, attripath
from pathlib import Path
# definition ...
class ProjectPaths(AttriPathsBase): ...
# -----------------------------------------------------

# use definitions in project functionality
from project.paths import ProjectPaths
paths = ProjectPaths("/path/to/project/or/data/root/")
```

## More Examples

### Inheritance
Suppose we have a pipeline where several steps take an input, compute and output, and emit documentation.
If all steps should emit a config and a manifest, we can create a `StepPaths` base-class such that individual
step definitions inherit those properties rather than re-typing them. Say we concretely have two steps: synthesis and simulation, and want:

```
project/
    synthesis/
        data.npy
        config.json
        manifest.json
    simulation/
        results.csv
        config.json
        manifest.json
```
Then the documentation files `config.json` and `manifest.json` are repeated. We encode that using inheritance

```python
from pathlib import Path
from stillib_paths import AttriPathsBase, attripath


class StepPaths(AttriPathsBase):
    @attripath("file")
    def manifest(self) -> Path:
        return self.base / "manifest.json"
    
    @attripath("file")
    def config(self) -> Path:
        return self.base / "config.json"
    
class SynthesisPaths(StepPaths):
    @attripath("file")
    def output_file(self) -> Path:
        return self.base / "data.npy"
    

class SimulationPaths(StepPaths):
    @attripath("file")
    def output_file(self) -> Path:
        return self.base / "results.csv"


class ProjectPaths(AttriPathsBase):
    @property
    def synthesis(self) -> SynthesisPaths:
        return SynthesisPaths(self.base / "synthesis")

    @property
    def simulation(self) -> SimulationPaths:
        return SimulationPaths(self.base / "simulation")
```
We can now access both `paths.synthesis.manifest` and `paths.simulation.manifest` as they both inherit from `StepPaths`.
