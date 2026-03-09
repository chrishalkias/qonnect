# -*- coding: utf-8 -*-
# game/play.py
'''
Created Wed 24 Apr 2025
The configuration and run file.
'''

from game import Qonnect

n, tau, p_e, p_s = (5, 10, 0.7, 0.9)

game_config = {
    'grid_size':          n,
    'cell_size':          90,         # cells auto-size the window — no manual tuning needed
    'dot_color':          (0, 220, 255),
    'merge_enabled':      True,
    'window_title':       "Qonnect",
    'dot_lifetime':       tau,
    'title_font_size':    38,
    'dot_creation_prob':  p_e,
    'dot_merge_prob':     p_s,
}

game = Qonnect(game_config)

if __name__ == "__main__":
    game.show_rules_popup()
    game.run()