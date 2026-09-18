# stillib_paths - a path management utility built on pathlib

## Installation 
```bash
# regular install
pip install .

# editable and development tools install
pip install -e .[dev]
```

## Why does this tool exist?
This tool aims to centralize file system structure in a single paths.py file.
The intend is to document and declare a file tree in one place rather than leaving magic strings and implicit conventions
scattered over a project. All path actions can then happen programmatically rather than through raw strings.
In collaboration settings, others can now interact with your file system structure in a more conceptual way, even when
actual path naming conventions are long and messy. By leaving the root as a parameter, one can easily interact with the filesystem in different locations across machines, servers, etc.

## Intended use 
Here are a few examples of how to use the tool:

### Simple static folder
We declare the project folder and its contents as a `PathsBase` object. Subpaths are defined by decorating generator functions according to their type: file, directory, child object. Suppose we want the file tree:

```
project/
    data/
        input.npy
        output.npy
    config.json
```

We then encode that structure in a paths.py file:

```python
from pathlib import Path
from stillib_paths import PathsBase, managed_path

class DataPaths(PathsBase):
    @managed_path("file")
    def input_file(self) -> Path:
        return self.base / "input.npy"

    @managed_path("file")
    def output_file(self) -> Path:
        return self.base / "output.npy"

class ProjectPaths(PathsBase):
    @managed_path("file")
    def config(self) -> Path:
        return self.base / "config.json"

    @managed_path("child")
    def data(self) -> DataPaths:
        return DataPaths(self.base / "data")

```
We can instanciate a `ProjectPaths` object and navigate the file system by accessing paths as attributes.
We could for instance print the config path and require that data/input.npy exists:

```python 
paths = ProjectPaths('path/to/project/root/')
print(paths.config)
input_path: Path = paths.data.input_file.require()
```

It is of course possible to define data/ as a dir_type property and input/output files from there, i.e.
```python 
class ProjectPaths(PathsBase):
    @managed_path("file")
    def config(self) -> Path:
        return self.base / "config.json"

    @managed_path("dir")
    def data(self) -> Path:
        return self.base / "data"

    @managed_path("file")
    def input_file(self) -> Path:
        return self.data.path / "input.npy"

    @managed_path("file")
    def output_file(self) -> Path:
        return self.data.path / "output.npy"

# the do directly:
input_file: Path = paths.input_file.ensure()    
```
But it quickly becomes much more transparent and versitile to define new `PathsBase` objects for subfolders.


### Parameterically derived folders
Suppose a project executes a lot of different runs that outputs a folder with the same conceptual content.
We can create a `RunPaths` object and parameterize it based on a `run_id`. Imagine the structure:

```
project/ 
    data/
        run_001/
            output.npy
        run_002/
            output.npy
        run_003/
           ...
    config.json
```

Then we simply define:    


```python 
from pathlib import Path
from stillib_paths import PathsBase, managed_path

class RunPaths(PathsBase):
    @managed_path("file")
    def output_file(self) -> Path:
        return self.base / "output.npy"

class ProjectPaths(PathsBase):
    @managed_path("file")
    def config(self) -> Path:
        return self.base / "config.json"

    @managed_path("dir")
    def data(self) -> Path:
        return self.base / "data"

    def run(self, run_id: str) -> RunPaths:
        # here we choose to enforce that the data/ folder exists once a RunPaths instance is created
        return RunPaths(self.data.ensure() / f"run_{run_id}")

# then access as:
paths = ProjectPaths("path/to/project/root/")
for run_id in ["001", "002", "003"]:
    run_paths = paths.run(run_id)
    run_paths.output_file.ensure(touch=True)
```

### Enheritance of repeated folder contents
Suppose we have a pipeline where several steps take in and input, computes and output and documentation.
If all steps should emit a config and a manifest, we can create a `StepPaths` base class such that individual
step definitions enherit those properties. Say we concretely have two steps: synthesis and simulation, and want:

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

```python
from pathlib import Path
from stillib_paths import PathsBase, managed_path


class StepPaths(PathsBase):
    @managed_path("file")
    def manifest(self) -> Path:
        return self.base / "manifest.json"
    
    @managed_path("file")
    def config(self) -> Path:
        return self.base / "config.json"
    
class SynthesisPaths(StepPaths):
    @managed_path("file")
    def output_file(self) -> Path:
        return self.base / "data.npy"
    

class SimulationPaths(StepPaths):
    @managed_path("file")
    def output_file(self) -> Path:
        return self.base / "results.csv"


class ProjectPaths(PathsBase):
    @managed_path("child")
    def synthesis(self) -> SynthesisPaths:
        return SynthesisPaths(self.base / "synthesis")

    @managed_path("child")
    def simulation(self) -> SimulationPaths:
        return SimulationPaths(self.base / "simulation")

# Then run synthesis and emit data.npy
# Have simulation require that the data exists and then produce results.csv
paths = ProjectPaths(Path("/path/to/project/root")) 
synthesize(paths.synthesis.output_file.path)
emit(paths.synthesis.config.path, paths.synthesis.manifest.path)
simulate(paths.synthesis.output_file.require())
```
Here `.require()` raises `MissingPathError` if the input does not exist and otherwise returns the Path.
