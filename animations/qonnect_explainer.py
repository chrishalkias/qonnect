"""Manim explainer for Qonnect's quantum-repeater network game."""

from __future__ import annotations

import numpy as np
from manim import (
    AnimationGroup,
    ArcBetweenPoints,
    Arrow,
    Circle,
    Create,
    DashedLine,
    Dot,
    DOWN,
    FadeIn,
    FadeOut,
    Flash,
    GrowArrow,
    LEFT,
    Line,
    ORIGIN,
    Rectangle,
    ReplacementTransform,
    RIGHT,
    RoundedRectangle,
    Scene,
    Succession,
    Text,
    Transform,
    UP,
    VGroup,
    WHITE,
    Write,
)


BACKGROUND = "#06080A"
PANEL = "#0A0D0F"
CELL = "#101618"
BORDER = "#284644"
DIM = "#5A7876"
TEXT = "#A0DCD2"
BRIGHT = "#D2FFF5"
CYAN = "#00E6DC"
CYAN_GLOW = "#006E6E"
GREEN = "#3CFF82"
GREEN_GLOW = "#00823C"
AMBER = "#FFB020"
RED = "#FF3C3C"

STORY_BEATS = (
    "game_board_mapping",
    "entanglement_generation",
    "entanglement_swapping",
    "end_to_end_link",
    "probability_and_decay",
    "physical_scope",
)

SWAP_RULE = "(i,j) + (j,k) → (i,k)"
PHYSICAL_SCOPE = (
    "Entanglement swapping uses a Bell-state measurement at the shared repeater, "
    "classical heralding and correction, and finite-lived quantum memory."
)
INTRO_TITLE = "Qonnect"
INTRO_SUBTITLE = "Extending quantum teleportation"
PANEL_HOLD_EXTENSION = 0.5


def txt(text: str, size: int = 28, color: str = TEXT, weight: str = "NORMAL") -> Text:
    return Text(text, font="monospace", font_size=size, color=color, weight=weight)


def panel_hold(base_seconds: float) -> float:
    return base_seconds + PANEL_HOLD_EXTENSION


def correction_outcomes() -> Text:
    return txt("00  01\n10  11", size=14, color=AMBER)


def action_log_transition(goal_steps: VGroup, first_log: Text) -> Succession:
    """Clear the instructions before revealing the first action-log entry."""
    return Succession(
        FadeOut(goal_steps),
        FadeIn(first_log, shift=LEFT * 0.15),
    )


def terminal_card(width: float, height: float, title: str | None = None) -> VGroup:
    box = Rectangle(
        width=width,
        height=height,
        stroke_color=BORDER,
        stroke_width=1.5,
        fill_color=PANEL,
        fill_opacity=1,
    )
    group = VGroup(box)
    if title:
        heading = txt(f"[ {title} ]", size=18, color=CYAN, weight="BOLD")
        heading.move_to(box.get_top() + DOWN * 0.28)
        rule = DashedLine(
            box.get_left() + RIGHT * 0.18 + UP * (height / 2 - 0.55),
            box.get_right() + LEFT * 0.18 + UP * (height / 2 - 0.55),
            dash_length=0.08,
            color=BORDER,
            stroke_width=1.2,
        )
        group.add(heading, rule)
    return group


def repeater(
    name: str,
    position: np.ndarray,
    endpoint: bool = False,
    label_direction: np.ndarray = LEFT,
) -> VGroup:
    color = GREEN if endpoint else CYAN
    glow = Circle(radius=0.27, color=color, fill_color=color, fill_opacity=0.10, stroke_opacity=0)
    body = Circle(radius=0.14, color=color, fill_color=CELL, fill_opacity=1, stroke_width=2)
    shine = Dot(radius=0.025, color=WHITE).shift(LEFT * 0.045 + UP * 0.045)
    node = VGroup(glow, body, shine).move_to(position)
    name_text = txt(name, size=18, color=color, weight="BOLD").next_to(
        node,
        label_direction,
        buff=0.16,
    )
    return VGroup(node, name_text)


def active_link(start: np.ndarray, end: np.ndarray, color: str = CYAN) -> VGroup:
    glow = Line(start, end, color=color, stroke_width=10, stroke_opacity=0.12)
    core = Line(start, end, color=color, stroke_width=3)
    particles = DashedLine(start, end, color=BRIGHT, stroke_width=1.5, dash_length=0.08)
    return VGroup(glow, core, particles)


