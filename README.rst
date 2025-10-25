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
