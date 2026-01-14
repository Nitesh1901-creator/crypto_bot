"""CSV persistence with atomic writes and simple file locks."""

from __future__ import annotations

import csv
import os
import pathlib
import tempfile
from contextlib import contextmanager
from typing import Dict, Iterable, List


@contextmanager
def _file_lock(lock_path: pathlib.Path):
    """
    A minimal cross-platform lock using an adjacent lock file.
    Not robust for high concurrency but sufficient for single-process bot writes.
    """
    lock_file = lock_path.with_suffix(lock_path.suffix + ".lock")
    fh = None
    try:
        fh = lock_file.open("w")
        # No advisory lock cross-platform; rely on atomic create and single-process discipline.
        yield
    finally:
        if fh:
            fh.close()
        if lock_file.exists():
            lock_file.unlink(missing_ok=True)


class CSVStore:
    """Thin CSV wrapper that writes atomically using temp files + rename."""

    def __init__(self, path: str | pathlib.Path, fieldnames: Iterable[str]) -> None:
        self.path = pathlib.Path(path).resolve()
        self.fieldnames = list(fieldnames)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.write_all([])

    def read_all(self) -> List[Dict[str, str]]:
        if not self.path.exists():
            return []
        with self.path.open("r", newline="") as fh:
            reader = csv.DictReader(fh)
            return list(reader)

    def append(self, row: Dict[str, str]) -> None:
        """Append a single row without rewriting the whole file."""
        with _file_lock(self.path):
            file_exists = self.path.exists()
            with self.path.open("a", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=self.fieldnames)
                if not file_exists or self.path.stat().st_size == 0:
                    writer.writeheader()
                writer.writerow(row)

    def write_all(self, rows: List[Dict[str, str]]) -> None:
        """Atomically rewrite the entire file with a temp + rename."""
        with _file_lock(self.path):
            tmp_fd, tmp_path = tempfile.mkstemp(dir=str(self.path.parent), prefix=self.path.name, text=True)
            try:
                with os.fdopen(tmp_fd, "w", newline="") as fh:
                    writer = csv.DictWriter(fh, fieldnames=self.fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                os.replace(tmp_path, self.path)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    def ensure_exists(self) -> None:
        """Create the CSV file with just a header row if it's missing or empty."""
        if not self.path.exists() or self.path.stat().st_size == 0:
            self.write_all([])
