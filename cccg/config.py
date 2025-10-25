"""Configuration helpers for the CCCG prototype."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DisplayConfig:
    """Visual settings for the pygame display."""

    width: int = 1280
    height: int = 720
    caption: str = "CCCG - Collectible Children Card Game"
    frame_rate: int = 60
    fullscreen: bool = False


@dataclass(frozen=True)
class AssetConfig:
    """Configuration for locating local assets."""

    root: Path = Path("assets")
    fonts: Path = Path("fonts")
    audio: Path = Path("audio")
    images: Path = Path("images")

    def font_path(self, name: str) -> Path:
        """Return the full path for a font asset."""

        return self.root / self.fonts / name

    def image_path(self, name: str) -> Path:
        """Return the full path for an image asset."""

        return self.root / self.images / name

    def audio_path(self, name: str) -> Path:
        """Return the full path for an audio asset."""

        return self.root / self.audio / name


@dataclass(frozen=True)
class GameConfig:
    """High-level configuration structure for the game."""

    display: DisplayConfig = DisplayConfig()
    assets: AssetConfig = AssetConfig()
