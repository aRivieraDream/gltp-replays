import asyncio
import json
from pathlib import Path
from typing import Any, Dict

import aiofiles
import aiofiles.os

# a cache of one Lock per file path
_file_locks: Dict[Path, asyncio.Lock] = {}


def _lock_for(path: Path) -> asyncio.Lock:
    """
    Return a dedicated asyncio.Lock for this path.
    Creates one if it doesn't exist yet.
    """
    lock = _file_locks.get(path)
    if lock is None:
        lock = asyncio.Lock()
        _file_locks[path] = lock
    return lock


async def read_json(path: Path) -> Any:
    """
    Read JSON from `path` under a per-path lock.
    """
    lock = _lock_for(path)
    async with lock:
        async with aiofiles.open(path, "r") as f:
            data = await f.read()
    return json.loads(data)


async def write_json(path: Path, data: Any) -> None:
    """
    Atomically write JSON to `path` under the same per-path lock.
    """
    tmp = path.with_suffix(".tmp")
    lock = _lock_for(path)
    async with lock:
        async with aiofiles.open(tmp, "w") as f:
            await f.write(json.dumps(data, indent=2))
        await aiofiles.os.replace(tmp, path)
