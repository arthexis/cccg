"""Asset discovery helpers for the CCCG prototype."""

from __future__ import annotations

from pathlib import Path

from .config import AssetConfig


class ResourceManager:
    """Utility to locate optional asset files."""

    def __init__(self, config: AssetConfig | None = None) -> None:
        self.config = config or AssetConfig()

    def resolve(self, path: Path | str) -> Path:
        """Resolve a path relative to the asset root."""

        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.config.root / candidate
        return candidate

    def require(self, path: Path | str) -> Path:
        """Ensure that the given asset exists on disk."""

        resolved = self.resolve(path)
        if not resolved.exists():
            raise FileNotFoundError(f"Asset not found: {resolved}")
        return resolved

    def ensure_directories(self) -> None:
        """Create the asset directories if they are missing."""

        for directory in (
            self.config.root,
            self.config.root / self.config.fonts,
            self.config.root / self.config.images,
            self.config.root / self.config.audio,
        ):
            directory.mkdir(parents=True, exist_ok=True)
