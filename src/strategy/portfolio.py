"""In-memory view of positions stored in CSV."""

from __future__ import annotations

from typing import Dict, List

from src.datastore.csv_store import CSVStore


class Portfolio:
    """Helper to load and query open positions from the CSV store."""

    def __init__(self, positions_store: CSVStore) -> None:
        self.positions_store = positions_store
        self.positions: Dict[str, Dict[str, str]] = {}
        self.refresh()

    def refresh(self) -> None:
        """Reload positions from disk."""
        self.positions = {row["position_id"]: row for row in self.positions_store.read_all()}

    def open_positions(self) -> List[Dict[str, str]]:
        return [p for p in self.positions.values() if p.get("status") == "OPEN"]

    def open_positions_for_symbol(self, symbol: str) -> List[Dict[str, str]]:
        return [p for p in self.open_positions() if p.get("symbol") == symbol]

