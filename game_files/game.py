# -*- coding: utf-8 -*-
# game/game.py

'''
                 ██████   ██████  ███    ██ ███    ██ ███████  ██████ ████████ 
                ██    ██ ██    ██ ████   ██ ████   ██ ██      ██         ██    
                ██    ██ ██    ██ ██ ██  ██ ██ ██  ██ █████   ██         ██    
                ██ ▄▄ ██ ██    ██ ██  ██ ██ ██  ██ ██ ██      ██         ██    
                 ██████   ██████  ██   ████ ██   ████ ███████  ██████    ██    
                     ▀▀                                                                                                        
                               Created Wed 15 Apr 2025
                        A simple quantum network based board game.
'''

import pygame
import random
import sys
import math
from typing import List, Tuple, Optional, Dict


# ── Palette ────────────────────────────────────────────────────────────────────
C_BG           = ( 8,  12,  24)
C_CELL_BASE    = (14,  21,  42)
C_CELL_BORDER  = (28,  44,  88)
C_DIAG_CELL    = ( 5,   8,  16)
C_VALID_CELL   = (18,  32,  72)
C_VALID_BORDER = (40,  80, 160)
C_DOT          = (  0, 220, 255)
C_DOT_GLOW     = (  0, 100, 180)
C_TARGET       = ( 20, 255, 120)
C_TARGET_GLOW  = (  0, 120,  60)
C_SELECT       = (255, 200,   0)
C_DIAG_LINE    = (200,  30,  60)
C_PANEL_BG     = ( 10,  16,  34)
C_PANEL_BORDER = ( 28,  50, 110)
C_TEXT_DIM     = (100, 130, 180)
C_TEXT         = (170, 200, 240)
C_TEXT_BRIGHT  = (220, 240, 255)
C_TEXT_CYAN    = (  0, 220, 255)
C_WIN_TEXT     = ( 20, 255, 120)
C_LOSE_TEXT    = (220,  60,  60)
C_FAIL_X       = (255,  50,  50)

LEFT_PANEL_W = 124
SIDE_PANEL_W = 215


