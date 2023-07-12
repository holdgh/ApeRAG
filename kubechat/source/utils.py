import os
import tempfile


def gen_temporary_file(name):
    prefix, suffix = os.path.splitext(name)
    prefix = prefix.strip("/").replace("/", "--")
    suffix = suffix.lower()
    return tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix)
