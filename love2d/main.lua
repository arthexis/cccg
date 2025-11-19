-- Love2D port of the CCCG prototype.
-- Provides a basic card deck, draggable cards, stacking, and a curved hand zone.

local CARD_WIDTH, CARD_HEIGHT = 90, 132
local GRID_CELL_SIZE = 48
local GRID_DASH_LENGTH, GRID_GAP_LENGTH = 10, 6
local HAND_LEFT_RIGHT_MARGIN_RATIO = 0.08
local HAND_BOTTOM_MARGIN_RATIO = 0.0
local HAND_ARC_HEIGHT_RATIO = 0.15
local HAND_HOVER_LIFT_RATIO = 0.20
local HAND_ZONE_HEIGHT_RATIO = 0.25
local HAND_SCALE = 1.5
local HAND_HOVER_SCALE_MULTIPLIER = 1.5
local HAND_HANG_DEPTH_RATIO = 0.40

local objects = {}
local amarres = {}
local handZone = {cards = {}, bottomMargin = HAND_BOTTOM_MARGIN_RATIO, hangDepth = HAND_HANG_DEPTH_RATIO}
local draggedObject = nil
local dragOffset = {x = 0, y = 0}
local dragScale = 1.30
local camera = {scale = 1.0, min = 0.25, max = 4.0, center = {x = 0, y = 0}}
local pan = {active = false, last = {x = 0, y = 0}}
local fonts = {}
local deckSprite = nil

