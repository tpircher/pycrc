"""Build hook that generates the documentation before the sdist is created.

The generated pages are not checked in; they are built from the DocBook
sources in ``doc`` and added to the source distribution as build
artifacts.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

#: Files produced by ``make -C doc``. ``docbook.css`` is generated as a
#: side effect of the HTML transformation and is referenced by pycrc.html.
DOC_ARTIFACTS = (
    "doc/pycrc.html",
    "doc/pycrc.1",
    "doc/docbook.css",
)


class DocsBuildHook(BuildHookInterface):
    """Build the HTML and manual-page documentation for source distributions."""

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if self.target_name != "sdist":
            return

        missing = [tool for tool in ("make", "xsltproc") if shutil.which(tool) is None]
        if missing:
            tools = ", ".join(missing)
            raise RuntimeError(
                f"Building the pycrc documentation requires {tools}. "
                "On Debian/Ubuntu install them with: "
                "apt-get install make xsltproc docbook-xsl-ns docbook5-xml"
            )

        doc_dir = Path(self.root) / "doc"
        subprocess.run(["make", "-C", str(doc_dir), "clean", "all"], check=True)

        missing_artifacts = [path for path in DOC_ARTIFACTS if not (Path(self.root) / path).is_file()]
        if missing_artifacts:
            raise RuntimeError(f"Documentation build did not produce: {', '.join(missing_artifacts)}")

        build_data.setdefault("artifacts", []).extend(DOC_ARTIFACTS)
