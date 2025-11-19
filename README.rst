CCCG - Collectible Children Card Game
=====================================

This repository contains the very first scaffolding for a collectible card game
prototype powered by `pygame <https://www.pygame.org>`_. 

Running the prototype
---------------------

Install the project in editable mode and launch the ``cccg`` console script::

   pip install -e .
   cccg --width 1600 --height 900 --fps 120

Pass ``--fullscreen`` to launch the prototype in full-screen windowed mode, or
``--windowed`` to force the traditional window size regardless of the default
configuration.

The current implementation only opens an empty window with a placeholder
background colour. Future iterations will introduce gameplay systems,
animations and assets.

Love2D edition
--------------

A Lua version of the prototype is available in the ``love2d`` directory. Run
it with a local Love2D install::

   cd love2d
   love .

The Love2D build mirrors the pygame prototype: click the deck to draw cards,
drag cards around the grid (stacking them when they overlap), drag with Ctrl
held to split stacks, drop cards into the bottom hand zone to see the curved
fan layout, and use the mouse wheel to zoom while panning with a click-and-drag
on empty space.
