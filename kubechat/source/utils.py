import os
import tempfile


def gen_temporary_file(name, default_suffix=""):
    prefix, suffix = os.path.splitext(name)
    prefix = prefix.strip("/").replace("/", "--")
    suffix = suffix.lower()
    if not suffix:
        suffix = default_suffix
    return tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix)
