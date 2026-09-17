from pathlib import Path

from stillib_paths import PathsBase, childpaths, pathfield


class Folder(PathsBase):
    @pathfield(kind="file")
    def env(self) -> Path:
        return self.base / "env.yml"


class MyPaths(PathsBase):
    @pathfield(kind="file")
    def config(self) -> Path:
        return self.base / "config.json"

    @childpaths
    def folder(self) -> Folder:
        return Folder(self.base / "folder")


def main() -> int:
    paths = MyPaths(
        "/home/andreasstillits/coding/tools/stillib_paths/src/stillib_paths/examples"
    )
    print(paths.base)
    print(type(paths.config))
    print(paths.config.path)
    print(paths.config.exists())
    #
    print(paths.folder.base)
    print(type(paths.folder.env))
    print(paths.folder.env.path)
    print(paths.folder.env.exists())
    print(paths.folder.env.ensure())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