def virtual_link(start: np.ndarray, end: np.ndarray, color: str = CYAN, angle: float = -1.1) -> VGroup:
    glow = ArcBetweenPoints(start, end, angle=angle, color=color, stroke_width=11, stroke_opacity=0.12)
    core = ArcBetweenPoints(start, end, angle=angle, color=color, stroke_width=3.5)
    return VGroup(glow, core)


def matrix_view(n: int, cell_size: float, center: np.ndarray) -> tuple[VGroup, dict[tuple[int, int], np.ndarray]]:
    cells = VGroup()
    centers: dict[tuple[int, int], np.ndarray] = {}
    total = n * cell_size
    top_left = center + LEFT * (total / 2) + UP * (total / 2)

    target = {(0, n - 1), (n - 1, 0)}
    valid = {(i, i + 1) for i in range(n - 1)} | {(i + 1, i) for i in range(n - 1)}

    for row in range(n):
        for col in range(n):
            pos = top_left + RIGHT * (col * cell_size + cell_size / 2) + DOWN * (
                row * cell_size + cell_size / 2
            )
            centers[(row, col)] = pos
            if row == col:
                fill, stroke = BACKGROUND, "#661E20"
            elif (row, col) in target:
                fill, stroke = "#0A2016", GREEN
            elif (row, col) in valid:
                fill, stroke = "#102224", "#288282"
            else:
                fill, stroke = CELL, BORDER
            cells.add(
                Rectangle(
                    width=cell_size - 0.04,
                    height=cell_size - 0.04,
                    fill_color=fill,
                    fill_opacity=1,
                    stroke_color=stroke,
                    stroke_width=1.4,
                ).move_to(pos)
            )

    row_labels = VGroup()
    col_labels = VGroup()
    for index in range(n):
        row_labels.add(
            txt(f"R{index + 1}", size=16, color=DIM).move_to(
                centers[(index, 0)] + LEFT * (cell_size * 0.78)
            )
        )
        col_labels.add(
            txt(f"R{index + 1}", size=16, color=DIM).move_to(
                centers[(0, index)] + UP * (cell_size * 0.73)
            )
        )

    diagonal = Line(
        centers[(0, 0)] + LEFT * (cell_size / 2) + UP * (cell_size / 2),
        centers[(n - 1, n - 1)] + RIGHT * (cell_size / 2) + DOWN * (cell_size / 2),
        color=RED,
        stroke_width=1.5,
        stroke_opacity=0.55,
    )
    return VGroup(cells, row_labels, col_labels, diagonal), centers


def matrix_dot(position: np.ndarray, color: str = CYAN) -> VGroup:
    halo = Circle(radius=0.18, fill_color=color, fill_opacity=0.12, stroke_opacity=0)
    dot = Dot(radius=0.085, color=color)
    shine = Dot(radius=0.018, color=WHITE).shift(LEFT * 0.025 + UP * 0.025)
    return VGroup(halo, dot, shine).move_to(position)


def selection(position: np.ndarray, size: float = 0.76) -> VGroup:
    outer = Rectangle(width=size, height=size, color=AMBER, stroke_width=3)
    inner = Rectangle(width=size - 0.10, height=size - 0.10, color=AMBER, stroke_width=1)
    return VGroup(outer, inner).move_to(position)


