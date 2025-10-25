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

    def __init__(self, label: str, position: tuple[int, int]) -> None:
        image = self._create_card_surface(label)
        super().__init__(image=image, position=position)
        self.label = label

    @staticmethod
    def _create_card_surface(label: str) -> pygame.Surface:
        surface = pygame.Surface(CardSprite.CARD_SIZE, pygame.SRCALPHA)
        surface.fill((242, 242, 242))
        pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), width=3, border_radius=8)

        font = pygame.font.Font(None, 54)
        text = font.render(label, True, (0, 0, 0))
        text_rect = text.get_rect(center=(CardSprite.CARD_SIZE[0] // 2, CardSprite.CARD_SIZE[1] // 2))
        surface.blit(text, text_rect)
        return surface


class DeckSprite(GameObject):
    """Sprite representing a face-down deck of playing cards."""

    DECK_SIZE = (90, 120)

    def __init__(self, position: tuple[int, int]) -> None:
        image = self._create_deck_surface()
        super().__init__(image=image, position=position)

    @staticmethod
    def _create_deck_surface() -> pygame.Surface:
        surface = pygame.Surface(DeckSprite.DECK_SIZE, pygame.SRCALPHA)
        base_color: Color = (32, 96, 64)
        accent_color: Color = (255, 255, 255)
        surface.fill(base_color)
        pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), width=3, border_radius=10)

        card_rect = surface.get_rect().inflate(-16, -16)
        for offset in range(0, 15, 5):
            shifted = card_rect.move(offset, -offset)
            pygame.draw.rect(surface, accent_color, shifted, width=2, border_radius=6)

        stripe_rect = pygame.Rect(0, 0, surface.get_width(), 28)
        stripe_rect.center = surface.get_rect().center
        pygame.draw.rect(surface, (180, 0, 0), stripe_rect, border_radius=6)
        pygame.draw.rect(surface, accent_color, stripe_rect, width=2, border_radius=6)
        return surface
