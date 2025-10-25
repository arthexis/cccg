"""Pygame application bootstrap for the CCCG prototype."""

from __future__ import annotations

import math

import pygame

from .config import GameConfig
from .game_objects import CardSprite, DeckSprite, GameObject
from .resources import ResourceManager


class CardGameApp:
    """Minimal pygame wrapper that wires together the systems."""

    GRID_CELL_SIZE = 48
    GRID_DASH_LENGTH = 10
    GRID_GAP_LENGTH = 6
    GRID_LINE_WIDTH = 1

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
        self.zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 2.0
        self.camera_center = pygame.Vector2(0, 0)
        self.pan_active = False
        self.pan_last_pos = pygame.Vector2()

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
                pointer_world = self._screen_to_world(pygame.Vector2(event.pos))
                if not self._begin_drag(pointer_world):
                    self._begin_pan(pygame.Vector2(event.pos))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                pointer_world = self._screen_to_world(pygame.Vector2(event.pos))
                self._end_drag(pointer_world)
                self._end_pan()
            elif event.type == pygame.MOUSEWHEEL:
                self._adjust_zoom(event.y)

    def update(self, dt: float) -> None:  # noqa: D401 - placeholder hook
        """Advance the game state by *dt* seconds."""

        if self.dragged_object is not None:
            pointer = self._screen_to_world(pygame.Vector2(pygame.mouse.get_pos()))
            self._drag_object(pointer)
        elif self.pan_active:
            self._update_pan(pygame.Vector2(pygame.mouse.get_pos()))

    def draw(self) -> None:
        """Render the current frame."""

        assert self.screen is not None
        self.screen.fill((32, 48, 64))
        if self.dragged_object is not None or self.pan_active:
            self._draw_grid(self.screen)
        for obj in self.objects:
            self._draw_object(self.screen, obj)
        pygame.display.flip()

    # Internal helpers -------------------------------------------------

    def _create_initial_objects(self) -> None:
        """Populate the scene with an ace of spades and a deck."""

        card_width, card_height = CardSprite.CARD_SIZE
        _, deck_height = DeckSprite.DECK_SIZE
        horizontal_gap = 24
        card_position = (-card_width - horizontal_gap // 2, -card_height // 2)
        deck_position = (horizontal_gap // 2, -deck_height // 2)

        self.objects = [
            CardSprite("A♠", position=card_position),
            DeckSprite(position=deck_position),
        ]
        for obj in self.objects:
            self._snap_object_to_grid(obj)
        self.dragged_object = None

    def _begin_drag(self, pointer: pygame.Vector2) -> bool:
        """Start dragging the top-most object under *pointer* if any."""

        for index in range(len(self.objects) - 1, -1, -1):
            candidate = self.objects[index]
            if candidate.rect.collidepoint(pointer.x, pointer.y):
                self.dragged_object = candidate
                self.drag_offset = pointer - pygame.Vector2(candidate.rect.topleft)
                # bring to front for rendering
                self.objects.append(self.objects.pop(index))
                candidate.set_scale(self.drag_scale)
                self.drag_offset = pointer - pygame.Vector2(candidate.rect.topleft)
                self._drag_object(pointer)
                return True

        return False

    def _drag_object(self, pointer: pygame.Vector2) -> None:
        """Reposition the currently dragged object to follow *pointer*."""

        if self.dragged_object is None:
            return
        self.dragged_object.capture_shadow_sample()
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
        self._snap_object_to_grid(self.dragged_object)
        self.dragged_object = None

    def _begin_pan(self, screen_position: pygame.Vector2) -> None:
        """Start panning the camera following the pointer."""

        self.pan_active = True
        self.pan_last_pos = pygame.Vector2(screen_position)

    def _update_pan(self, screen_position: pygame.Vector2) -> None:
        """Update the camera position while panning."""

        if not self.pan_active:
            return
        delta = pygame.Vector2(screen_position) - self.pan_last_pos
        if delta.length_squared() > 0:
            self.camera_center -= delta / max(self.zoom, 1e-6)
            self.pan_last_pos = pygame.Vector2(screen_position)

    def _end_pan(self) -> None:
        """Stop panning the camera."""

        self.pan_active = False

    # Grid helpers -----------------------------------------------------

    def _draw_grid(self, surface: pygame.Surface) -> None:
        """Render a dashed white grid centred on the play area."""

        grid_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        color = pygame.Color(255, 255, 255, 150)

        assert self.screen is not None
        screen_width, screen_height = self.screen.get_size()

        top_left_world = self._screen_to_world(pygame.Vector2(0, 0))
        bottom_right_world = self._screen_to_world(pygame.Vector2(screen_width, screen_height))

        left_world = min(top_left_world.x, bottom_right_world.x)
        right_world = max(top_left_world.x, bottom_right_world.x)
        top_world = min(top_left_world.y, bottom_right_world.y)
        bottom_world = max(top_left_world.y, bottom_right_world.y)

        cell = self.GRID_CELL_SIZE
        start_x = math.floor(left_world / cell) * cell
        end_x = math.ceil(right_world / cell) * cell
        start_y = math.floor(top_world / cell) * cell
        end_y = math.ceil(bottom_world / cell) * cell

        x = start_x
        while x <= end_x:
            start = pygame.Vector2(x, start_y)
            end = pygame.Vector2(x, end_y)
            self._draw_dashed_line(grid_surface, color, start, end)
            x += cell

        y = start_y
        while y <= end_y:
            start = pygame.Vector2(start_x, y)
            end = pygame.Vector2(end_x, y)
            self._draw_dashed_line(grid_surface, color, start, end)
            y += cell

        surface.blit(grid_surface, (0, 0))

    def _draw_dashed_line(
        self,
        surface: pygame.Surface,
        color: pygame.Color,
        start: pygame.Vector2,
        end: pygame.Vector2,
    ) -> None:
        """Draw a dashed line between *start* and *end* on *surface*."""

        dash = self.GRID_DASH_LENGTH
        gap = self.GRID_GAP_LENGTH

        start_vec = pygame.Vector2(start)
        end_vec = pygame.Vector2(end)
        direction = end_vec - start_vec
        length = direction.length()
        if length == 0:
            return

        direction.normalize_ip()
        progress = 0.0

        while progress < length:
            dash_end = min(progress + dash, length)
            start_point = start_vec + direction * progress
            end_point = start_vec + direction * dash_end
            start_screen = self._world_to_screen(start_point)
            end_screen = self._world_to_screen(end_point)
            pygame.draw.line(
                surface,
                color,
                (int(round(start_screen.x)), int(round(start_screen.y))),
                (int(round(end_screen.x)), int(round(end_screen.y))),
                max(1, int(round(self.GRID_LINE_WIDTH * self.zoom))),
            )
            progress = dash_end + gap

    def _draw_object(self, surface: pygame.Surface, obj: GameObject) -> None:
        """Draw *obj* onto *surface* accounting for the current zoom."""

        self._draw_shadow_trail(surface, obj)
        world_position = pygame.Vector2(obj.rect.topleft)
        screen_position = self._world_to_screen(world_position)
        if abs(self.zoom - 1.0) < 1e-3:
            image = obj.image
        else:
            width = max(1, int(round(obj.image.get_width() * self.zoom)))
            height = max(1, int(round(obj.image.get_height() * self.zoom)))
            image = pygame.transform.smoothscale(obj.image, (width, height))
        draw_rect = image.get_rect()
        draw_rect.topleft = (int(round(screen_position.x)), int(round(screen_position.y)))
        surface.blit(image, draw_rect)

    def _draw_shadow_trail(self, surface: pygame.Surface, obj: GameObject) -> None:
        """Render trailing motion shadows for *obj* if available."""

        obj.update_shadow_history()
        if not obj.shadow_trail:
            return

        current_time = pygame.time.get_ticks() / 1000.0
        for position, scale, timestamp in obj.shadow_trail:
            age = current_time - timestamp
            if age < 0 or age > obj.SHADOW_LIFETIME:
                continue

            fade = max(0.0, min(1.0, 1.0 - age / obj.SHADOW_LIFETIME))
            shadow_surface = obj.get_shadow_surface(scale)
            if abs(self.zoom - 1.0) < 1e-3:
                scaled_shadow = shadow_surface
            else:
                width = max(1, int(round(shadow_surface.get_width() * self.zoom)))
                height = max(1, int(round(shadow_surface.get_height() * self.zoom)))
                scaled_shadow = pygame.transform.smoothscale(
                    shadow_surface, (width, height)
                )

            shadow_image = scaled_shadow.copy()
            shadow_image.fill(
                (255, 255, 255, int(round(255 * fade))),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            screen_position = self._world_to_screen(position)
            draw_rect = shadow_image.get_rect()
            draw_rect.topleft = (
                int(round(screen_position.x)),
                int(round(screen_position.y)),
            )
            surface.blit(shadow_image, draw_rect)

    def _snap_object_to_grid(self, obj: GameObject) -> None:
        """Snap *obj* to the nearest grid coordinate, respecting its span."""

        cell = self.GRID_CELL_SIZE
        span_x, span_y = getattr(obj, "GRID_SPAN", (1, 1))

        block_width = span_x * cell
        block_height = span_y * cell

        margin_x = max(0.0, (block_width - obj.rect.width) / 2)
        margin_y = max(0.0, (block_height - obj.rect.height) / 2)
        margin_vec = pygame.Vector2(margin_x, margin_y)

        block_candidate = pygame.Vector2(obj.rect.topleft) - margin_vec
        if cell > 0:
            cell_x = round(block_candidate.x / cell)
            cell_y = round(block_candidate.y / cell)
        else:
            cell_x = cell_y = 0

        snapped_block = pygame.Vector2(cell_x * cell, cell_y * cell)
        snapped_position = snapped_block + margin_vec

        obj.rect.topleft = (int(snapped_position.x), int(snapped_position.y))
        obj.position = obj.rect.topleft

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

    # Coordinate helpers ----------------------------------------------

    def _adjust_zoom(self, steps: int) -> None:
        """Modify the global zoom level by *steps* scroll increments."""

        if steps == 0:
            return
        zoom_factor = 1.2 ** steps
        new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * zoom_factor))
        if abs(new_zoom - self.zoom) < 1e-6:
            return
        mouse_position = pygame.Vector2(pygame.mouse.get_pos())
        focus_before = self._screen_to_world(mouse_position)
        self.zoom = new_zoom
        focus_after = self._screen_to_world(mouse_position)
        self.camera_center += focus_before - focus_after

    def _world_to_screen(self, point: pygame.Vector2) -> pygame.Vector2:
        """Convert a world-space *point* to screen-space coordinates."""

        assert self.screen is not None
        screen_size = pygame.Vector2(self.screen.get_size())
        screen_center = screen_size / 2
        offset = pygame.Vector2(point) - self.camera_center
        return screen_center + offset * self.zoom

    def _screen_to_world(self, point: pygame.Vector2) -> pygame.Vector2:
        """Convert a screen-space *point* to world-space coordinates."""

        assert self.screen is not None
        screen_size = pygame.Vector2(self.screen.get_size())
        screen_center = screen_size / 2
        offset = pygame.Vector2(point) - screen_center
        if self.zoom != 0:
            offset /= self.zoom
        return self.camera_center + offset