class QonnectRepeaterExplainer(Scene):
    def construct(self) -> None:
        self.camera.background_color = BACKGROUND
        self.add_scanlines()
        self.introduction()
        self.setup_game_interface()
        self.board_mapping()
        self.entanglement_generation()
        self.entanglement_swapping()
        self.physical_workflow()
        self.probability_and_decay()
        self.final_scope()

    def add_scanlines(self) -> None:
        lines = VGroup(
            *[
                Line(LEFT * 7.1, RIGHT * 7.1, color="#132020", stroke_width=0.45, stroke_opacity=0.32)
                .shift(UP * (3.9 - index * 0.16))
                for index in range(50)
            ]
        )
        lines.set_z_index(100)
        self.add(lines)

    def introduction(self) -> None:
        status = txt("QUANTUM REPEATER NETWORK // ONLINE", size=19, color=CYAN)
        status.to_edge(UP, buff=0.65)
        title_shadow_a = txt(INTRO_TITLE, size=72, color="#FF2864", weight="BOLD").shift(LEFT * 0.035)
        title_shadow_b = txt(INTRO_TITLE, size=72, color=CYAN, weight="BOLD").shift(RIGHT * 0.035)
        title = txt(INTRO_TITLE, size=72, color=BRIGHT, weight="BOLD")
        title_group = VGroup(title_shadow_a, title_shadow_b, title)
        title_group.move_to(UP * 0.65)
        subtitle = txt(INTRO_SUBTITLE, size=28, color=TEXT)
        subtitle.next_to(title_group, DOWN, buff=0.24)

        node_positions = [LEFT * 2.7, LEFT * 0.9, RIGHT * 0.9, RIGHT * 2.7]
        nodes = VGroup(*[repeater(f"R{i + 1}", p + DOWN * 1.6, endpoint=i in (0, 3)) for i, p in enumerate(node_positions)])
        rails = VGroup(
            *[
                DashedLine(
                    nodes[i][0].get_center(),
                    nodes[i + 1][0].get_center(),
                    color=BORDER,
                    dash_length=0.12,
                )
                for i in range(3)
            ]
        )

        self.play(FadeIn(status), FadeIn(title_shadow_a), FadeIn(title_shadow_b), Write(title))
        self.play(FadeIn(subtitle), FadeIn(rails), FadeIn(nodes, lag_ratio=0.12), run_time=1.2)
        pulse = active_link(nodes[0][0].get_center(), nodes[-1][0].get_center(), GREEN)
        self.play(Create(pulse), run_time=1.2)
        self.wait(panel_hold(0.8))
        self.play(FadeOut(VGroup(status, title_group, subtitle, nodes, rails, pulse)), run_time=0.7)

    def setup_game_interface(self) -> None:
        heading = txt("QONNECT // CHAIN MODE", size=27, color=BRIGHT, weight="BOLD")
        heading.to_edge(UP, buff=0.26)
        left_card = terminal_card(2.8, 6.35, "SYSTEM").move_to(LEFT * 5.5 + DOWN * 0.28)
        board_card = terminal_card(5.6, 6.35, "LINK MATRIX").move_to(LEFT * 1.05 + DOWN * 0.28)
        side_card = terminal_card(3.2, 6.35, "ACTION LOG").move_to(RIGHT * 5.15 + DOWN * 0.28)

        node_positions = [np.array([-5.05, 1.75 - i * 1.15, 0]) for i in range(4)]
        nodes = VGroup(
            *[
                repeater(f"R{i + 1}", position, endpoint=i in (0, 3))
                for i, position in enumerate(node_positions)
            ]
        )
        physical_edges = VGroup(
            *[
                DashedLine(
                    node_positions[i],
                    node_positions[i + 1],
                    color=BORDER,
                    dash_length=0.08,
                    stroke_width=2,
                )
                for i in range(3)
            ]
        )

        matrix, centers = matrix_view(4, 0.88, np.array([-0.75, -0.15, 0]))
        legend = VGroup(
            txt("cyan", size=16, color=CYAN),
            txt("= entangled link", size=16, color=DIM),
            txt("green", size=16, color=GREEN),
            txt("= endpoint target", size=16, color=DIM),
        ).arrange_in_grid(rows=2, cols=2, cell_alignment=LEFT, buff=(0.12, 0.12))
        legend.move_to(board_card.get_bottom() + UP * 0.48)

        goal = txt("GOAL", size=19, color=GREEN, weight="BOLD")
        goal_text = txt("connect R1 ↔ R4", size=20, color=BRIGHT)
        steps = VGroup(
            goal,
            goal_text,
            txt("", size=8),
            txt("click valid cell", size=17, color=DIM),
            txt("select 2 links", size=17, color=DIM),
            txt("swap through", size=17, color=DIM),
            txt("shared repeater", size=17, color=DIM),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
        steps.move_to(side_card.get_center() + UP * 1.1)

        params = VGroup(
            txt("p_create : 0.80", size=16, color=TEXT),
            txt("p_swap   : 0.80", size=16, color=TEXT),
            txt("lifetime : 5", size=16, color=TEXT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        params.move_to(side_card.get_bottom() + UP * 0.72)

        self.play(FadeIn(heading), FadeIn(left_card), FadeIn(board_card), FadeIn(side_card))
        self.play(FadeIn(physical_edges), FadeIn(nodes, lag_ratio=0.12), Create(matrix), run_time=1.4)
        self.play(FadeIn(legend), FadeIn(steps), FadeIn(params))

        self.interface = VGroup(
            heading,
            left_card,
            board_card,
            side_card,
            physical_edges,
            nodes,
            matrix,
            legend,
            steps,
            params,
        )
        self.nodes = nodes
        self.node_positions = node_positions
        self.centers = centers
        self.goal_steps = steps
        self.active_links: dict[tuple[int, int], VGroup] = {}
        self.board_dots: dict[tuple[int, int], VGroup] = {}
        self.log_items = VGroup()

    def log(self, message: str, color: str = TEXT) -> Text:
        entry = txt(message, size=15, color=color)
        y = -0.10 - len(self.log_items) * 0.32
        entry.move_to(np.array([5.05, y, 0]))
        self.log_items.add(entry)
        return entry

    def add_board_link(self, i: int, j: int, color: str = CYAN) -> VGroup:
        pair = VGroup(matrix_dot(self.centers[(i, j)], color), matrix_dot(self.centers[(j, i)], color))
        self.board_dots[(min(i, j), max(i, j))] = pair
        return pair

    def board_mapping(self) -> None:
        map_title = txt("cell (i,j) = link Ri ↔ Rj", size=17, color=BRIGHT, weight="BOLD")
        map_title.move_to(UP * 2.15 + LEFT * 0.75)
        link = active_link(self.node_positions[0], self.node_positions[1])
        dots = self.add_board_link(0, 1)
        mirror = DashedLine(
            self.centers[(0, 1)], self.centers[(1, 0)], color=AMBER, dash_length=0.08
        )
        note = txt("mirror cells = one undirected link", size=16, color=AMBER)
        note.move_to(np.array([-0.75, -2.15, 0]))

        self.play(FadeIn(map_title), Create(link), FadeIn(dots), Create(mirror), run_time=1.4)
        self.play(FadeIn(note), Flash(self.centers[(0, 1)], color=CYAN), Flash(self.centers[(1, 0)], color=CYAN))
        self.wait(panel_hold(1.0))
        self.play(FadeOut(VGroup(map_title, mirror, note)))

        self.active_links[(0, 1)] = link
        first_log = self.log("EG (R1,R2)", CYAN)
        self.play(action_log_transition(self.goal_steps, first_log))

    def entanglement_generation(self) -> None:
        operation = txt("ENTANGLE ADJACENT\nREPEATERS", size=16, color=CYAN, weight="BOLD")
        operation.move_to(np.array([5.05, 1.38, 0]))
        equation = txt("|00〉 → (|00〉+|11〉)/√2", size=13, color=BRIGHT)
        equation.next_to(operation, DOWN, buff=0.18)
        self.play(FadeIn(operation), Write(equation), run_time=0.9)

        for i, j in ((1, 2), (2, 3)):
            link = active_link(self.node_positions[i], self.node_positions[j])
            dots = self.add_board_link(i, j)
            log_entry = self.log(f"EG (R{i + 1},R{j + 1})", CYAN)
            self.play(
                AnimationGroup(Create(link), FadeIn(dots), FadeIn(log_entry, shift=LEFT * 0.12), lag_ratio=0),
                run_time=1.0,
            )
            self.active_links[(i, j)] = link

        clocks = VGroup(
            *[
                txt("life 5", size=14, color=TEXT).next_to(
                    self.centers[pair], RIGHT, buff=0.08
                )
                for pair in ((0, 1), (1, 2), (2, 3))
            ]
        )
        self.play(FadeIn(clocks, lag_ratio=0.12))
        self.wait(panel_hold(0.8))
        self.play(FadeOut(VGroup(operation, equation, clocks)))

    def entanglement_swapping(self) -> None:
        title = txt("SELECT TWO LINKS\nSHARING A REPEATER", size=15, color=AMBER, weight="BOLD")
        title.move_to(np.array([5.05, 1.38, 0]))
        rule = txt(SWAP_RULE, size=14, color=BRIGHT)
        rule.next_to(title, DOWN, buff=0.18)
        self.play(FadeIn(title), FadeIn(rule))

        select_a = selection(self.centers[(0, 1)])
        select_b = selection(self.centers[(1, 2)])
        beam = Line(self.centers[(0, 1)], self.centers[(1, 2)], color=AMBER, stroke_width=4)
        self.play(Create(select_a), Create(select_b), Create(beam), run_time=0.8)

        bsm = txt("Bell measurement @ R2", size=16, color=AMBER)
        bsm.move_to(np.array([5.05, 0.42, 0]))
        self.play(FadeIn(bsm), Flash(self.node_positions[1], color=AMBER), run_time=0.8)

        old_links = VGroup(self.active_links.pop((0, 1)), self.active_links.pop((1, 2)))
        old_dots = VGroup(self.board_dots.pop((0, 1)), self.board_dots.pop((1, 2)))
        long_link = virtual_link(self.node_positions[0], self.node_positions[2])
        long_dots = self.add_board_link(0, 2)
        log_entry = self.log("ES R2 : R1↔R3", AMBER)
        self.play(
            FadeOut(VGroup(old_links, old_dots, select_a, select_b, beam)),
            Create(long_link),
            FadeIn(long_dots),
            FadeIn(log_entry, shift=LEFT * 0.12),
            run_time=1.2,
        )
        self.active_links[(0, 2)] = long_link

        new_rule = txt("(R1,R3)+(R3,R4) → (R1,R4)", size=13, color=BRIGHT)
        new_rule.move_to(rule)
        self.play(ReplacementTransform(rule, new_rule), bsm.animate.set_opacity(0.35))

        select_c = selection(self.centers[(0, 2)])
        select_d = selection(self.centers[(2, 3)])
        self.play(Create(select_c), Create(select_d), Flash(self.node_positions[2], color=AMBER))

        old_links_2 = VGroup(self.active_links.pop((0, 2)), self.active_links.pop((2, 3)))
        old_dots_2 = VGroup(self.board_dots.pop((0, 2)), self.board_dots.pop((2, 3)))
        target_link = virtual_link(self.node_positions[0], self.node_positions[3], GREEN, angle=-1.25)
        target_dots = self.add_board_link(0, 3, GREEN)
        win_log = self.log("TARGET R1↔R4", GREEN)
        self.play(
            FadeOut(VGroup(old_links_2, old_dots_2, select_c, select_d)),
            Create(target_link),
            FadeIn(target_dots),
            FadeIn(win_log, shift=LEFT * 0.12),
            run_time=1.2,
        )
        self.active_links[(0, 3)] = target_link

        win_box = RoundedRectangle(
            width=7.0,
            height=1.25,
            corner_radius=0.08,
            fill_color=BACKGROUND,
            fill_opacity=0.94,
            stroke_color=GREEN,
            stroke_width=3,
        )
        win_text = txt("END-TO-END LINKED!", size=34, color=GREEN, weight="BOLD")
        win_group = VGroup(win_box, win_text).move_to(ORIGIN)
        self.play(FadeIn(win_group, scale=0.9), Flash(ORIGIN, color=GREEN, flash_radius=3.5), run_time=1.0)
        self.wait(panel_hold(1.2))
        self.play(FadeOut(win_group), FadeOut(VGroup(title, new_rule, bsm)))
        self.wait(0.5)

    def physical_workflow(self) -> None:
        self.play(FadeOut(VGroup(self.interface, self.log_items, *self.active_links.values(), *self.board_dots.values())), run_time=0.8)

        heading = txt("WHAT THE REPEATER NETWORK DOES", size=31, color=BRIGHT, weight="BOLD")
        heading.to_edge(UP, buff=0.35)
        subtitle = txt("Qonnect compresses a hardware protocol into two board actions.", size=21, color=TEXT)
        subtitle.next_to(heading, DOWN, buff=0.16)

        labels = ["ESTABLISH", "STORE", "SWAP", "CORRECT", "CONNECT"]
        colors = [CYAN, CYAN, AMBER, AMBER, GREEN]
        cards = VGroup(*[terminal_card(2.35, 3.9, name) for name in labels]).arrange(RIGHT, buff=0.26)
        cards.move_to(DOWN * 0.35)

        icons = VGroup()
        captions = VGroup()

        photon_line = DashedLine(LEFT * 0.62, RIGHT * 0.62, color=CYAN, dash_length=0.09)
        photon_nodes = VGroup(Circle(0.13, color=CYAN), Circle(0.13, color=CYAN))
        photon_nodes[0].move_to(photon_line.get_left())
        photon_nodes[1].move_to(photon_line.get_right())
        icons.add(VGroup(photon_line, photon_nodes).move_to(cards[0].get_center() + UP * 0.35))
        captions.add(txt("photons create\nan adjacent Bell pair", size=12, color=TEXT).next_to(cards[0].get_bottom(), UP, buff=0.35))

        memory = RoundedRectangle(
            width=1.1,
            height=0.8,
            corner_radius=0.08,
            color=CYAN,
            fill_color=CELL,
            fill_opacity=1,
        )
        memory_text = txt("MEM", size=22, color=CYAN, weight="BOLD").move_to(memory)
        timer = txt("5 4 3…", size=16, color=AMBER).next_to(memory, DOWN, buff=0.16)
        icons.add(VGroup(memory, memory_text, timer).move_to(cards[1].get_center() + UP * 0.25))
        captions.add(txt("quantum memories\nhold finite-lived pairs", size=12, color=TEXT).next_to(cards[1].get_bottom(), UP, buff=0.35))

        bsm_box = Rectangle(
            width=0.85,
            height=0.68,
            color=AMBER,
            fill_color=CELL,
            fill_opacity=1,
        )
        bsm_text = txt("BSM", size=18, color=AMBER, weight="BOLD").move_to(bsm_box)
        bsm_arrows = VGroup(
            Arrow(LEFT * 0.8 + UP * 0.35, bsm_box.get_left(), color=CYAN, buff=0),
            Arrow(LEFT * 0.8 + DOWN * 0.35, bsm_box.get_left(), color=CYAN, buff=0),
        )
        icons.add(VGroup(bsm_box, bsm_text, bsm_arrows).move_to(cards[2].get_center() + UP * 0.35))
        captions.add(txt("Bell-state measurement\nat the shared repeater", size=12, color=TEXT).next_to(cards[2].get_bottom(), UP, buff=0.35))

        bit = correction_outcomes()
        signal = VGroup(
            Line(LEFT * 0.7, RIGHT * 0.7, color=AMBER),
            *[Line(UP * 0.12, DOWN * 0.12, color=AMBER).shift(RIGHT * x) for x in (-0.45, 0, 0.45)],
        )
        icons.add(VGroup(bit, signal).arrange(DOWN, buff=0.18).move_to(cards[3].get_center() + UP * 0.3))
        captions.add(txt("classical heralding\nand Pauli correction", size=12, color=TEXT).next_to(cards[3].get_bottom(), UP, buff=0.35))

        end_nodes = VGroup(Circle(0.15, color=GREEN), Circle(0.15, color=GREEN)).arrange(RIGHT, buff=1.0)
        end_link = active_link(end_nodes[0].get_center(), end_nodes[1].get_center(), GREEN)
        icons.add(VGroup(end_link, end_nodes).move_to(cards[4].get_center() + UP * 0.35))
        captions.add(txt("a longer entangled link\nconnects distant users", size=12, color=TEXT).next_to(cards[4].get_bottom(), UP, buff=0.35))

        stage_arrows = VGroup(
            *[
                Arrow(cards[i].get_right(), cards[i + 1].get_left(), color=colors[i], buff=0.08, stroke_width=2)
                for i in range(4)
            ]
        )

        self.play(FadeIn(heading), FadeIn(subtitle), FadeIn(cards, lag_ratio=0.08), run_time=1.2)
        for index in range(5):
            animations = [FadeIn(icons[index]), FadeIn(captions[index])]
            if index < 4:
                animations.append(GrowArrow(stage_arrows[index]))
            self.play(*animations, run_time=0.75)
        self.wait(panel_hold(1.0))

        scope = txt(
            "The game abstracts the hardware into EG clicks and ES merges.",
            size=21,
            color=BRIGHT,
            weight="BOLD",
        ).to_edge(DOWN, buff=0.22)
        self.play(FadeIn(scope, shift=UP * 0.1))
        self.wait(panel_hold(1.0))
        self.play(FadeOut(VGroup(heading, subtitle, cards, icons, captions, stage_arrows, scope)), run_time=0.8)

    def probability_and_decay(self) -> None:
        heading = txt("THE NETWORK IS STOCHASTIC", size=32, color=BRIGHT, weight="BOLD")
        heading.to_edge(UP, buff=0.42)
        subtitle = txt("Every move competes with failure and decoherence.", size=22, color=TEXT)
        subtitle.next_to(heading, DOWN, buff=0.16)

        probability_card = terminal_card(5.6, 4.7, "SUCCESS PROBABILITY").shift(LEFT * 3.15 + DOWN * 0.42)
        memory_card = terminal_card(5.6, 4.7, "MEMORY LIFETIME").shift(RIGHT * 3.15 + DOWN * 0.42)

        p_create = txt("p_create = 0.80", size=25, color=CYAN, weight="BOLD")
        p_swap = txt("p_swap   = 0.80", size=25, color=AMBER, weight="BOLD")
        chance = VGroup(p_create, p_swap).arrange(DOWN, aligned_edge=LEFT, buff=0.34)
        chance.move_to(probability_card.get_center() + UP * 0.45)
        fail = txt("operation failed", size=20, color=RED, weight="BOLD")
        x1 = Line(LEFT * 0.34, RIGHT * 0.34, color=RED, stroke_width=6).rotate(np.pi / 4)
        x2 = x1.copy().rotate(np.pi / 2)
        fail_group = VGroup(x1, x2, fail).arrange(DOWN, buff=0.22)
        fail_group.move_to(probability_card.get_center() + DOWN * 1.0)

        memories = VGroup(*[Circle(0.16, color=CYAN, fill_color=CYAN, fill_opacity=0.8) for _ in range(5)])
        memories.arrange(RIGHT, buff=0.24).move_to(memory_card.get_center() + UP * 0.55)
        timer = txt("5 → 4 → 3 → 2 → 1 → 0", size=22, color=AMBER)
        timer.next_to(memories, DOWN, buff=0.42)
        decay = txt("link expires", size=22, color=RED, weight="BOLD").next_to(timer, DOWN, buff=0.38)

        self.play(FadeIn(heading), FadeIn(subtitle), FadeIn(probability_card), FadeIn(memory_card))
        self.play(FadeIn(chance), FadeIn(memories, lag_ratio=0.1), FadeIn(timer))
        self.play(FadeIn(fail_group), memories.animate.set_opacity(0.12), FadeIn(decay), run_time=1.2)

        policy = txt("Plan the swaps before the memories expire.", size=28, color=GREEN, weight="BOLD")
        policy.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(policy, shift=UP * 0.15))
        self.wait(panel_hold(1.4))
        self.play(FadeOut(VGroup(heading, subtitle, probability_card, memory_card, chance, fail_group, memories, timer, decay, policy)), run_time=0.8)

    def final_scope(self) -> None:
        kicker = txt("WHAT QONNECT TEACHES", size=20, color=CYAN, weight="BOLD")
        heading = txt("Quantum networking is a control problem", size=38, color=BRIGHT, weight="BOLD")
        bullets = VGroup(
            txt("✓ generate short links", size=24, color=GREEN, weight="BOLD"),
            txt("✓ store them in quantum memory", size=24, color=GREEN, weight="BOLD"),
            txt("✓ swap through shared repeaters", size=24, color=GREEN, weight="BOLD"),
            txt("✓ reach the endpoints before decoherence", size=24, color=GREEN, weight="BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        divider = Line(LEFT * 5.2, RIGHT * 5.2, color=BORDER, stroke_width=1.5)
        scope_title = txt("PHYSICAL SCOPE", size=18, color=AMBER, weight="BOLD")
        scope = txt(
            "Real swapping uses a Bell-state measurement, classical heralding,\n"
            "Pauli correction, and noisy finite-lived quantum memories.",
            size=19,
            color=TEXT,
        )

        group = VGroup(kicker, heading, bullets, divider, scope_title, scope)
        group.arrange(DOWN, buff=0.27).move_to(ORIGIN + UP * 0.15)

        endpoints = VGroup(
            repeater("ALICE", LEFT * 1.3 + DOWN * 3.15, True),
            repeater(
                "BOB",
                RIGHT * 1.3 + DOWN * 3.15,
                True,
                label_direction=RIGHT,
            ),
        )
        link = active_link(endpoints[0][0].get_center(), endpoints[1][0].get_center(), GREEN)

        self.play(FadeIn(kicker), Write(heading), run_time=1.0)
        self.play(FadeIn(bullets, lag_ratio=0.16), run_time=1.2)
        self.play(Create(divider), FadeIn(scope_title), FadeIn(scope), run_time=0.9)
        self.play(FadeIn(endpoints), Create(link), run_time=0.8)
        self.wait(panel_hold(2.2))
