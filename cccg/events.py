"""Custom pygame events used by the CCCG prototype."""

from __future__ import annotations

import pygame

# Reserve a block of user events for the game.
USER_EVENT_BASE = pygame.USEREVENT + 1
CARD_DRAWN = USER_EVENT_BASE + 0
TURN_STARTED = USER_EVENT_BASE + 1
TURN_ENDED = USER_EVENT_BASE + 2
