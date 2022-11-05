def get_version():
    try:
        import importlib.metadata
        return importlib.metadata.version("pycrc")
    except:     # noqa: E722
        pass
    try:
        import re
        import os
        with open(os.path.join('..', '..', 'pyproject.toml'), 'r') as file:
            text = file.read()
        pattern = re.compile(r"""^version *= *["']([^'"]*)['"]""",  re.MULTILINE)
        m = re.search(pattern, text)
        if m:
            return m[1]
    except FileNotFoundError:
        pass
    return 'unknown'


__version__ = get_version()
__author__ = "Thomas Pircher"