class Qonnect:
    def __init__(self, config: dict):
        """
        Main game class. Implements the quantum repeater board game Qonnect.

        Attributes:
            config          (dict)    – configuration dictionary
            action_log      (list)    – all performed actions
            screen          (Surface) – pygame display
            grid            (list)    – NxN boolean board state
            dot_timers      (dict)    – remaining lifetime per dot
            selected_cells  (list)    – up to two cells picked for swapping
            _flash_cells    (dict)    – (row,col)->expiry_ms for fail-X overlay
            game_over       (bool)    – whether game has ended
            win             (bool)    – whether player won
            action_count    (int)     – total action counter (drives decay)
        """

        self.config = {
            'grid_size':           5,
            'cell_size':           80,
            'padding':             2,
            'bg_color':            C_BG,
            'grid_color':          C_CELL_BORDER,
            'dot_color':           C_DOT,
            'target_position':     (0, 0),
            'target_color':        C_TARGET,
            'merge_enabled':       True,
            'window_title':        "Qonnect",
            'black_cells':         [],
            'grey_cells':          [],
            'diagonal_color':      C_DIAG_LINE,
            'text_color':          C_TEXT,
            'text_padding':        28,
            'dot_lifetime':        5,
            'title_font_size':     40,
            'selection_color':     C_SELECT,
            'selection_thickness': 3,
            'dot_creation_prob':   0.8,
            'dot_merge_prob':      0.8,
        }

        self.action_log: List[str] = []
        self.config.update(config)
        self.config['target_position'] = (0, self.config['grid_size'] - 1)

        pygame.init()

        # ── Geometry ───────────────────────────────────────────────────────────
        N   = self.config['grid_size']
        CS  = self.config['cell_size']
        PAD = self.config['padding']
        TP  = self.config['text_padding']
        TH  = self.config['title_font_size'] + 10

        self._cell_stride = CS + PAD
        self._grid_x0     = LEFT_PANEL_W + TP
        self._grid_y0     = TH + TP

        grid_px_w = N * self._cell_stride + PAD
        grid_px_h = N * self._cell_stride + PAD

        win_w = LEFT_PANEL_W + TP + grid_px_w + SIDE_PANEL_W
        win_h = TH + TP + grid_px_h + 4

        self.screen = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption(self.config['window_title'])

        self.initialize_special_cells()

        # ── State ──────────────────────────────────────────────────────────────
        self.grid:           List[List[bool]]         = [[False] * N for _ in range(N)]
        self.dot_timers:     Dict[Tuple[int,int],int] = {}
        self.selected_cells: List[Tuple[int,int]]     = []
        self._flash_cells:   Dict[Tuple[int,int],int] = {}
        # pending deferred swap: (pos1, pos2, execute_at_ms)
        self._pending_swap:  Optional[Tuple]           = None
        self.game_over    = False
        self.win          = False
        self.action_count = 0

        # ── Fonts ──────────────────────────────────────────────────────────────
        self._font_title = pygame.font.SysFont(
            'consolas,couriernew,monospace', self.config['title_font_size'], bold=True)
        self._font_ui    = pygame.font.SysFont('consolas,couriernew,monospace', 16)
        self._font_small = pygame.font.SysFont('consolas,couriernew,monospace', 13)
        # NOT bold – bold monospace at large size smears into illegible blobs
        self._font_big   = pygame.font.SysFont('consolas,couriernew,monospace', 34)

    # ══════════════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_glow_circle(self, surface, color, center, radius,
                          layers=5, max_alpha=160):
        for i in range(layers, 0, -1):
            r     = radius + i * 4
            alpha = int(max_alpha * (1 - i / layers) * 0.5)
            s     = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (r, r), r)
            surface.blit(s, (center[0] - r, center[1] - r))

    def _cell_rect(self, row: int, col: int) -> pygame.Rect:
        return pygame.Rect(
            self._grid_x0 + col * self._cell_stride,
            self._grid_y0 + row * self._cell_stride,
            self.config['cell_size'],
            self.config['cell_size'],
        )

    def _wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines, current = [], []
        for w in words:
            test = ' '.join(current + [w])
            if font.size(test)[0] <= max_width:
                current.append(w)
            else:
                lines.append(' '.join(current))
                current = [w]
        if current:
            lines.append(' '.join(current))
        return lines

    def _add_flash(self, row: int, col: int, duration_ms: int = 700):
        """Schedule a red-X flash overlay on a grid cell for duration_ms ms."""
        self._flash_cells[(row, col)] = pygame.time.get_ticks() + duration_ms

    def _wave_line_points(self, p0, p1, amplitude, freq, phase_offset=0, steps=60):
        """
        Generate polyline points for an animated wave along the straight path p0→p1.
        The wave oscillates perpendicular to the path direction.
        amplitude   – max pixel deviation from centre line
        freq        – wave cycles per pixel of path length
        phase_offset– time-driven phase so the wave appears to travel
        """
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        length = math.hypot(dx, dy) or 1.0
        # unit vectors: along path and perpendicular
        ux, uy   = dx / length, dy / length
        px_, py_ = -uy, ux          # perpendicular (rotated 90°)

        pts = []
        for k in range(steps + 1):
            t    = k / steps
            # position along the straight line
            lx   = p0[0] + t * dx
            ly   = p0[1] + t * dy
            # sinusoidal displacement perpendicular to path
            wave = amplitude * math.sin(2 * math.pi * freq * t * length + phase_offset)
            pts.append((lx + px_ * wave, ly + py_ * wave))
        return pts

    def _wave_arc_points(self, p0, p1, ctrl, amplitude, freq, phase_offset=0, steps=60):
        """
        Generate animated wave points along a quadratic Bézier arc.
        Wave oscillates perpendicular to the instantaneous tangent.
        """
        pts = []
        for k in range(steps + 1):
            t    = k / steps
            mt   = 1 - t
            # Bézier position
            bx   = mt*mt*p0[0] + 2*mt*t*ctrl[0] + t*t*p1[0]
            by   = mt*mt*p0[1] + 2*mt*t*ctrl[1] + t*t*p1[1]
            # Bézier tangent (derivative)
            tx_  = 2*(mt*(ctrl[0]-p0[0]) + t*(p1[0]-ctrl[0]))
            ty_  = 2*(mt*(ctrl[1]-p0[1]) + t*(p1[1]-ctrl[1]))
            tlen = math.hypot(tx_, ty_) or 1.0
            # perpendicular to tangent
            nx_, ny_ = -ty_/tlen, tx_/tlen
            wave = amplitude * math.sin(2 * math.pi * freq * t + phase_offset)
            pts.append((bx + nx_ * wave, by + ny_ * wave))
        return pts

    def _bezier_points(self, p0, p1, ctrl, steps=40):
        """Quadratic Bézier from p0 to p1 via ctrl point."""
        pts = []
        for k in range(steps + 1):
            t  = k / steps
            mt = 1 - t
            x  = mt*mt*p0[0] + 2*mt*t*ctrl[0] + t*t*p1[0]
            y  = mt*mt*p0[1] + 2*mt*t*ctrl[1] + t*t*p1[1]
            pts.append((x, y))
        return pts

    # ══════════════════════════════════════════════════════════════════════════
    # Rules popup
    # ══════════════════════════════════════════════════════════════════════════

    def show_rules_popup(self):
        rules_lines = [
            ("QONNECT  —  RULES", True),
            ("", False),
            ("Goal:", True),
            ("  Achieve end-to-end entanglement (green cell).", False),
            ("", False),
            ("Entangle  [click grey cell]:", True),
            ("  Dot placed at (i,j) and mirror (j,i). Prob = p_e.", False),
            ("  Red X = entanglement generation failed.", False),
            ("", False),
            ("Swap  [click two dots]:", True),
            ("  Merges (i,j)+(j,k) -> (i,k). Prob = p_s.", False),
            ("  Red X on both cells = swap failed.", False),
            ("", False),
            ("Decay:", True),
            ("  Every action ages all dots. Fading = low lifetime.", False),
            ("", False),
            ("Chain panel (left):", True),
            ("  Shows the physical repeater chain. Straight lines", False),
            ("  = adjacent links. Arcs = long-range links.", False),
            ("", False),
            ("Reset:  press  R", True),
            ("", False),
            ("                                           — Chris", False),
        ]

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 660, 520
        px = (self.screen.get_width()  - pw) // 2
        py = (self.screen.get_height() - ph) // 2

        pygame.draw.rect(self.screen, C_PANEL_BG,     (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(self.screen, C_PANEL_BORDER,  (px, py, pw, ph), 1, border_radius=8)

        font_h = pygame.font.SysFont('consolas,couriernew,monospace', 17, bold=True)
        font_r = pygame.font.SysFont('consolas,couriernew,monospace', 15)

        y = py + 22
        for line, heading in rules_lines:
            if not line:
                y += 7
                continue
            f   = font_h if heading else font_r
            col = C_TEXT_CYAN if heading else C_TEXT
            for sub in (self._wrap_text(line, f, pw - 40) if len(line) > 70 else [line]):
                surf = f.render(sub, True, col)
                self.screen.blit(surf, (px + 20, y))
                y += 22

        btn = pygame.Rect(px + pw - 120, py + ph - 50, 96, 32)
        pygame.draw.rect(self.screen, (20, 180, 80), btn, border_radius=5)
        pygame.draw.rect(self.screen, C_TARGET, btn, 1, border_radius=5)
        bt = font_h.render("PLAY", True, (8, 12, 24))
        self.screen.blit(bt, bt.get_rect(center=btn.center))
        pygame.display.flip()

        waiting = True
        while waiting:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif ev.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(ev.pos):
                    waiting = False

    # ══════════════════════════════════════════════════════════════════════════
    # Initialisation
    # ══════════════════════════════════════════════════════════════════════════

    def initialize_special_cells(self):
        N = self.config['grid_size']
        self.config['black_cells'] = [(i, i) for i in range(N)]
        grey = set()
        for i in range(N):
            if i + 1 < N: grey.add((i, i + 1))
            if i - 1 >= 0: grey.add((i, i - 1))
        black = set(self.config['black_cells'])
        self.config['grey_cells'] = [c for c in grey if c not in black]

    # ══════════════════════════════════════════════════════════════════════════
    # Coordinate mapping
    # ══════════════════════════════════════════════════════════════════════════

    def pos_to_grid(self, pos: Tuple[int,int]) -> Optional[Tuple[int,int]]:
        x, y   = pos
        N      = self.config['grid_size']
        CS     = self.config['cell_size']
        stride = self._cell_stride

        if (x < self._grid_x0 or y < self._grid_y0 or
                x >= self._grid_x0 + N * stride or
                y >= self._grid_y0 + N * stride):
            return None

        col = (x - self._grid_x0) // stride
        row = (y - self._grid_y0) // stride

        if (x - self._grid_x0) % stride >= CS: return None
        if (y - self._grid_y0) % stride >= CS: return None

        return (row, col)

    # ══════════════════════════════════════════════════════════════════════════
    # Left panel: physical chain visualisation
    # ══════════════════════════════════════════════════════════════════════════

    def draw_left_panel(self):
        N      = self.config['grid_size']
        CS     = self.config['cell_size']
        stride = self._cell_stride
        win_h  = self.screen.get_height()
        pw     = LEFT_PANEL_W
        now_s  = pygame.time.get_ticks() / 1000.0   # seconds for wave animation

        # Background + right border
        pygame.draw.rect(self.screen, C_PANEL_BG, (0, 0, pw, win_h))
        pygame.draw.line(self.screen, C_PANEL_BORDER, (pw - 1, 0), (pw - 1, win_h), 1)

        # Section header
        hdr = self._font_ui.render("SYSTEM", True, C_TEXT_CYAN)
        self.screen.blit(hdr, hdr.get_rect(center=(pw // 2, 18)))
        pygame.draw.line(self.screen, C_PANEL_BORDER, (10, 32), (pw - 10, 32), 1)

        # Node geometry: right side of panel, y aligned to grid rows
        node_x  = pw - 28
        node_r  = max(7, CS // 10)
        node_ys = [self._grid_y0 + i * stride + CS // 2 for i in range(N)]

        # Collect canonical connections (smaller index first)
        connections = [
            (i, j)
            for i in range(N)
            for j in range(i + 1, N)
            if self.grid[i][j]
        ]

        # ── Draw connections (animated waves) ────────────────────────────────
        conn_surf = pygame.Surface((pw, win_h), pygame.SRCALPHA)

        for idx, (i, j) in enumerate(connections):
            is_target_link = (i == 0 and j == N - 1)
            lt    = self.dot_timers.get((i, j), self.config['dot_lifetime'])
            frac  = max(0.0, lt / max(1, self.config['dot_lifetime']))
            alpha = int(220 * frac)
            span  = j - i
            base  = C_TARGET if is_target_link else C_DOT
            lw    = 3 if frac > 0.5 else 2

            y0 = node_ys[i]
            y1 = node_ys[j]

            # Phase travels along the wire; each link has a unique offset
            phase = now_s * 4.0 - idx * 0.9
            amp   = 3.5 * frac

            if span == 1:
                # Wave along the vertical segment (displaces in x)
                pts = self._wave_line_points(
                    (node_x, y0), (node_x, y1),
                    amplitude=amp, freq=0.022, phase_offset=phase, steps=50)
                if len(pts) >= 2:
                    pygame.draw.lines(conn_surf, (*base, int(alpha * 0.22)),
                                      False, pts, lw + 5)
                    pygame.draw.lines(conn_surf, (*base, alpha), False, pts, lw)
            else:
                # Wave along a Bézier arc curving to the left
                max_reach = node_x - 10
                reach     = int(max_reach * (span - 1) / max(1, N - 2))
                reach     = min(max(12, reach), max_reach)
                ctrl      = (node_x - reach, (y0 + y1) // 2)
                pts = self._wave_arc_points(
                    (node_x, y0), (node_x, y1), ctrl,
                    amplitude=amp * 1.4, freq=1.5,
                    phase_offset=phase, steps=60)
                if len(pts) >= 2:
                    pygame.draw.lines(conn_surf, (*base, int(alpha * 0.22)),
                                      False, pts, lw + 5)
                    pygame.draw.lines(conn_surf, (*base, alpha), False, pts, lw)

        self.screen.blit(conn_surf, (0, 0))

        # ── Draw nodes (vertical) ─────────────────────────────────────────────
        for i in range(N):
            y_pos        = node_ys[i]
            is_endpoint  = (i == 0 or i == N - 1)
            is_connected = any(
                self.grid[i][j] or self.grid[j][i]
                for j in range(N) if j != i
            )

            # Win pulse behind endpoint nodes
            if self.game_over and self.win and is_endpoint:
                pulse = int(abs(math.sin(now_s * 3.0)) * 150)
                gp = pygame.Surface((node_r * 8, node_r * 8), pygame.SRCALPHA)
                pygame.draw.circle(gp, (*C_TARGET, pulse),
                                   (node_r * 4, node_r * 4), node_r * 4)
                self.screen.blit(gp, (node_x - node_r * 4, y_pos - node_r * 4))

            if is_connected or is_endpoint:
                glow_c  = C_TARGET_GLOW if is_endpoint else C_DOT_GLOW
                g_alpha = 80 if is_endpoint else 50
                gs = pygame.Surface((node_r * 6, node_r * 6), pygame.SRCALPHA)
                pygame.draw.circle(gs, (*glow_c, g_alpha),
                                   (node_r * 3, node_r * 3), node_r * 3)
                self.screen.blit(gs, (node_x - node_r * 3, y_pos - node_r * 3))

            fill_c   = (15, 38, 28) if is_endpoint else C_CELL_BASE
            border_c = C_TARGET     if is_endpoint else C_DOT

            pygame.draw.circle(self.screen, fill_c,   (node_x, y_pos), node_r)
            pygame.draw.circle(self.screen, border_c, (node_x, y_pos), node_r, 2)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (node_x - node_r // 3, y_pos - node_r // 3),
                               max(1, node_r // 4))

            label_col = C_TARGET if is_endpoint else C_TEXT_DIM
            lbl = self._font_small.render(f"R{i+1}", True, label_col)
            self.screen.blit(lbl, (node_x - node_r - 4 - lbl.get_width(),
                                   y_pos - lbl.get_height() // 2))

    

    # ══════════════════════════════════════════════════════════════════════════
    # Main grid drawing
    # ══════════════════════════════════════════════════════════════════════════

    def draw_grid(self):
        N      = self.config['grid_size']
        CS     = self.config['cell_size']
        stride = self._cell_stride

        self.screen.fill(C_BG)

        # Title
        th = self.config['title_font_size'] + 10
        tx = self._grid_x0 + (N * stride) // 2
        ty = (th - 10) // 2
        for dx in (-1, 1):
            for dy in (-1, 1):
                sh = self._font_title.render("QONNECT", True, (0, 60, 120))
                self.screen.blit(sh, sh.get_rect(center=(tx + dx*2, ty + dy*2)))
        ts = self._font_title.render("QONNECT", True, C_TEXT_CYAN)
        self.screen.blit(ts, ts.get_rect(center=(tx, ty)))

        # Row / column labels
        TP = self.config['text_padding']
        for i in range(N):
            lbl = self._font_small.render(str(i + 1), True, C_TEXT_DIM)
            self.screen.blit(lbl, lbl.get_rect(
                center=(self._grid_x0 + i * stride + CS // 2, self._grid_y0 - TP // 2)))
            self.screen.blit(lbl, lbl.get_rect(
                center=(self._grid_x0 - TP // 2, self._grid_y0 + i * stride + CS // 2)))

        # Cells
        black_set  = set(self.config['black_cells'])
        grey_set   = set(self.config['grey_cells'])
        target_row, target_col = self.config['target_position']

        for row in range(N):
            for col in range(N):
                rect      = self._cell_rect(row, col)
                is_target = (
                    (row == target_row and col == target_col) or
                    (row == target_col and col == target_row)
                )
                if (row, col) in black_set:
                    pygame.draw.rect(self.screen, C_DIAG_CELL, rect)
                    for k in range(0, CS, 8):
                        pygame.draw.line(self.screen, (15, 22, 45),
                                         (rect.left+k, rect.top), (rect.left, rect.top+k), 1)
                        pygame.draw.line(self.screen, (15, 22, 45),
                                         (rect.right-k, rect.bottom), (rect.right, rect.bottom-k), 1)
                elif is_target:
                    pygame.draw.rect(self.screen, (12, 48, 32), rect)
                    pygame.draw.rect(self.screen, C_TARGET, rect, 2)
                    sz = 6
                    for cr, cc in [(rect.left, rect.top), (rect.right-sz, rect.top),
                                   (rect.left, rect.bottom-sz), (rect.right-sz, rect.bottom-sz)]:
                        pygame.draw.rect(self.screen, C_TARGET, (cr, cc, sz, sz))
                    # Win pulse overlay on target cells
                    if self.game_over and self.win:
                        pulse_a = int(abs(math.sin(pygame.time.get_ticks() / 280.0)) * 110)
                        ps = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                        pygame.draw.rect(ps, (*C_TARGET, pulse_a), ps.get_rect())
                        self.screen.blit(ps, rect.topleft)
                elif (row, col) in grey_set:
                    pygame.draw.rect(self.screen, C_VALID_CELL, rect)
                    pygame.draw.rect(self.screen, C_VALID_BORDER, rect, 1)
                else:
                    pygame.draw.rect(self.screen, C_CELL_BASE, rect)
                    pygame.draw.rect(self.screen, C_CELL_BORDER, rect, 1)

        # Diagonal marker
        pygame.draw.line(self.screen, (*C_DIAG_LINE, 100),
            (self._grid_x0, self._grid_y0),
            (self._grid_x0 + N * stride, self._grid_y0 + N * stride), 2)

        # Dots
        dot_radius = max(6, CS // 5)
        for row in range(N):
            for col in range(N):
                if (row, col) in black_set or not self.grid[row][col]:
                    continue
                cx = self._grid_x0 + col * stride + CS // 2
                cy = self._grid_y0 + row * stride + CS // 2

                remaining = self.dot_timers.get((row, col), self.config['dot_lifetime'])
                frac      = max(0.0, remaining / max(1, self.config['dot_lifetime']))
                alpha     = int(255 * frac)
                is_t      = ((row == target_row and col == target_col) or
                             (row == target_col and col == target_row))
                dot_c     = C_TARGET if is_t else C_DOT
                glow_c    = C_TARGET_GLOW if is_t else C_DOT_GLOW

                self._draw_glow_circle(self.screen, glow_c, (cx, cy),
                                       dot_radius, layers=max(2, int(5*frac)),
                                       max_alpha=int(140*frac))
                ds = pygame.Surface((dot_radius*2+2, dot_radius*2+2), pygame.SRCALPHA)
                pygame.draw.circle(ds, (*dot_c, alpha),
                                   (dot_radius+1, dot_radius+1), dot_radius)
                pygame.draw.circle(ds, (255, 255, 255, int(alpha * 0.6)),
                                   (dot_radius+1 - dot_radius//4,
                                    dot_radius+1 - dot_radius//4),
                                   max(2, dot_radius // 3))
                self.screen.blit(ds, (cx - dot_radius - 1, cy - dot_radius - 1))

        # Selection highlights
        for (row, col) in self.selected_cells:
            rect = self._cell_rect(row, col)
            for shrink in (6, 4, 2, 0):
                r = rect.inflate(-shrink, -shrink)
                s = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
                pygame.draw.rect(s, (*C_SELECT, 60 if shrink else 220),
                                 s.get_rect(),
                                 self.config['selection_thickness'] - shrink // 2)
                self.screen.blit(s, r.topleft)
            sz = 7
            for cr, cc in [(rect.left, rect.top), (rect.right-sz, rect.top),
                           (rect.left, rect.bottom-sz), (rect.right-sz, rect.bottom-sz)]:
                pygame.draw.rect(self.screen, C_SELECT, (cr, cc, sz, sz))

        # Merge beam: animated line between the two pending-swap cells
        if self._pending_swap is not None:
            pos1, pos2, fire_at = self._pending_swap
            now_ms   = pygame.time.get_ticks()
            elapsed  = now_ms - (fire_at - 300)          # 0 → 300 ms
            progress = max(0.0, min(1.0, elapsed / 300)) # 0.0 → 1.0

            r1, c1 = pos1
            r2, c2 = pos2
            cx1 = self._grid_x0 + c1 * stride + CS // 2
            cy1 = self._grid_y0 + r1 * stride + CS // 2
            cx2 = self._grid_x0 + c2 * stride + CS // 2
            cy2 = self._grid_y0 + r2 * stride + CS // 2

            # Strobe flicker: fast sin wave that accelerates toward merge
            flicker_freq = 8.0 + progress * 16.0         # speeds up as merge nears
            flicker = abs(math.sin(now_ms / 1000.0 * flicker_freq * math.pi))

            # Core beam colour shifts gold → white as progress → 1
            r_c = int(C_SELECT[0] + (255 - C_SELECT[0]) * progress)
            g_c = int(C_SELECT[1] + (255 - C_SELECT[1]) * progress)
            b_c = int(C_SELECT[2] + (255 - C_SELECT[2]) * progress)
            beam_color = (r_c, g_c, b_c)

            alpha_core = int(flicker * 230)
            alpha_glow = int(flicker * 70)

            beam_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

            # Outer glow passes (wide, very transparent)
            for gw, ga_scale in [(14, 0.25), (8, 0.45), (4, 0.65)]:
                pygame.draw.line(beam_surf,
                                 (*beam_color, int(alpha_glow * ga_scale)),
                                 (cx1, cy1), (cx2, cy2), gw)

            # Core beam
            pygame.draw.line(beam_surf,
                             (*beam_color, alpha_core),
                             (cx1, cy1), (cx2, cy2), 2)

            # Travelling particle: a small bright circle that slides c1→c2
            px = int(cx1 + (cx2 - cx1) * progress)
            py = int(cy1 + (cy2 - cy1) * progress)
            particle_r = max(3, CS // 14)
            pygame.draw.circle(beam_surf,
                               (255, 255, 255, int(flicker * 220)),
                               (px, py), particle_r)
            pygame.draw.circle(beam_surf,
                               (*beam_color, int(flicker * 140)),
                               (px, py), particle_r + 4)

            self.screen.blit(beam_surf, (0, 0))

        # Failure flash: red X
        now = pygame.time.get_ticks()
        for k in [k for k, v in self._flash_cells.items() if v <= now]:
            del self._flash_cells[k]

        for (row, col), expiry in list(self._flash_cells.items()):
            frac  = max(0.0, (expiry - now) / 700.0)
            alpha = int(230 * frac)
            rect  = self._cell_rect(row, col)

            # Tinted background
            bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(bg, (180, 20, 20, int(55 * frac)), bg.get_rect())
            self.screen.blit(bg, rect.topleft)

            # X strokes with glow
            m  = max(8, rect.width // 5)
            xs = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            lw = max(2, rect.width // 12)
            for gw, ga in [(lw + 6, 0.20), (lw + 3, 0.35), (lw, 1.0)]:
                pygame.draw.line(xs, (*C_FAIL_X, int(alpha * ga)),
                                 (m, m), (rect.width-m, rect.height-m), gw)
                pygame.draw.line(xs, (*C_FAIL_X, int(alpha * ga)),
                                 (rect.width-m, m), (m, rect.height-m), gw)
            self.screen.blit(xs, rect.topleft)

        # Game-over overlay
        if self.game_over:
            ov = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 110))
            self.screen.blit(ov, (0, 0))

            msg   = "END-TO-END LINKED!" if self.win else "DECOHERENCE  —  GAME OVER"
            color = C_WIN_TEXT if self.win else C_LOSE_TEXT
            sub   = "press  R  to play again"

            ms = self._font_big.render(msg, True, color)
            ss = self._font_ui.render(sub, True, C_TEXT_DIM)

            # Centre over the grid area only (excludes panels)
            gcx = (self._grid_x0 + self._grid_x0 + N * stride) // 2
            gcy = self.screen.get_height() // 2

            # Shadow
            for dx in range(-2, 3):
                for dy in range(-1, 2):
                    sh = self._font_big.render(msg, True, (0, 0, 0))
                    self.screen.blit(sh, sh.get_rect(center=(gcx+dx, gcy+dy+2)))
            self.screen.blit(ms, ms.get_rect(center=(gcx, gcy)))
            self.screen.blit(ss, ss.get_rect(center=(gcx, gcy + 46)))

        # Sub-panels drawn last so they sit on top of the background fill
        self.draw_left_panel()
        self.draw_side_panel()

        pygame.display.flip()

    # ══════════════════════════════════════════════════════════════════════════
    # Right info panel
    # ══════════════════════════════════════════════════════════════════════════

    def draw_side_panel(self):
        N       = self.config['grid_size']
        stride  = self._cell_stride
        panel_x = self._grid_x0 + N * stride + self.config['padding'] + 4
        panel_w = SIDE_PANEL_W - 8
        win_h   = self.screen.get_height()

        pygame.draw.rect(self.screen, C_PANEL_BG, (panel_x, 0, panel_w, win_h))
        pygame.draw.line(self.screen, C_PANEL_BORDER, (panel_x, 0), (panel_x, win_h), 1)

        def lbl(text, y, color=C_TEXT_DIM, font=None):
            f = font or self._font_small
            s = f.render(text, True, color)
            self.screen.blit(s, (panel_x + 10, y))
            return y + s.get_height() + 4

        def section(title, y):
            s = self._font_ui.render(title, True, C_TEXT_CYAN)
            self.screen.blit(s, (panel_x + 10, y))
            y += s.get_height() + 2
            pygame.draw.line(self.screen, C_PANEL_BORDER,
                             (panel_x + 10, y), (panel_x + panel_w - 10, y), 1)
            return y + 6

        y = 14
        y = section("PARAMETERS", y)
        y = lbl(f"grid      : {N}x{N}",                                  y, C_TEXT)
        y = lbl(f"p_create  : {self.config['dot_creation_prob']:.2f}",   y, C_TEXT)
        y = lbl(f"p_swap    : {self.config['dot_merge_prob']:.2f}",      y, C_TEXT)
        y = lbl(f"lifetime  : {self.config['dot_lifetime']}",            y, C_TEXT)
        y = lbl(f"actions   : {self.action_count}", y, C_TEXT_BRIGHT, self._font_ui)
        y += 12

        y = section("LEGEND", y)
        for swatch, text in [
            (C_VALID_CELL, "valid placement"),
            (C_TARGET,     "target cell"),
            (C_DOT,        "entangled link"),
            (C_SELECT,     "selected"),
            (C_FAIL_X,     "operation failed"),
        ]:
            sw = pygame.Rect(panel_x + 10, y + 2, 10, 10)
            pygame.draw.rect(self.screen, swatch, sw)
            pygame.draw.rect(self.screen, (*swatch, 180), sw, 1)
            s = self._font_small.render(text, True, C_TEXT_DIM)
            self.screen.blit(s, (panel_x + 26, y))
            y += 17
        y += 8

        y = section("ACTION LOG", y)
        for action in self.action_log[-(win_h // 20):]:
            c = C_TARGET if action.startswith("ES ") else (
                C_LOSE_TEXT if "FAIL" in action else C_TEXT)
            y = lbl(action, y, c)

    # ══════════════════════════════════════════════════════════════════════════
    # Game logic
    # ══════════════════════════════════════════════════════════════════════════

    def is_valid_placement_position(self, row: int, col: int) -> bool:
        return (row, col) in self.config['grey_cells']

    def place_dot_with_symmetry(self, row: int, col: int) -> bool:
        if self.is_valid_placement_position(row, col) and not self.grid[row][col]:
            self.age_dots()
            if random.random() < self.config['dot_creation_prob']:
                self.grid[row][col] = True
                self.dot_timers[(row, col)] = self.config['dot_lifetime']
                mr, mc = col, row
                if mr != mc:
                    self.grid[mr][mc] = True
                    self.dot_timers[(mr, mc)] = self.config['dot_lifetime']
                self.log_action(f"EG ({row+1},{col+1})")
                self.check_win_condition()
                return True
            else:
                self._add_flash(row, col)
                self.log_action(f"EG FAIL ({row+1},{col+1})")
        return False

    def can_merge(self, pos1: Tuple[int,int], pos2: Tuple[int,int]) -> bool:
        r1, c1 = pos1; r2, c2 = pos2
        return not (r1 == c2 and c1 == r2)

    def merge_dots_with_symmetry(self, pos1: Tuple[int,int], pos2: Tuple[int,int]):
        r1, c1 = pos1; r2, c2 = pos2
        if not self.can_merge(pos1, pos2):
            return
        if self.grid[r1][c1] and self.grid[r2][c2]:
            self.age_dots()
            if random.random() < self.config['dot_merge_prob']:
                lt1      = self.dot_timers.get((r1, c1), self.config['dot_lifetime'])
                lt2      = self.dot_timers.get((r2, c2), self.config['dot_lifetime'])
                avg_life = (lt1 + lt2) // 2
                nr, nc = -1, -1
                if   c1 == r2: nr, nc = r1, c2
                elif c1 == c2: nr, nc = r1, r2
                elif r1 == r2: nr, nc = c1, c2
                elif r1 == c2: nr, nc = c1, r2
                if nr != -1 and nc != -1:
                    self.remove_dot(r1, c1)
                    self.remove_dot(r2, c2)
                    if (nr, nc) not in self.config['black_cells']:
                        self.grid[nr][nc] = True
                        self.dot_timers[(nr, nc)] = avg_life
                        mr, mc = nc, nr
                        if mr != mc:
                            self.grid[mr][mc] = True
                            self.dot_timers[(mr, mc)] = avg_life
                    self.log_action(f"ES ({r1+1},{c1+1})x({r2+1},{c2+1})")
                    self.check_win_condition()
            else:
                self._add_flash(r1, c1)
                self._add_flash(r2, c2)
                self.log_action(f"ES FAIL ({r1+1},{c1+1})x({r2+1},{c2+1})")

    def remove_dot(self, row: int, col: int):
        self.grid[row][col] = False
        self.dot_timers.pop((row, col), None)
        mr, mc = col, row
        if mr != mc:
            self.grid[mr][mc] = False
            self.dot_timers.pop((mr, mc), None)

    def age_dots(self):
        self.action_count += 1
        expired = []
        for pos in list(self.dot_timers):
            self.dot_timers[pos] -= 1
            if self.dot_timers[pos] <= 0:
                expired.append(pos)
        for r, c in expired:
            self.remove_dot(r, c)

    def check_win_condition(self):
        tr, tc = self.config['target_position']
        if self.grid[tr][tc] or self.grid[tc][tr]:
            self.game_over = True
            self.win = True

    # ══════════════════════════════════════════════════════════════════════════
    # Input
    # ══════════════════════════════════════════════════════════════════════════

    def handle_click(self, pos: Tuple[int,int]):
        if self.game_over:
            return
        # If a pending swap is waiting, ignore new clicks until it fires
        if self._pending_swap is not None:
            return
        grid_pos = self.pos_to_grid(pos)
        if not grid_pos:
            return
        row, col = grid_pos
        if (row, col) in self.config['black_cells']:
            return
        if not self.config['merge_enabled']:
            self.place_dot_with_symmetry(row, col)
            return
        if self.is_valid_placement_position(row, col) and not self.grid[row][col]:
            self.place_dot_with_symmetry(row, col)
            return
        if (row, col) in self.selected_cells:
            self.selected_cells.remove((row, col))
        elif (row, col) not in self.config['black_cells']:
            if len(self.selected_cells) == 1:
                sr, sc = self.selected_cells[0]
                if row == sc and col == sr:
                    return   # refuse mirror selection
            self.selected_cells.append((row, col))
            if len(self.selected_cells) == 2:
                # Schedule the merge after a short display pause (300 ms)
                # so the player can see both cells highlighted simultaneously.
                self._pending_swap = (
                    self.selected_cells[0],
                    self.selected_cells[1],
                    pygame.time.get_ticks() + 300,
                )

    # ══════════════════════════════════════════════════════════════════════════
    # Logging
    # ══════════════════════════════════════════════════════════════════════════

    def log_action(self, action: str):
        self.action_log.append(action)

    # ══════════════════════════════════════════════════════════════════════════
    # Main loop
    # ══════════════════════════════════════════════════════════════════════════

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    self.handle_click(ev.pos)
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.__init__(self.config)

            # Fire deferred swap once the display pause has elapsed
            if self._pending_swap is not None:
                pos1, pos2, fire_at = self._pending_swap
                if pygame.time.get_ticks() >= fire_at:
                    self._pending_swap  = None
                    self.selected_cells = []
                    self.merge_dots_with_symmetry(pos1, pos2)

            self.draw_grid()
            clock.tick(60)