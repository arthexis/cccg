"""Pygame application bootstrap for the CCCG prototype."""

from __future__ import annotations

import pygame

from .config import GameConfig
from .game_objects import CardSprite, DeckSprite, GameObject
from .resources import ResourceManager


class CardGameApp:
    """Minimal pygame wrapper that wires together the systems."""

    def __init__(self, config: GameConfig | None = None) -> None:
        self.config = config or GameConfig()
        self.resources = ResourceManager(self.config.assets)
        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.running = False
        self.objects: list[GameObject] = []
        self.dragged_object: GameObject | None = None
        self.drag_offset = pygame.Vector2()
        self.drag_scale = 1.15

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
        self._create_initial_objects()

    def handle_events(self) -> None:
        """Consume pygame events."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._begin_drag(pygame.Vector2(event.pos))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._end_drag(pygame.Vector2(event.pos))

    def update(self, dt: float) -> None:  # noqa: D401 - placeholder hook
        """Advance the game state by *dt* seconds."""

        if self.dragged_object is not None:
            self._drag_object(pygame.Vector2(pygame.mouse.get_pos()))

    def draw(self) -> None:
        """Render the current frame."""

        assert self.screen is not None
        self.screen.fill((32, 48, 64))
        for obj in self.objects:
            obj.draw(self.screen)
        pygame.display.flip()

    # Internal helpers -------------------------------------------------

    def _create_initial_objects(self) -> None:
        """Populate the scene with an ace of spades and a deck."""

        self.objects = [
            CardSprite("A♠", position=(120, 140)),
            DeckSprite(position=(320, 120)),
        ]
        self.dragged_object = None

    def _begin_drag(self, pointer: pygame.Vector2) -> None:
        """Start dragging the top-most object under *pointer* if any."""

        for index in range(len(self.objects) - 1, -1, -1):
            candidate = self.objects[index]
            if candidate.rect.collidepoint(pointer):
                self.dragged_object = candidate
                self.drag_offset = pointer - pygame.Vector2(candidate.rect.topleft)
                # bring to front for rendering
                self.objects.append(self.objects.pop(index))
                candidate.set_scale(self.drag_scale)
                self.drag_offset = pointer - pygame.Vector2(candidate.rect.topleft)
                self._drag_object(pointer)
                break

    def _drag_object(self, pointer: pygame.Vector2) -> None:
        """Reposition the currently dragged object to follow *pointer*."""

        if self.dragged_object is None:
            return
        new_position = pointer - self.drag_offset
        top_left = (int(new_position.x), int(new_position.y))
        self.dragged_object.rect.topleft = top_left
        self.dragged_object.position = top_left

    def _end_drag(self, pointer: pygame.Vector2) -> None:
        """Release the currently dragged object, if any."""

        if self.dragged_object is None:
            return
        self._drag_object(pointer)
        self.dragged_object.set_scale(1.0)
        self.dragged_object = None

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
