"""Game domain models for the CCCG prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass(slots=True)
class Card:
    """Represents a card template in the game."""

    identifier: str
    name: str
    description: str = ""
    cost: int = 0
    attack: int = 0
    defense: int = 0


@dataclass(slots=True)
class Deck:
    """Collection of cards that can be drawn from."""

    cards: List[Card] = field(default_factory=list)

    def draw(self) -> Card | None:
        """Remove and return the top card from the deck."""

        if not self.cards:
            return None
        return self.cards.pop(0)

    def add(self, card: Card) -> None:
        """Add a card to the bottom of the deck."""

        self.cards.append(card)

    def extend(self, cards: Iterable[Card]) -> None:
        """Add multiple cards to the deck."""

        self.cards.extend(cards)

    def shuffle(self) -> None:
        """Shuffle the deck in place."""

        from random import shuffle

        shuffle(self.cards)


@dataclass(slots=True)
class Hand:
    """Cards held by a player."""

    cards: List[Card] = field(default_factory=list)

    def add(self, card: Card) -> None:
        """Add a card to the hand."""

        self.cards.append(card)

    def remove(self, card: Card) -> None:
        """Remove a specific card from the hand."""

        self.cards.remove(card)


@dataclass(slots=True)
class Player:
    """Represents a game participant."""

    name: str
    deck: Deck
    hand: Hand = field(default_factory=Hand)
    health: int = 20

    def draw_card(self) -> Card | None:
        """Draw the next card from the deck into the hand."""

        card = self.deck.draw()
        if card is not None:
            self.hand.add(card)
        return card
