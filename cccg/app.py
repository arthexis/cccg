"""Pygame application bootstrap for the CCCG prototype."""

from __future__ import annotations

import math

import pygame

from typing import Iterable

from .config import GameConfig
from .game_objects import Amarre, CardSprite, DeckSprite, GameObject
from .resources import ResourceManager


class HandZone:
    """Screen-anchored holder for cards currently in the player's hand."""

    LEFT_RIGHT_MARGIN_RATIO = 0.08
    BOTTOM_MARGIN_RATIO = 0.0
    ARC_HEIGHT_RATIO = 0.15
    HOVER_LIFT_RATIO = 0.20
    ZONE_HEIGHT_RATIO = 0.25
    HAND_SCALE = 1.5
    HOVER_SCALE_MULTIPLIER = 1.5
    HANG_DEPTH_RATIO = 0.40

    def __init__(self) -> None:
        self.cards: list[CardSprite] = []

    def add_card(self, app: "CardGameApp", card: CardSprite) -> None:
        """Add *card* to the hand if it is not already managed."""

        if card in self.cards:
            return
        app._detach_card_from_amarre(card)
        card.in_hand = True
        card.hand_hovered = False
        card.hand_screen_rect = None
        self.cards.append(card)
        if card in app.objects:
            app.objects.remove(card)
            app.objects.append(card)
        self.update(app)

    def remove_card(self, app: "CardGameApp", card: CardSprite) -> None:
        """Remove *card* from the hand if present."""

        if card not in self.cards:
            return
        self.cards.remove(card)
        card.in_hand = False
        card.hand_hovered = False
        card.hand_screen_rect = None
        if self.cards:
            self.update(app)

    def handle_drop(
        self, app: "CardGameApp", card: CardSprite, pointer_screen: pygame.Vector2
    ) -> bool:
        """Place *card* into the hand when it touches the bottom of the screen."""

        if app.screen is None:
            return False

        if getattr(card, "amarre", None) is not None:
            return False

        screen_width, screen_height = app.screen.get_size()
        zone_top = screen_height * (1.0 - self.ZONE_HEIGHT_RATIO)
        if pointer_screen.y >= zone_top:
            self.add_card(app, card)
            return True

        card_screen_topleft = app._world_to_screen(pygame.Vector2(card.rect.topleft))
        card_screen_rect = pygame.Rect(
            int(round(card_screen_topleft.x)),
            int(round(card_screen_topleft.y)),
            card.image.get_width(),
            card.image.get_height(),
        )
        bottom_margin = screen_height * self.BOTTOM_MARGIN_RATIO
        if card_screen_rect.bottom >= screen_height - bottom_margin:
            self.add_card(app, card)
            return True

        return False

    def update(self, app: "CardGameApp") -> None:
        """Arrange the cards in hand along a gentle arc at the bottom of the screen."""

        if app.screen is None or not self.cards:
            return

        screen_width, screen_height = app.screen.get_size()
        margin = screen_width * self.LEFT_RIGHT_MARGIN_RATIO
        available_width = max(0.0, screen_width - 2 * margin)
        bottom_margin_pixels = screen_height * self.BOTTOM_MARGIN_RATIO
        arc_height = screen_height * self.ARC_HEIGHT_RATIO
        hover_lift = screen_height * self.HOVER_LIFT_RATIO
        pointer = pygame.Vector2(pygame.mouse.get_pos())

        count = len(self.cards)
        if count == 1:
            centers = [screen_width / 2.0]
        elif count > 1:
            step = available_width / (count - 1)
            centers = [margin + step * index for index in range(count)]
        else:
            centers = []

        hovered_index: int | None = None
        if app.dragged_object is None:
            for index, card in enumerate(self.cards):
                normalized = 0.0 if count <= 1 else (index / (count - 1)) * 2.0 - 1.0
                offset = arc_height * (1.0 - normalized**2)
                base_rect = self._compute_hand_rect(
                    screen_height,
                    centers[index],
                    card,
                    self.HAND_SCALE,
                    bottom_margin_pixels,
                    offset,
                )
                hover_rect = self._compute_hand_rect(
                    screen_height,
                    centers[index],
                    card,
                    self.HAND_SCALE * self.HOVER_SCALE_MULTIPLIER,
                    bottom_margin_pixels,
                    max(offset, hover_lift),
                )
                if hover_rect.collidepoint(pointer):
                    hovered_index = index
                    break
                if base_rect.collidepoint(pointer):
                    hovered_index = index

        for index, card in enumerate(self.cards):
            if card is app.dragged_object:
                continue
            normalized = 0.0 if count <= 1 else (index / (count - 1)) * 2.0 - 1.0
            offset = arc_height * (1.0 - normalized**2)
            is_hovered = hovered_index == index
            target_scale = self.HAND_SCALE * (
                self.HOVER_SCALE_MULTIPLIER if is_hovered else 1.0
            )
            lift = max(offset, hover_lift) if is_hovered else offset
            target_screen_rect = self._compute_hand_rect(
                screen_height,
                centers[index],
                card,
                target_scale,
                bottom_margin_pixels,
                lift,
            )
            card.hand_screen_rect = target_screen_rect
            target_world = app._screen_to_world(
                pygame.Vector2(target_screen_rect.left, target_screen_rect.top)
            )
            if abs(card.scale - target_scale) > 1e-3:
                card.set_scale(target_scale)
            top_left = (int(round(target_world.x)), int(round(target_world.y)))
            card.rect.topleft = top_left
            card.position = top_left
            card.in_hand = True
            card.hand_hovered = is_hovered

            if is_hovered and (not app.objects or app.objects[-1] is not card):
                if card in app.objects:
                    app.objects.remove(card)
                    app.objects.append(card)

    def _compute_hand_rect(
        self,
        screen_height: int,
        center_x: float,
        card: CardSprite,
        scale: float,
        bottom_margin: float,
        lift: float,
    ) -> pygame.Rect:
        """Return the screen-space rectangle for a hand card with hanging offset."""

        width = card.base_image.get_width() * scale
        height = card.base_image.get_height() * scale
        bottom = screen_height + height * self.HANG_DEPTH_RATIO - bottom_margin - lift
        top = bottom - height
        left = center_x - width / 2.0
        return pygame.Rect(
            int(round(left)),
            int(round(top)),
            int(round(width)),
            int(round(height)),
        )


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
        self.amarres: list[Amarre] = []
        self.hand_zone = HandZone()
        self.dragged_object: GameObject | Amarre | None = None
        self.drag_offset = pygame.Vector2()
        self.drag_start_position: pygame.Vector2 | None = None
        self.drag_scale = 1.30
        self.zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 4.0
        self.camera_center = pygame.Vector2(0, 0)
        self.pan_active = False
        self.pan_last_pos = pygame.Vector2()
        self.last_click_time = 0
        self.last_clicked_object: GameObject | None = None
        self.double_click_threshold_ms = 400
        self.deck_sprite: DeckSprite | None = None
        self.last_escape_press_time = 0
        self.escape_double_press_threshold_ms = 500

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
        self.hand_zone.update(self)

    def handle_events(self) -> None:
        """Consume pygame events."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_escape_press()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pointer_world = self._screen_to_world(pygame.Vector2(event.pos))
                clicked_object = self._find_top_object(pointer_world)
                if self._handle_control_draw(pointer_world, clicked_object):
                    continue
                self._record_pointer_click(clicked_object)
                if not self._begin_drag(pointer_world):
                    self._begin_pan(pygame.Vector2(event.pos))
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                pointer_screen = pygame.Vector2(event.pos)
                pointer_world = self._screen_to_world(pointer_screen)
                self._end_drag(pointer_world, pointer_screen)
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

        self.hand_zone.update(self)

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

        self.deck_sprite = DeckSprite(position=deck_position)
        self.objects = [
            CardSprite("A♠", position=card_position),
            self.deck_sprite,
        ]
        for obj in self.objects:
            self._snap_object_to_grid(obj)
        self.dragged_object = None

    def _find_top_object(self, pointer: pygame.Vector2) -> GameObject | None:
        """Return the top-most object at *pointer* if any."""

        for candidate in reversed(self.objects):
            if candidate.rect.collidepoint(pointer.x, pointer.y):
                return candidate
        return None

    def _record_pointer_click(self, clicked_object: GameObject | None) -> None:
        """Track the most recent pointer click for double-click detection."""

        if clicked_object is not None and clicked_object not in self.objects:
            clicked_object = None
        self.last_clicked_object = clicked_object
        self.last_click_time = pygame.time.get_ticks()

    def _reset_click_tracker(self) -> None:
        """Clear the stored click state."""

        self.last_clicked_object = None
        self.last_click_time = 0

    def _handle_control_draw(
        self, pointer: pygame.Vector2, clicked_object: GameObject | None
    ) -> bool:
        """Draw a card from the deck when control is held during a click."""

        if clicked_object is None:
            return False

        if not isinstance(clicked_object, DeckSprite):
            return False

        if self.deck_sprite is None or clicked_object is not self.deck_sprite:
            return False

        if not (pygame.key.get_mods() & pygame.KMOD_CTRL):
            return False

        new_card = self._spawn_card_from_deck(clicked_object)
        if new_card is None:
            return False

        self.dragged_object = new_card
        self.drag_start_position = pygame.Vector2(new_card.rect.topleft)
        new_card.set_scale(self.drag_scale)
        self.drag_offset = pygame.Vector2(new_card.rect.width / 2, new_card.rect.height / 2)
        self._drag_object(pointer)
        return True

    def _handle_escape_press(self) -> None:
        """Center the camera on the deck when escape is pressed twice."""

        now = pygame.time.get_ticks()
        if (
            self.last_escape_press_time
            and 0 < now - self.last_escape_press_time <= self.escape_double_press_threshold_ms
        ):
            self._center_view_on_deck()
            self.last_escape_press_time = 0
        else:
            self.last_escape_press_time = now

    def _center_view_on_deck(self) -> None:
        """Reposition the camera so the deck is centred on screen."""

        deck = self.deck_sprite
        if deck is not None:
            self.camera_center = pygame.Vector2(deck.rect.center)
        else:
            self.camera_center = pygame.Vector2(0, 0)
        self.pan_active = False

    def _spawn_card_from_deck(self, deck: DeckSprite) -> CardSprite | None:
        """Draw a card from *deck* and spawn it if space is available."""

        if deck is None:
            return None

        position = self._find_free_card_position(deck)
        if position is None:
            return None

        card_label = deck.draw_card()
        if card_label is None:
            self._remove_deck(deck)
            return None

        new_card = CardSprite(card_label, position=position)
        self._snap_object_to_grid(new_card)
        self.objects.append(new_card)

        if deck.is_empty():
            self._remove_deck(deck)

        return new_card

    def _remove_deck(self, deck: DeckSprite) -> None:
        """Remove *deck* from the scene and clear references."""

        if deck in self.objects:
            self.objects.remove(deck)
        if self.deck_sprite is deck:
            self.deck_sprite = None
        if self.last_clicked_object is deck:
            self._reset_click_tracker()

    def _find_free_card_position(
        self, deck: DeckSprite, *, ignore: tuple[GameObject, ...] | list[GameObject] = ()
    ) -> tuple[int, int] | None:
        """Locate a nearby free grid position for a card next to *deck*."""

        cell = self.GRID_CELL_SIZE
        deck_cell, _, _ = self._get_object_grid_cell(deck)
        card_span_x, card_span_y = CardSprite.GRID_SPAN

        block_width = card_span_x * cell
        block_height = card_span_y * cell
        margin_x = max(0.0, (block_width - CardSprite.CARD_SIZE[0]) / 2)
        margin_y = max(0.0, (block_height - CardSprite.CARD_SIZE[1]) / 2)
        card_margin = pygame.Vector2(margin_x, margin_y)

        offsets = [
            (card_span_x, 0),
            (-card_span_x, 0),
            (0, -card_span_y),
            (0, card_span_y),
            (card_span_x, -card_span_y),
            (card_span_x, card_span_y),
            (-card_span_x, -card_span_y),
            (-card_span_x, card_span_y),
        ]

        for dx, dy in offsets:
            candidate_cell = pygame.Vector2(deck_cell.x + dx, deck_cell.y + dy)
            candidate_origin = pygame.Vector2(candidate_cell.x * cell, candidate_cell.y * cell)
            candidate_position = candidate_origin + card_margin
            card_rect = pygame.Rect(
                int(round(candidate_position.x)),
                int(round(candidate_position.y)),
                CardSprite.CARD_SIZE[0],
                CardSprite.CARD_SIZE[1],
            )
            collision = False
            for obj in self.objects:
                if obj is deck:
                    continue
                if obj in ignore:
                    continue
                if card_rect.colliderect(obj.rect):
                    collision = True
                    break
            if not collision:
                return card_rect.topleft

        return None

    def _get_object_grid_cell(
        self, obj: GameObject
    ) -> tuple[pygame.Vector2, pygame.Vector2, tuple[int, int]]:
        """Return the grid cell, margin, and span metadata for *obj*."""

        cell = self.GRID_CELL_SIZE
        span = getattr(obj, "GRID_SPAN", (1, 1))
        span_x, span_y = span
        block_width = span_x * cell
        block_height = span_y * cell
        margin_x = max(0.0, (block_width - obj.rect.width) / 2)
        margin_y = max(0.0, (block_height - obj.rect.height) / 2)
        margin = pygame.Vector2(margin_x, margin_y)
        block_candidate = pygame.Vector2(obj.rect.topleft) - margin
        if cell > 0:
            cell_x = round(block_candidate.x / cell)
            cell_y = round(block_candidate.y / cell)
        else:
            cell_x = cell_y = 0
        return pygame.Vector2(cell_x, cell_y), margin, span

    def _begin_drag(self, pointer: pygame.Vector2) -> bool:
        """Start dragging the top-most object under *pointer* if any."""

        for index in range(len(self.objects) - 1, -1, -1):
            candidate = self.objects[index]
            if candidate.rect.collidepoint(pointer.x, pointer.y):
                if isinstance(candidate, CardSprite):
                    group = candidate.amarre
                    if group is not None and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.dragged_object = group
                        self.drag_start_position = pygame.Vector2(group.rect.topleft)
                        self.drag_offset = pointer - pygame.Vector2(group.rect.topleft)
                        group.bring_to_front(self.objects)
                        group.set_scale(self.drag_scale)
                        self.drag_offset = pointer - pygame.Vector2(group.rect.topleft)
                        self._drag_object(pointer)
                        return True
                    if group is not None and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        removed = group.remove_card(candidate)
                        if removed:
                            self._remove_amarre(group)
                    self.hand_zone.remove_card(self, candidate)
                self.dragged_object = candidate
                self.drag_start_position = pygame.Vector2(candidate.rect.topleft)
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
        obj = self.dragged_object
        obj.capture_shadow_sample()
        new_position = pointer - self.drag_offset
        top_left = (int(new_position.x), int(new_position.y))
        if isinstance(obj, Amarre):
            obj.move_to(top_left)
        else:
            obj.rect.topleft = top_left
            obj.position = top_left

    def _end_drag(
        self, pointer: pygame.Vector2, pointer_screen: pygame.Vector2 | None = None
    ) -> None:
        """Release the currently dragged object, if any."""

        if self.dragged_object is None:
            return
        obj = self.dragged_object
        self._drag_object(pointer)
        if pointer_screen is None:
            pointer_screen = self._world_to_screen(pointer)

        if isinstance(obj, CardSprite):
            if self.hand_zone.handle_drop(self, obj, pointer_screen):
                obj.set_scale(self.hand_zone.HAND_SCALE)
                self.dragged_object = None
                self.drag_start_position = None
                return
            obj.set_scale(1.0)
            self.hand_zone.remove_card(self, obj)
            self._snap_object_to_grid(obj)
            self._handle_card_drop(obj)
            self._evaluate_amarres_after_drop([obj])
        elif isinstance(obj, Amarre):
            obj.set_scale(1.0)
            self._snap_object_to_grid(obj)
            obj.move_to(obj.rect.topleft)
            self._handle_amarre_drop(obj)
        else:
            obj.set_scale(1.0)
            self._snap_object_to_grid(obj)
            if isinstance(obj, DeckSprite):
                self._handle_deck_drop(obj)

        self.dragged_object = None
        self.drag_start_position = None

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

    def _handle_card_drop(self, card: CardSprite) -> None:
        """Ensure dropped cards do not block the deck."""

        deck = self.deck_sprite
        if deck is None or deck not in self.objects:
            return

        if not card.rect.colliderect(deck.rect):
            return

        new_position = self._find_free_card_position(deck, ignore=(card,))
        if new_position is None:
            if self.drag_start_position is not None:
                original = (
                    int(round(self.drag_start_position.x)),
                    int(round(self.drag_start_position.y)),
                )
                card.rect.topleft = original
                card.position = original
                self._snap_object_to_grid(card)
            return

        card.rect.topleft = new_position
        card.position = new_position
        self._snap_object_to_grid(card)

    def _handle_deck_drop(self, deck: DeckSprite) -> None:
        """Return overlapping cards to the deck when it is dropped on them."""

        removed_cards: list[CardSprite] = []
        for obj in list(self.objects):
            if not isinstance(obj, CardSprite):
                continue
            if obj.rect.colliderect(deck.rect):
                deck.shuffle_in_card(obj.label)
                self._detach_card_from_amarre(obj)
                removed_cards.append(obj)
                self.objects.remove(obj)
                self.hand_zone.remove_card(self, obj)
                if self.last_clicked_object is obj:
                    self._reset_click_tracker()

        if removed_cards:
            # Ensure the deck remains tracked even if it was previously removed.
            if self.deck_sprite is None:
                self.deck_sprite = deck

    def _handle_amarre_drop(self, group: Amarre) -> None:
        """Re-evaluate card stacks after an amarre is released."""

        if group.is_empty():
            self._remove_amarre(group)
            return

        anchor = group.cards[0] if group.cards else None
        if anchor is not None:
            before = anchor.rect.topleft
            self._handle_card_drop(anchor)
            if anchor.rect.topleft != before:
                group.move_to(anchor.rect.topleft)
        self._evaluate_amarres_after_drop(group.cards)

    def _evaluate_amarres_after_drop(self, cards: Iterable[CardSprite]) -> None:
        """Update amarre membership for the provided *cards*."""

        for card in list(cards):
            if card not in self.objects or card.in_hand:
                continue
            partner = self._find_card_collision_partner(card)
            if partner is not None:
                self._join_cards_into_amarre(card, partner)

        for card in list(cards):
            group = getattr(card, "amarre", None)
            if group is None:
                continue
            if len(group.cards) < 2:
                self._remove_amarre(group)

    def _join_cards_into_amarre(self, primary: CardSprite, other: CardSprite) -> None:
        """Merge *primary* and *other* into a shared amarre."""

        if primary.in_hand or other.in_hand:
            return

        target_group = other.amarre
        primary_group = primary.amarre

        if target_group is None and primary_group is None:
            new_group = Amarre([other, primary])
            self.amarres.append(new_group)
            target_group = new_group
        elif target_group is None and primary_group is not None:
            primary_group.add_card(other)
            target_group = primary_group
        elif target_group is not None and primary_group is None:
            target_group.add_card(primary)
        elif target_group is not None and primary_group is not None:
            if target_group is primary_group:
                target_group.move_to(target_group.rect.topleft)
                return
            for card in list(primary_group.cards):
                target_group.add_card(card)
            self._remove_amarre(primary_group)

        if target_group is None:
            return

        if target_group not in self.amarres:
            self.amarres.append(target_group)

        anchor = target_group.cards[0].rect.topleft if target_group.cards else primary.rect.topleft
        target_group.move_to(anchor)
        target_group.set_scale(1.0)
        target_group.bring_to_front(self.objects)

    def _find_card_collision_partner(self, card: CardSprite) -> CardSprite | None:
        """Return another card occupying the same space as *card* if any."""

        for candidate in reversed(self.objects):
            if not isinstance(candidate, CardSprite):
                continue
            if candidate is card:
                continue
            if candidate.in_hand:
                continue
            if card.rect.colliderect(candidate.rect):
                return candidate
        return None

    def _detach_card_from_amarre(self, card: CardSprite) -> None:
        """Remove *card* from its amarre if it is part of one."""

        group = getattr(card, "amarre", None)
        if group is None:
            return
        if group.remove_card(card):
            self._remove_amarre(group)

    def _remove_amarre(self, group: Amarre) -> None:
        """Drop *group* from tracking and detach any remaining cards."""

        if group in self.amarres:
            self.amarres.remove(group)
        for member in list(group.cards):
            group.remove_card(member)

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

        if isinstance(obj, CardSprite) and obj.in_hand:
            if obj.hand_screen_rect is not None:
                screen_position = pygame.Vector2(obj.hand_screen_rect.topleft)
            else:
                screen_position = self._world_to_screen(pygame.Vector2(obj.rect.topleft))
            image = obj.image
            draw_rect = image.get_rect()
            draw_rect.topleft = (int(round(screen_position.x)), int(round(screen_position.y)))
            surface.blit(image, draw_rect)
            return

        world_position = pygame.Vector2(obj.rect.topleft)
        screen_position = self._world_to_screen(world_position)
        total_scale = obj.scale * self.zoom
        if abs(total_scale - 1.0) < 1e-3:
            image = obj.image
        else:
            source = getattr(obj, "hi_res_image", obj.base_image)
            source_scale = float(getattr(obj, "hi_res_scale", 1.0))
            width = max(1, int(round(source.get_width() * (total_scale / source_scale))))
            height = max(1, int(round(source.get_height() * (total_scale / source_scale))))
            image = pygame.transform.smoothscale(source, (width, height))
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
