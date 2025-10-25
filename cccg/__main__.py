"""Command-line entry point for the CCCG prototype."""

from __future__ import annotations

import argparse

from .app import CardGameApp
from .config import DisplayConfig, GameConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the CCCG pygame prototype.")
    parser.add_argument(
        "--width",
        type=int,
        help="Override the display width.",
    )
    parser.add_argument(
        "--height",
        type=int,
        help="Override the display height.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        help="Override the target frame rate.",
    )
    parser.add_argument(
        "--fullscreen",
        dest="fullscreen",
        action="store_true",
        help="Start the game in full-screen windowed mode.",
    )
    parser.add_argument(
        "--windowed",
        dest="fullscreen",
        action="store_false",
        help="Force the game to start in windowed mode.",
    )
    parser.set_defaults(fullscreen=None)
    return parser


def parse_config(namespace: argparse.Namespace) -> GameConfig:
    config = GameConfig()
    display = config.display
    width = namespace.width or display.width
    height = namespace.height or display.height
    fps = namespace.fps or display.frame_rate
    fullscreen = (
        display.fullscreen
        if namespace.fullscreen is None
        else namespace.fullscreen
    )

    return GameConfig(
        display=DisplayConfig(
            width=width,
            height=height,
            caption=display.caption,
            frame_rate=fps,
            fullscreen=fullscreen,
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = parse_config(args)
    app = CardGameApp(config)
    app.run()
    return 0


if __name__ == "__main__":  # pragma: no cover - module use only
    raise SystemExit(main())
