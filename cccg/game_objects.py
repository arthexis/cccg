"""Visual game object classes for the simple poker demo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Tuple

import pygame


Color = Tuple[int, int, int]


@dataclass(slots=True)
class GameObject:
    """Base class for drawable objects that can be dragged around."""

    image: pygame.Surface
    position: tuple[int, int]
    scale: float = 1.0
    base_image: pygame.Surface = field(init=False, repr=False)
    GRID_SPAN: ClassVar[tuple[int, int]] = (1, 1)

    def __post_init__(self) -> None:
        self.base_image = self.image.copy()
        self.scale = float(self.scale)
        self.rect = self.image.get_rect(topleft=self.position)

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


CARD_PADDING = 6


class CardSprite(GameObject):
    """Concrete sprite representing a face-up playing card."""

    CARD_SIZE = (90, 132)
    GRID_SPAN: ClassVar[tuple[int, int]] = (2, 3)
    RENDER_SCALE = 4

    SUIT_COLORS = {
        "♠": (20, 20, 20),
        "♣": (20, 20, 20),
        "♥": (200, 16, 46),
        "♦": (200, 16, 46),
    }

    def __init__(self, label: str, position: tuple[int, int]) -> None:
        hi_res_image = self._create_card_surface(label, scale=self.RENDER_SCALE)
        image = pygame.transform.smoothscale(hi_res_image, CardSprite.CARD_SIZE)
        super().__init__(image=image, position=position)
        self.label = label
        self.hi_res_image = hi_res_image
        self.hi_res_scale = float(self.RENDER_SCALE)

    @staticmethod
    def _create_card_surface(label: str, scale: int = 1) -> pygame.Surface:
        width = CardSprite.CARD_SIZE[0] * scale
        height = CardSprite.CARD_SIZE[1] * scale
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))

        border_radius = 12 * scale
        card_rect = surface.get_rect().inflate(-2 * CARD_PADDING * scale, -2 * CARD_PADDING * scale)
        face_color = (246, 246, 246)
        outline_color = (24, 24, 24)
        pygame.draw.rect(surface, face_color, card_rect, border_radius=border_radius)
        pygame.draw.rect(surface, outline_color, card_rect, width=2, border_radius=border_radius)

        value, suit = CardSprite._split_label(label)
        suit_color = CardSprite.SUIT_COLORS.get(suit, outline_color)

        value_font = CardSprite._load_font(48 * scale, bold=True)
        suit_font = CardSprite._load_font(40 * scale)
        center_font = CardSprite._load_font(82 * scale)

        if suit:
            value_surface = value_font.render(value, True, suit_color)
            suit_surface = suit_font.render(suit, True, suit_color)

            padding = 6 * scale
            surface.blit(value_surface, (card_rect.left + padding, card_rect.top + padding))

            suit_rect = suit_surface.get_rect()
            suit_rect.bottomright = (
                card_rect.right - padding,
                card_rect.bottom - padding,
            )
            surface.blit(suit_surface, suit_rect)

            center_surface = center_font.render(suit, True, suit_color)
            center_rect = center_surface.get_rect(center=card_rect.center)
            surface.blit(center_surface, center_rect)
        else:
            # Fallback to centered label when no suit is provided.
            fallback_font = CardSprite._load_font(54 * scale)
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

class DeckSprite(GameObject):
    """Sprite representing a face-down deck of playing cards."""

    DECK_SIZE = CardSprite.CARD_SIZE
    GRID_SPAN: ClassVar[tuple[int, int]] = (2, 3)
    RENDER_SCALE = CardSprite.RENDER_SCALE

    def __init__(self, position: tuple[int, int]) -> None:
        hi_res_image = self._create_deck_surface(scale=self.RENDER_SCALE)
        image = pygame.transform.smoothscale(hi_res_image, DeckSprite.DECK_SIZE)
        super().__init__(image=image, position=position)
        self.hi_res_image = hi_res_image
        self.hi_res_scale = float(self.RENDER_SCALE)

    @staticmethod
    def _create_deck_surface(scale: int = 1) -> pygame.Surface:
        width = DeckSprite.DECK_SIZE[0] * scale
        height = DeckSprite.DECK_SIZE[1] * scale
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))

        outer_rect = surface.get_rect()
        border_radius = 16 * scale
        card_rect = outer_rect.inflate(-2 * CARD_PADDING * scale, -2 * CARD_PADDING * scale)

        base_color: Color = (120, 0, 0)
        pygame.draw.rect(surface, base_color, card_rect, border_radius=border_radius)

        edge_color: Color = (160, 30, 30)
        edge_spacing = 6 * scale
        edge_height = 3 * scale
        horizontal_padding = 8 * scale
        for offset in range(edge_spacing, min(5 * edge_spacing, card_rect.height // 2), edge_spacing):
            edge_rect = pygame.Rect(
                card_rect.left + horizontal_padding,
                card_rect.top + offset,
                card_rect.width - 2 * horizontal_padding,
                edge_height,
            )
            pygame.draw.rect(surface, edge_color, edge_rect, border_radius=1)

        inner_rect = card_rect.inflate(-18 * scale, -18 * scale)
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
        spacing = 10 * scale
        pattern_color = (255, 215, 215, 70)
        line_width = max(1, scale)
        for offset in range(-inner_rect.height, inner_rect.width, spacing):
            start = (offset, 0)
            end = (offset + inner_rect.height, inner_rect.height)
            pygame.draw.line(pattern_surface, pattern_color, start, end, width=line_width)
        for offset in range(0, inner_rect.width + inner_rect.height, spacing):
            start = (offset, 0)
            end = (offset - inner_rect.height, inner_rect.height)
            pygame.draw.line(pattern_surface, pattern_color, start, end, width=line_width)

        gradient_surface.blit(pattern_surface, (0, 0))

        highlight_height = max(8 * scale, inner_rect.height // 3)
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
        pygame.draw.rect(
            surface,
            border_color,
            card_rect,
            width=max(1, 3 * scale),
            border_radius=border_radius,
        )
        pygame.draw.rect(
            surface,
            accent_color,
            card_rect.inflate(-10 * scale, -10 * scale),
            width=max(1, 2 * scale),
            border_radius=max(border_radius - 4 * scale, 0),
        )

        return surface
