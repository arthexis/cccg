"""Pygame application bootstrap for the CCCG prototype."""

from __future__ import annotations

import pygame

from .config import GameConfig
from .resources import ResourceManager


class CardGameApp:
    """Minimal pygame wrapper that wires together the systems."""

    def __init__(self, config: GameConfig | None = None) -> None:
        self.config = config or GameConfig()
        self.resources = ResourceManager(self.config.assets)
        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.running = False

    def setup(self) -> None:
        """Initialise pygame and the display surface."""

        pygame.init()
        self.resources.ensure_directories()
        display = self.config.display
        flags = 0
        size = (display.width, display.height)

        if display.fullscreen:
            flags |= pygame.FULLSCREEN
            if display.width > 0 and display.height > 0:
                size = (display.width, display.height)
            else:
                info = pygame.display.Info()
                size = (info.current_w, info.current_h)

        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption(display.caption)
        self.clock = pygame.time.Clock()
        self.running = True

    def handle_events(self) -> None:
        """Consume pygame events."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self, dt: float) -> None:  # noqa: D401 - placeholder hook
        """Advance the game state by *dt* seconds."""

    def draw(self) -> None:
        """Render the current frame."""

        assert self.screen is not None
        self.screen.fill((32, 48, 64))
        pygame.display.flip()

    def run(self) -> None:
        """Run the main loop until the app stops."""

        if not self.running:
            self.setup()

        assert self.clock is not None
        display = self.config.display

        while self.running:
            self.handle_events()
            dt = self.clock.tick(display.frame_rate) / 1000.0
            self.update(dt)
            self.draw()

        pygame.quit()
