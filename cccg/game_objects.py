"""Visual game object classes for the simple poker demo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import pygame


Color = Tuple[int, int, int]


@dataclass(slots=True)
class GameObject:
    """Base class for drawable objects that can be dragged around."""

    image: pygame.Surface
    position: tuple[int, int]

    def __post_init__(self) -> None:
        self.rect = self.image.get_rect(topleft=self.position)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)


class CardSprite(GameObject):
    """Concrete sprite representing a face-up playing card."""

    CARD_SIZE = (80, 112)

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
        card_rect = surface.get_rect()
        face_color = (246, 246, 246)
        outline_color = (24, 24, 24)
        pygame.draw.rect(surface, face_color, card_rect, border_radius=border_radius)
        pygame.draw.rect(surface, outline_color, card_rect, width=2, border_radius=border_radius)

        value, suit = CardSprite._split_label(label)
        suit_color = CardSprite.SUIT_COLORS.get(suit, outline_color)

        value_font = pygame.font.Font(None, 48)
        suit_font = pygame.font.Font(None, 40)
        center_font = pygame.font.Font(None, 76)

        value_surface = value_font.render(value, True, suit_color)
        suit_surface = suit_font.render(suit, True, suit_color)

        if suit:
            pip_surface = CardSprite._build_corner_pip(value_surface, suit_surface)
            padding = 10
            surface.blit(pip_surface, (padding, padding))
            pip_rotated = pygame.transform.rotate(pip_surface, 180)
            pip_rect = pip_rotated.get_rect()
            pip_rect.bottomright = (
                CardSprite.CARD_SIZE[0] - padding,
                CardSprite.CARD_SIZE[1] - padding,
            )
            surface.blit(pip_rotated, pip_rect)

        if suit:
            center_surface = center_font.render(suit, True, suit_color)
            center_rect = center_surface.get_rect(center=card_rect.center)
            surface.blit(center_surface, center_rect)
        else:
            # Fallback to centered label when no suit is provided.
            fallback_font = pygame.font.Font(None, 54)
            text = fallback_font.render(label, True, outline_color)
            text_rect = text.get_rect(center=card_rect.center)
            surface.blit(text, text_rect)

        return surface

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

    DECK_SIZE = (90, 132)

    def __init__(self, position: tuple[int, int]) -> None:
        image = self._create_deck_surface()
        super().__init__(image=image, position=position)

    @staticmethod
    def _create_deck_surface() -> pygame.Surface:
        surface = pygame.Surface(DeckSprite.DECK_SIZE, pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))

        rect = surface.get_rect()
        border_radius = 16
        base_color: Color = (120, 0, 0)
        pygame.draw.rect(surface, base_color, rect, border_radius=border_radius)

        inner_rect = rect.inflate(-18, -18)
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
        pygame.draw.rect(surface, border_color, rect, width=3, border_radius=border_radius)
        pygame.draw.rect(surface, accent_color, rect.inflate(-10, -10), width=2, border_radius=border_radius - 4)

        return surface
