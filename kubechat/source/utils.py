import asyncio
import functools
import os
import tempfile


def gen_temporary_file(name, default_suffix=""):
    prefix, suffix = os.path.splitext(name)
    prefix = prefix.strip("/").replace("/", "--")
    suffix = suffix.lower()
    if not suffix:
        suffix = default_suffix
    return tempfile.NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix)


async def async_run(f, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(f, *args, **kwargs))