local function splitLabel(label)
  local suit = label:sub(-1)
  if suit == "♠" or suit == "♥" or suit == "♦" or suit == "♣" then
    local value = label:sub(1, #label - 1)
    if value == "" then value = suit end
    return value, suit
  end
  return label, ""
end

local function suitColor(suit)
  if suit == "♥" or suit == "♦" then
    return {200, 16, 46}
  elseif suit == "♠" or suit == "♣" then
    return {20, 20, 20}
  end
  return {24, 24, 24}
end

local function createCard(label, position)
  local card = {
    type = "card",
    label = label,
    x = position[1],
    y = position[2],
    scale = 1.0,
    inHand = false,
    handHovered = false,
    amarre = nil,
    handRect = nil,
    width = CARD_WIDTH,
    height = CARD_HEIGHT,
  }
  return card
end

local function standardDeck()
  local values = {"A","2","3","4","5","6","7","8","9","10","J","Q","K"}
  local suits = {"♠","♥","♦","♣"}
  local cards = {}
  for _, suit in ipairs(suits) do
    for _, value in ipairs(values) do
      table.insert(cards, value .. suit)
    end
  end
  table.insert(cards, "Joker")
  table.insert(cards, "Joker")
  return cards
end

local function createDeck(position, cards)
  local deck = {
    type = "deck",
    cards = cards or standardDeck(),
    x = position[1],
    y = position[2],
    width = CARD_WIDTH,
    height = CARD_HEIGHT,
  }
  return deck
end

local function pushObject(obj)
  table.insert(objects, obj)
end

local function screenToWorld(x, y)
  local w, h = love.graphics.getDimensions()
  local worldX = (x - w / 2) / camera.scale + camera.center.x
  local worldY = (y - h / 2) / camera.scale + camera.center.y
  return worldX, worldY
end

local function worldToScreen(x, y)
  local w, h = love.graphics.getDimensions()
  local screenX = (x - camera.center.x) * camera.scale + w / 2
  local screenY = (y - camera.center.y) * camera.scale + h / 2
  return screenX, screenY
end

local function objectRect(obj)
  return obj.x, obj.y, obj.width * obj.scale, obj.height * obj.scale
end

local function pointInObject(obj, x, y)
  local ox, oy, ow, oh = objectRect(obj)
  return x >= ox and x <= ox + ow and y >= oy and y <= oy + oh
end

local function addAmarre(group)
  table.insert(amarres, group)
end

local function removeAmarre(group)
  for i, g in ipairs(amarres) do
    if g == group then
      table.remove(amarres, i)
      break
    end
  end
end

local function createAmarre(cards)
  local group = {type = "amarre", cards = {}, scale = 1.0, x = 0, y = 0}
  for _, card in ipairs(cards or {}) do
    group.x, group.y = card.x, card.y
    card.amarre = group
    card.inHand = false
    card.handRect = nil
    table.insert(group.cards, card)
  end
  addAmarre(group)
  return group
end

local function updateAmarreAnchor(group)
  if #group.cards == 0 then return end
  local anchor = group.cards[1]
  group.x, group.y = anchor.x, anchor.y
  for _, card in ipairs(group.cards) do
    card.x, card.y = anchor.x, anchor.y
    card.scale = group.scale
  end
end

local function detachCard(card)
  local group = card.amarre
  if not group then return end
  for i, member in ipairs(group.cards) do
    if member == card then
      table.remove(group.cards, i)
      break
    end
  end
  card.amarre = nil
  card.scale = 1.0
  if #group.cards == 0 then
    removeAmarre(group)
  elseif #group.cards == 1 then
    group.cards[1].amarre = nil
    group.cards[1].scale = 1.0
    removeAmarre(group)
  else
    updateAmarreAnchor(group)
  end
end

local function findTopObject(x, y)
  for i = #objects, 1, -1 do
    local candidate = objects[i]
    if pointInObject(candidate, x, y) then
      return candidate
    end
  end
  return nil
end

local function bringToFront(obj)
  for i, other in ipairs(objects) do
    if other == obj then
      table.remove(objects, i)
      break
    end
  end
  table.insert(objects, obj)
end

local function spawnCardFromDeck(deck)
  local cardLabel = deck.cards[#deck.cards]
  if not cardLabel then return nil end
  table.remove(deck.cards, #deck.cards)
  local position = {deck.x + deck.width + 10, deck.y}
  local card = createCard(cardLabel, position)
  pushObject(card)
  return card
end

local function snapToGrid(obj)
  local cell = GRID_CELL_SIZE
  local ox, oy = obj.x, obj.y
  ox = math.floor((ox + cell / 2) / cell) * cell
  oy = math.floor((oy + cell / 2) / cell) * cell
  obj.x, obj.y = ox, oy
end

local function endDrag(pointerX, pointerY)
  if not draggedObject then return nil end
  local obj = draggedObject
  if obj.type == "card" then
    -- Check hand drop
    local w, h = love.graphics.getDimensions()
    local zoneTop = h * (1.0 - HAND_ZONE_HEIGHT_RATIO)
    local screenX, screenY = worldToScreen(pointerX, pointerY)
    if screenY >= zoneTop then
      handZone.cards[#handZone.cards + 1] = obj
      detachCard(obj)
      obj.inHand = true
    else
      obj.inHand = false
    end
  end

  draggedObject = nil
  dragOffset = {x = 0, y = 0}
  if obj.type == "amarre" then
    obj.scale = 1.0
    updateAmarreAnchor(obj)
  else
    obj.scale = obj.scale / dragScale
  end
  snapToGrid(obj)
  return obj
end

local function attemptStack(card)
  for i = #objects, 1, -1 do
    local other = objects[i]
    if other ~= card and other.type == "card" and not other.inHand then
      local ax, ay, aw, ah = objectRect(card)
      local bx, by, bw, bh = objectRect(other)
      if ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by then
        local aGroup, bGroup = card.amarre, other.amarre
        if not aGroup and not bGroup then
          createAmarre({other, card})
        elseif aGroup and not bGroup then
          table.insert(aGroup.cards, other)
          other.amarre = aGroup
        elseif not aGroup and bGroup then
          table.insert(bGroup.cards, card)
          card.amarre = bGroup
        elseif aGroup ~= bGroup then
          for _, member in ipairs(bGroup.cards) do
            table.insert(aGroup.cards, member)
            member.amarre = aGroup
          end
          removeAmarre(bGroup)
        end
        updateAmarreAnchor(card.amarre or other.amarre)
        return
      end
    end
  end
end

local function layoutHand()
  if #handZone.cards == 0 then return end
  local w, h = love.graphics.getDimensions()
  local margin = w * HAND_LEFT_RIGHT_MARGIN_RATIO
  local available = math.max(0, w - 2 * margin)
  local bottomMargin = h * handZone.bottomMargin
  local arcHeight = h * HAND_ARC_HEIGHT_RATIO
  local hoverLift = h * HAND_HOVER_LIFT_RATIO
  local count = #handZone.cards
  local baseScale = HAND_SCALE
  if count > 0 then
    local usable = w - 2 * margin
    baseScale = math.max(0.1, math.min(HAND_SCALE, usable / (CARD_WIDTH * count)))
  end
  local cardWidth = CARD_WIDTH * baseScale
  local centers = {}
  if count == 1 then
    centers[1] = w / 2
  else
    local start = margin + cardWidth / 2
    local span = math.max(0, available - cardWidth)
    local step = count > 1 and span / (count - 1) or 0
    for i = 1, count do
      centers[i] = start + step * (i - 1)
    end
  end

  local pointerX, pointerY = love.mouse.getPosition()
  local hovered = nil
  for i, card in ipairs(handZone.cards) do
    local normalized = count <= 1 and 0 or ((i - 1) / (count - 1)) * 2 - 1
    local offset = arcHeight * (1 - normalized * normalized)
    local targetScale = baseScale
    local top = h - bottomMargin - (CARD_HEIGHT * targetScale) + CARD_HEIGHT * HAND_HANG_DEPTH_RATIO - offset
    local left = centers[i] - (CARD_WIDTH * targetScale) / 2
    if pointerX >= left and pointerX <= left + CARD_WIDTH * targetScale and pointerY >= top and pointerY <= top + CARD_HEIGHT * targetScale then
      hovered = i
      break
    end
  end

  for i, card in ipairs(handZone.cards) do
    local normalized = count <= 1 and 0 or ((i - 1) / (count - 1)) * 2 - 1
    local offset = arcHeight * (1 - normalized * normalized)
    local targetScale = baseScale
    local lift = offset
    if hovered == i then
      targetScale = baseScale * HAND_HOVER_SCALE_MULTIPLIER
      lift = math.max(offset, hoverLift)
      card.handHovered = true
    else
      card.handHovered = false
    end
    local screenX = centers[i] - (CARD_WIDTH * targetScale) / 2
    local screenY = h + CARD_HEIGHT * HAND_HANG_DEPTH_RATIO - (CARD_HEIGHT * targetScale) - lift - bottomMargin
    local worldX, worldY = screenToWorld(screenX, screenY)
    card.x, card.y = worldX, worldY
    card.scale = targetScale
    card.inHand = true
    card.handRect = {x = screenX, y = screenY, w = CARD_WIDTH * targetScale, h = CARD_HEIGHT * targetScale}
  end
end

function love.load()
  love.window.setTitle("CCCG - Love2D Edition")
  fonts.large = love.graphics.newFont(42)
  fonts.medium = love.graphics.newFont(24)
  fonts.small = love.graphics.newFont(18)

  local deckHeight = CARD_HEIGHT
  local gap = 24
  local cardPos = {-CARD_WIDTH - gap / 2, -deckHeight / 2}
  local deckPos = {gap / 2, -deckHeight / 2}

  local card = createCard("A♠", cardPos)
  deckSprite = createDeck(deckPos)
  pushObject(card)
  pushObject(deckSprite)
  snapToGrid(card)
  snapToGrid(deckSprite)
  layoutHand()
end

function love.update(dt)
  if draggedObject then
    local mx, my = love.mouse.getPosition()
    local wx, wy = screenToWorld(mx, my)
    if draggedObject.type == "amarre" then
      draggedObject.x = wx - dragOffset.x
      draggedObject.y = wy - dragOffset.y
      for _, card in ipairs(draggedObject.cards) do
        card.x, card.y = draggedObject.x, draggedObject.y
      end
    else
      draggedObject.x = wx - dragOffset.x
      draggedObject.y = wy - dragOffset.y
    end
  elseif pan.active then
    local mx, my = love.mouse.getPosition()
    local dx = (pan.last.x - mx) / camera.scale
    local dy = (pan.last.y - my) / camera.scale
    camera.center.x = camera.center.x + dx
    camera.center.y = camera.center.y + dy
    pan.last.x, pan.last.y = mx, my
  end
  layoutHand()
end

function love.draw()
  love.graphics.clear(32/255, 48/255, 64/255)
  love.graphics.push()
  local w, h = love.graphics.getDimensions()
  love.graphics.translate(w / 2, h / 2)
  love.graphics.scale(camera.scale)
  love.graphics.translate(-camera.center.x, -camera.center.y)

  -- grid
  local function dashedLine(x1, y1, x2, y2)
    local dx, dy = x2 - x1, y2 - y1
    local len = math.sqrt(dx * dx + dy * dy)
    if len == 0 then return end
    local ux, uy = dx / len, dy / len
    local progress = 0
    while progress < len do
      local dashEnd = math.min(progress + GRID_DASH_LENGTH, len)
      local sx = x1 + ux * progress
      local sy = y1 + uy * progress
      local ex = x1 + ux * dashEnd
      local ey = y1 + uy * dashEnd
      love.graphics.line(sx, sy, ex, ey)
      progress = progress + GRID_DASH_LENGTH + GRID_GAP_LENGTH
    end
  end

  local color = {1, 1, 1, 0.6}
  love.graphics.setColor(color)
  local left = math.floor((camera.center.x - w / 2 / camera.scale) / GRID_CELL_SIZE) * GRID_CELL_SIZE
  local right = math.ceil((camera.center.x + w / 2 / camera.scale) / GRID_CELL_SIZE) * GRID_CELL_SIZE
  local top = math.floor((camera.center.y - h / 2 / camera.scale) / GRID_CELL_SIZE) * GRID_CELL_SIZE
  local bottom = math.ceil((camera.center.y + h / 2 / camera.scale) / GRID_CELL_SIZE) * GRID_CELL_SIZE
  for x = left, right, GRID_CELL_SIZE do
    dashedLine(x, top, x, bottom)
  end
  for y = top, bottom, GRID_CELL_SIZE do
    dashedLine(left, y, right, y)
  end
  love.graphics.setColor(1,1,1,1)

  local function drawCard(card)
    local x, y, w, h = objectRect(card)
    love.graphics.push()
    love.graphics.translate(x, y)
    love.graphics.scale(card.scale)
    local suitLabel, suit = splitLabel(card.label)
    local suitCol = suitColor(suit)
    love.graphics.setColor(246/255, 246/255, 246/255)
    love.graphics.rectangle("fill", 0, 0, CARD_WIDTH, CARD_HEIGHT, 12)
    love.graphics.setColor(24/255, 24/255, 24/255)
    love.graphics.rectangle("line", 0, 0, CARD_WIDTH, CARD_HEIGHT, 12)
    love.graphics.setColor(suitCol[1]/255, suitCol[2]/255, suitCol[3]/255)
    love.graphics.setFont(fonts.medium)
    love.graphics.print(suitLabel, 8, 6)
    love.graphics.setFont(fonts.large)
    local text = suit ~= "" and suit or card.label
    local tw = fonts.large:getWidth(text)
    local th = fonts.large:getHeight()
    love.graphics.print(text, CARD_WIDTH - tw - 10, CARD_HEIGHT - th - 6)
    love.graphics.pop()
  end

  local function drawDeck(deck)
    local x, y = deck.x, deck.y
    love.graphics.push()
    love.graphics.translate(x, y)
    love.graphics.setColor(120/255, 0, 0)
    love.graphics.rectangle("fill", 0, 0, CARD_WIDTH, CARD_HEIGHT, 14)
    love.graphics.setColor(30/255, 0, 0)
    love.graphics.rectangle("line", 0, 0, CARD_WIDTH, CARD_HEIGHT, 14)
    love.graphics.setFont(fonts.medium)
    love.graphics.print("Deck (" .. tostring(#deck.cards) .. ")", 10, CARD_HEIGHT/2 - fonts.medium:getHeight()/2)
    love.graphics.pop()
  end

  for _, obj in ipairs(objects) do
    if obj.type == "card" then
      drawCard(obj)
    elseif obj.type == "deck" then
      drawDeck(obj)
    end
  end

  love.graphics.pop()
end

function love.mousepressed(x, y, button)
  if button ~= 1 then return end
  local wx, wy = screenToWorld(x, y)
  local clicked = findTopObject(wx, wy)
  if clicked and clicked.type == "deck" and clicked == deckSprite then
    local newCard = spawnCardFromDeck(deckSprite)
    if newCard then
      draggedObject = newCard
      dragOffset = {x = newCard.width * newCard.scale / 2, y = newCard.height * newCard.scale / 2}
      newCard.scale = newCard.scale * dragScale
      bringToFront(newCard)
      return
    end
  end

  if clicked then
    if clicked.type == "card" then
      local group = clicked.amarre
      if group and love.keyboard.isDown("lctrl", "rctrl") then
        detachCard(clicked)
      elseif group then
        draggedObject = group
        dragOffset = {x = wx - group.x, y = wy - group.y}
        group.scale = dragScale
        updateAmarreAnchor(group)
        bringToFront(clicked)
        return
      end
    end
    draggedObject = clicked
    dragOffset = {x = wx - clicked.x, y = wy - clicked.y}
    clicked.scale = clicked.scale * dragScale
    bringToFront(clicked)
  else
    pan.active = true
    pan.last.x, pan.last.y = x, y
  end
end

function love.mousereleased(x, y, button)
  if button ~= 1 then return end
  local wx, wy = screenToWorld(x, y)
  local released = nil
  if draggedObject then
    released = endDrag(wx, wy)
  end
  pan.active = false
  if released and released.type == "card" then
    attemptStack(released)
  end
end

function love.wheelmoved(dx, dy)
  local oldScale = camera.scale
  camera.scale = math.max(camera.min, math.min(camera.max, camera.scale + dy * 0.1))
  local mx, my = love.mouse.getPosition()
  local wx, wy = screenToWorld(mx, my)
  camera.center.x = wx - (mx - love.graphics.getWidth()/2) / camera.scale
  camera.center.y = wy - (my - love.graphics.getHeight()/2) / camera.scale
end

function love.keypressed(key)
  if key == "escape" then
    camera.center.x, camera.center.y = 0, 0
    camera.scale = 1.0
  end
end
