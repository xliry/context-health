from __future__ import annotations

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.sdist import sdist


class CleanSdist(sdist):
    def make_release_tree(self, base_dir, files):
        super().make_release_tree(base_dir, files)
        shutil.rmtree(Path(base_dir) / "context_health.egg-info", ignore_errors=True)


setup(cmdclass={"sdist": CleanSdist})
