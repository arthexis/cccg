"""Visual game object classes for the simple poker demo."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import ClassVar, Deque, Tuple

import pygame


Color = Tuple[int, int, int]


@dataclass(slots=True)
class GameObject:
    """Base class for drawable objects that can be dragged around."""

    image: pygame.Surface
    position: tuple[int, int]
    scale: float = 1.0
    base_image: pygame.Surface = field(init=False, repr=False)
    shadow_trail: Deque[tuple[pygame.Vector2, float, float]] = field(
        init=False, repr=False
    )
    _shadow_last_sample: pygame.Vector2 | None = field(init=False, repr=False)
    _shadow_cache: dict[float, pygame.Surface] = field(init=False, repr=False)
    GRID_SPAN: ClassVar[tuple[int, int]] = (1, 1)
    SHADOW_LIFETIME: ClassVar[float] = 0.25
    SHADOW_MIN_DISTANCE: ClassVar[float] = 8.0

    def __post_init__(self) -> None:
        self.base_image = self.image.copy()
        self.scale = float(self.scale)
        self.rect = self.image.get_rect(topleft=self.position)
        self.shadow_trail = deque()
        self._shadow_last_sample = None
        self._shadow_cache = {}

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)

    def set_scale(self, scale: float) -> None:
        """Update the sprite scale while keeping its top-left anchored."""

        scale = max(scale, 0.01)
        if abs(scale - self.scale) < 1e-3:
            return

        old_topleft = self.rect.topleft
        self.scale = scale
        if abs(scale - 1.0) < 1e-3:
            self.image = self.base_image.copy()
        else:
            width = max(1, int(round(self.base_image.get_width() * scale)))
            height = max(1, int(round(self.base_image.get_height() * scale)))
            self.image = pygame.transform.smoothscale(self.base_image, (width, height))
        self.rect = self.image.get_rect()
        self.rect.topleft = old_topleft
        self.position = self.rect.topleft

    # Shadow helpers -------------------------------------------------

    def capture_shadow_sample(self) -> None:
        """Record the current sprite position for trailing shadows."""

        now = pygame.time.get_ticks() / 1000.0
        current_position = pygame.Vector2(self.rect.topleft)
        if (
            self._shadow_last_sample is not None
            and (current_position - self._shadow_last_sample).length_squared()
            < self.SHADOW_MIN_DISTANCE**2
        ):
            return

        self.shadow_trail.append((current_position, float(self.scale), now))
        self._shadow_last_sample = pygame.Vector2(current_position)
        self._trim_shadow_trail(now)

    def _trim_shadow_trail(self, now: float | None = None) -> None:
        """Discard outdated samples based on the configured lifetime."""

        if now is None:
            now = pygame.time.get_ticks() / 1000.0
        while self.shadow_trail and now - self.shadow_trail[0][2] > self.SHADOW_LIFETIME:
            self.shadow_trail.popleft()

    def update_shadow_history(self) -> None:
        """Refresh internal timers, removing expired shadow samples."""

        self._trim_shadow_trail()
        if not self.shadow_trail:
            self._shadow_last_sample = None

    def get_shadow_surface(self, scale: float) -> pygame.Surface:
        """Return a tinted copy of the sprite scaled to *scale* for shadows."""

        rounded_scale = round(scale * 1000) / 1000
        cached = self._shadow_cache.get(rounded_scale)
        if cached is not None:
            return cached

        if abs(scale - 1.0) < 1e-3:
            base = self.base_image
        else:
            width = max(1, int(round(self.base_image.get_width() * scale)))
            height = max(1, int(round(self.base_image.get_height() * scale)))
            base = pygame.transform.smoothscale(self.base_image, (width, height))

        shadow_surface = base.copy()
        shadow_surface.fill((0, 0, 0, 160), special_flags=pygame.BLEND_RGBA_MULT)
        self._shadow_cache[rounded_scale] = shadow_surface
        return shadow_surface


CARD_PADDING = 6


class CardSprite(GameObject):
    """Concrete sprite representing a face-up playing card."""

    CARD_SIZE = (90, 132)
    GRID_SPAN: ClassVar[tuple[int, int]] = (2, 3)

    SUIT_COLORS = {
        "♠": (20, 20, 20),
        "♣": (20, 20, 20),
        "♥": (200, 16, 46),
        "♦": (200, 16, 46),
    }

    def __init__(self, label: str, position: tuple[int, int]) -> None:
        image = self._create_card_surface(label)
        super().__init__(image=image, position=position)
        self.label = label

    @staticmethod
    def _create_card_surface(label: str) -> pygame.Surface:
        surface = pygame.Surface(CardSprite.CARD_SIZE, pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))

        border_radius = 12
        card_rect = surface.get_rect().inflate(-2 * CARD_PADDING, -2 * CARD_PADDING)
        face_color = (246, 246, 246)
        outline_color = (24, 24, 24)
        pygame.draw.rect(surface, face_color, card_rect, border_radius=border_radius)
        pygame.draw.rect(surface, outline_color, card_rect, width=2, border_radius=border_radius)

        value, suit = CardSprite._split_label(label)
        suit_color = CardSprite.SUIT_COLORS.get(suit, outline_color)

        value_font = CardSprite._load_font(48, bold=True)
        suit_font = CardSprite._load_font(40)
        center_font = CardSprite._load_font(82)

        value_surface = value_font.render(value, True, suit_color)
        suit_surface = suit_font.render(suit, True, suit_color)

        if suit:
            pip_surface = CardSprite._build_corner_pip(value_surface, suit_surface)
            padding = card_rect.left + 6
            surface.blit(pip_surface, (padding, card_rect.top + 6))
            pip_rotated = pygame.transform.rotate(pip_surface, 180)
            pip_rect = pip_rotated.get_rect()
            pip_rect.bottomright = (
                card_rect.right - 6,
                card_rect.bottom - 6,
            )
            surface.blit(pip_rotated, pip_rect)

        if suit:
            center_surface = center_font.render(suit, True, suit_color)
            center_rect = center_surface.get_rect(center=card_rect.center)
            surface.blit(center_surface, center_rect)
        else:
            # Fallback to centered label when no suit is provided.
            fallback_font = CardSprite._load_font(54)
            text = fallback_font.render(label, True, outline_color)
            text_rect = text.get_rect(center=card_rect.center)
            surface.blit(text, text_rect)

        return surface

    @staticmethod
    def _load_font(size: int, bold: bool = False) -> pygame.font.Font:
        """Load a font that supports suit glyphs with sensible fallbacks."""

        preferred_fonts = [
            "dejavusans",
            "arialunicode",
            "arial",
            "liberationsans",
        ]
        for name in preferred_fonts:
            path = pygame.font.match_font(name, bold=bold)
            if path:
                return pygame.font.Font(path, size)
        return pygame.font.Font(None, size)

    @staticmethod
    def _split_label(label: str) -> tuple[str, str]:
        if not label:
            return "", ""
        suit = label[-1]
        if suit in CardSprite.SUIT_COLORS:
            value = label[:-1] or suit
            return value, suit
        return label, ""

    @staticmethod
    def _build_corner_pip(value_surface: pygame.Surface, suit_surface: pygame.Surface) -> pygame.Surface:
        diag_offset = 8
        width = max(value_surface.get_width(), suit_surface.get_width() + diag_offset)
        height = value_surface.get_height() + suit_surface.get_height() - diag_offset
        height = max(height, max(value_surface.get_height(), suit_surface.get_height()))
        pip_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pip_surface.blit(value_surface, (0, 0))
        pip_surface.blit(
            suit_surface,
            (
                width - suit_surface.get_width(),
                height - suit_surface.get_height(),
            ),
        )
        return pip_surface


class DeckSprite(GameObject):
    """Sprite representing a face-down deck of playing cards."""

    DECK_SIZE = CardSprite.CARD_SIZE
    GRID_SPAN: ClassVar[tuple[int, int]] = (2, 3)

    def __init__(self, position: tuple[int, int]) -> None:
        image = self._create_deck_surface()
        super().__init__(image=image, position=position)

    @staticmethod
    def _create_deck_surface() -> pygame.Surface:
        surface = pygame.Surface(DeckSprite.DECK_SIZE, pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))

        outer_rect = surface.get_rect()
        border_radius = 16
        card_rect = outer_rect.inflate(-2 * CARD_PADDING, -2 * CARD_PADDING)

        base_color: Color = (120, 0, 0)
        pygame.draw.rect(surface, base_color, card_rect, border_radius=border_radius)

        edge_color: Color = (160, 30, 30)
        edge_spacing = 6
        edge_height = 3
        for offset in range(edge_spacing, min(5 * edge_spacing, card_rect.height // 2), edge_spacing):
            edge_rect = pygame.Rect(card_rect.left + 8, card_rect.top + offset, card_rect.width - 16, edge_height)
            pygame.draw.rect(surface, edge_color, edge_rect, border_radius=1)

        inner_rect = card_rect.inflate(-18, -18)
        gradient_surface = pygame.Surface(inner_rect.size, pygame.SRCALPHA)
        top_color = pygame.Color(210, 60, 60)
        bottom_color = pygame.Color(90, 0, 0)
        height = inner_rect.height or 1
        for y in range(inner_rect.height):
            ratio = y / (height - 1 or 1)
            color = (
                int(top_color.r + (bottom_color.r - top_color.r) * ratio),
                int(top_color.g + (bottom_color.g - top_color.g) * ratio),
                int(top_color.b + (bottom_color.b - top_color.b) * ratio),
            )
            pygame.draw.line(
                gradient_surface,
                color,
                (0, y),
                (inner_rect.width, y),
            )

        pattern_surface = pygame.Surface(inner_rect.size, pygame.SRCALPHA)
        spacing = 10
        pattern_color = (255, 215, 215, 70)
        for offset in range(-inner_rect.height, inner_rect.width, spacing):
            start = (offset, 0)
            end = (offset + inner_rect.height, inner_rect.height)
            pygame.draw.line(pattern_surface, pattern_color, start, end, width=1)
        for offset in range(0, inner_rect.width + inner_rect.height, spacing):
            start = (offset, 0)
            end = (offset - inner_rect.height, inner_rect.height)
            pygame.draw.line(pattern_surface, pattern_color, start, end, width=1)

        gradient_surface.blit(pattern_surface, (0, 0))

        highlight_height = max(8, inner_rect.height // 3)
        highlight_surface = pygame.Surface((inner_rect.width, highlight_height), pygame.SRCALPHA)
        for y in range(highlight_height):
            alpha = int(120 * (1 - y / max(highlight_height - 1, 1)))
            pygame.draw.line(
                highlight_surface,
                (255, 255, 255, alpha),
                (0, y),
                (inner_rect.width, y),
            )
        gradient_surface.blit(highlight_surface, (0, 0))

        surface.blit(gradient_surface, inner_rect.topleft)

        border_color: Color = (30, 0, 0)
        accent_color: Color = (230, 200, 200)
        pygame.draw.rect(surface, border_color, card_rect, width=3, border_radius=border_radius)
        pygame.draw.rect(
            surface,
            accent_color,
            card_rect.inflate(-10, -10),
            width=2,
            border_radius=max(border_radius - 4, 0),
        )

        return surface
