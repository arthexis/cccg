CCCG - Collectible Children Card Game
=====================================

This repository contains the very first scaffolding for a collectible card game
prototype powered by `pygame <https://www.pygame.org>`_. The CCCG name leans
into the joke that the project could either be about collecting children or a
collectible game designed for children.

Running the prototype
---------------------

Install the project in editable mode and launch the ``cccg`` console script::

   pip install -e .
   cccg --width 1600 --height 900 --fps 120

The current implementation only opens an empty window with a placeholder
background colour. Future iterations will introduce gameplay systems,
animations and assets.
