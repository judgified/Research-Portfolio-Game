#!/usr/bin/env python3
"""
Unspoken — a narrative choice game built with Pygame.
Explores constrained identity through Omar's story (fictional setting).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pygame

# --- Display -----------------------------------------------------------------
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
# Story panel sits below the title so text is not covered by the HUD.
STORY_RECT = pygame.Rect(40, 72, 720, 320)
TITLE = "Unspoken"

# Colors (RGB)
COLOR_BG = (18, 18, 22)
COLOR_STORY_BG = (28, 28, 36)
COLOR_BORDER = (70, 70, 90)
COLOR_TEXT = (230, 230, 235)
COLOR_MUTED = (140, 140, 155)
COLOR_BUTTON = (55, 75, 110)
COLOR_BUTTON_HOVER = (70, 95, 140)
COLOR_BUTTON_DISABLED = (45, 45, 52)
COLOR_ACCENT = (180, 160, 120)

# --- Game stats (starting values per design) ---------------------------------
family_honor = 50
religious_conformity = 50
state_suspicion = 0


def clamp_stat(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def apply_deltas(dh: int, dc: int, ds: int) -> None:
    global family_honor, religious_conformity, state_suspicion
    family_honor = clamp_stat(family_honor + dh)
    religious_conformity = clamp_stat(religious_conformity + dc)
    state_suspicion = clamp_stat(state_suspicion + ds)


# --- Ending resolution -------------------------------------------------------
# No single "win"; each ending reflects the path taken under constraint.
def resolve_ending() -> str:
    fh, rc, ss = family_honor, religious_conformity, state_suspicion

    # Priority: clearest signals first, then nuanced branches.
    if ss >= 72:
        return "targeted"
    if rc >= 78:
        return "assimilation"
    if fh <= 22:
        return "isolation"
    if rc <= 38 and 28 <= ss <= 68:
        return "escape"
    if 34 <= fh <= 66 and 34 <= rc <= 66 and ss <= 52:
        return "witness"
    # Near-balanced fallback toward witness; otherwise pick closest theme.
    if ss >= 55:
        return "targeted"
    if rc >= 65:
        return "assimilation"
    if fh <= 35:
        return "isolation"
    return "witness"


ENDING_TEXT: dict[str, str] = {
    "assimilation": (
        "Assimilation\n\n"
        "Omar learns the right phrases, the right silences. Doors open that never "
        "opened before—because the cost is paid in the mirror. He is safe in the "
        "way a mask is safe: held in place by everyone who refuses to see what is "
        "underneath. The story they tell about him is finally simple. He repeats it."
    ),
    "isolation": (
        "Isolation\n\n"
        "The house grows quiet around him. Honor, in their mouths, becomes a blade "
        "with his name on it. He is not cast out in a single dramatic scene—only "
        "nudged, again and again, toward the edge of the room. He learns to eat "
        "without expecting a chair pulled out for him. Love, he realizes, can be "
        "real and still be conditional."
    ),
    "escape": (
        "Escape\n\n"
        "He leaves with little more than a bag and a borrowed name. The border is "
        "a line someone drew while he was sleeping; crossing it does not erase the "
        "past, but it changes which laws can reach him first. Suspicion follows "
        "like weather—sometimes distant, sometimes close. Freedom, he finds, is not "
        "a place. It is a series of rooms where the questions are different."
    ),
    "targeted": (
        "Targeted\n\n"
        "The state does not need to be fair; it only needs to be certain. Files "
        "multiply. A visit becomes a pattern. Omar understands, with cold clarity, "
        "that innocence is not a shield when suspicion is the weapon. He becomes "
        "a lesson others tell quietly: what happens when you are seen too clearly "
        "in a system that profits from fear."
    ),
    "witness": (
        "Witness\n\n"
        "Nothing resolves cleanly. Omar keeps parts of himself in separate pockets—"
        "one for family, one for faith, one for survival. He is not celebrated and "
        "not destroyed; he is alive in the uncomfortable middle. He tells the truth "
        "in small, careful pieces, and learns that some stories are only safe when "
        "they are incomplete. The cost is fatigue. The reward is breath."
    ),
}


# --- Choice / scene model ----------------------------------------------------
@dataclass
class Choice:
    label: str
    deltas: tuple[int, int, int]  # (family_honor, religious_conformity, state_suspicion)
    enabled_if: Callable[[], bool] | None = None
    locked_reason: str = ""


@dataclass
class Scene:
    id: str
    title: str
    body: str
    choices: list[Choice] = field(default_factory=list)


def build_scenes() -> dict[str, Scene]:
    """Five narrative beats: Naming, Family, Authority, Violence, Ending (resolved)."""
    return {
        "naming": Scene(
            id="naming",
            title="I — Naming",
            body=(
                "Morning light finds Omar at a plastic table in a municipal hall. "
                "Forms ask for a name the state can file, a name his family can "
                "repeat without flinching. The clerk taps a pen. Somewhere between "
                "language and law, identity becomes paperwork."
            ),
            choices=[
                Choice(
                    "Use the official spelling on every line.",
                    (5, 12, 4),
                ),
                Choice(
                    "Insist on the spelling his grandmother taught him.",
                    (10, -6, 8),
                ),
                Choice(
                    "Leave the middle name blank—half-visible on purpose.",
                    (-4, -8, 15),
                ),
            ],
        ),
        "family": Scene(
            id="family",
            title="II — Family",
            body=(
                "Home smells like rice and worry. His uncle speaks of reputation as "
                "if it were oxygen. His mother listens more than she speaks. Omar "
                "understands: some rooms are not debates; they are tests you are "
                "not supposed to fail out loud."
            ),
            choices=[
                Choice(
                    "Agree publicly; argue later in private.",
                    (8, 6, 2),
                ),
                Choice(
                    "Name what he actually wants, calmly, at the table.",
                    (-12, -4, 6),
                ),
                Choice(
                    "Stay silent and help clear the dishes—peace as performance.",
                    (4, 10, 0),
                ),
            ],
        ),
        "authority": Scene(
            id="authority",
            title="III — Authority",
            body=(
                "The street divides: a checkpoint, a sermon, a rumor traveling faster "
                "than truth. Faith and law overlap here like two shadows from one "
                "body. A uniform asks for papers. A voice asks for sincerity. Omar "
                "feels the weight of being readable."
            ),
            choices=[
                Choice(
                    "Answer exactly as expected; keep eyes lowered.",
                    (6, 14, 5),
                ),
                Choice(
                    "Speak carefully—truthful, but not provocative.",
                    (2, 2, 10),
                ),
                Choice(
                    "Refuse a humiliating question. Name the rule, not himself.",
                    (-8, -14, 22),
                    enabled_if=lambda: religious_conformity <= 58 or state_suspicion >= 14,
                    locked_reason="(locked: earlier choices left you too aligned to risk this)",
                ),
            ],
        ),
        "violence": Scene(
            id="violence",
            title="IV — Violence",
            body=(
                "A neighbor's door splinters. A crowd forms before anyone agrees on "
                "what it saw. Phones rise like small torches. Omar's pulse insists: "
                "move, speak, hide—choose before the moment hardens into history."
            ),
            choices=[
                Choice(
                    "Walk away fast; protect himself first.",
                    (-6, 4, 8),
                ),
                Choice(
                    "Record from the edge—evidence without a face in the frame.",
                    (-10, -6, 25),
                ),
                Choice(
                    "Step between a frightened kid and a raised hand.",
                    (12, -8, 18),
                    enabled_if=lambda: family_honor >= 35,
                    locked_reason="(locked: family would not believe you'd risk this)",
                ),
            ],
        ),
        "ending": Scene(
            id="ending",
            title="V — Ending",
            body="",
            choices=[],
        ),
    }


# --- Pygame helpers ----------------------------------------------------------
def wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current: list[str] = []
        for w in words:
            trial = " ".join(current + [w])
            if font.size(trial)[0] <= max_width or not current:
                current.append(w)
            else:
                lines.append(" ".join(current))
                current = [w]
        if current:
            lines.append(" ".join(current))
    return lines


def draw_hud(
    surface: pygame.Surface,
    font_small: pygame.font.Font,
    y_stats: int,
) -> None:
    hud = (
        f"Family honor: {family_honor}    "
        f"Religious conformity: {religious_conformity}    "
        f"State suspicion: {state_suspicion}"
    )
    surf = font_small.render(hud, True, COLOR_MUTED)
    surface.blit(surf, (40, y_stats))


def main() -> None:
    global family_honor, religious_conformity, state_suspicion

    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("arial", 22, bold=True)
    font_body = pygame.font.SysFont("arial", 18)
    font_small = pygame.font.SysFont("arial", 15)
    font_button = pygame.font.SysFont("arial", 16)

    scenes = build_scenes()
    current_scene_id = "naming"
    ending_key: str | None = None

    # Button layout
    button_width = 700
    button_height = 44
    button_left = 50
    button_start_y = 405
    button_gap = 52
    restart_y = button_start_y + 120

    running = True
    while running:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                scene = scenes[current_scene_id]
                if current_scene_id == "ending":
                    restart_rect = pygame.Rect(button_left, restart_y, 200, button_height)
                    if restart_rect.collidepoint(event.pos):
                        family_honor = 50
                        religious_conformity = 50
                        state_suspicion = 0
                        ending_key = None
                        current_scene_id = "naming"
                        scenes = build_scenes()
                    continue
                for i, choice in enumerate(scene.choices):
                    rect = pygame.Rect(
                        button_left,
                        button_start_y + i * button_gap,
                        button_width,
                        button_height,
                    )
                    enabled = choice.enabled_if is None or choice.enabled_if()
                    if rect.collidepoint(event.pos) and enabled:
                        dh, dc, ds = choice.deltas
                        apply_deltas(dh, dc, ds)
                        # Advance scene sequence
                        order = ["naming", "family", "authority", "violence", "ending"]
                        idx = order.index(current_scene_id)
                        if idx < len(order) - 1:
                            current_scene_id = order[idx + 1]
                        if current_scene_id == "ending":
                            ending_key = resolve_ending()
                            scenes["ending"].body = ENDING_TEXT[ending_key]
                            scenes["ending"].title = "V — What remained unspoken"
                        break

        # --- Draw ---
        screen.fill(COLOR_BG)

        scene = scenes[current_scene_id]
        y_stats = 16
        draw_hud(screen, font_small, y_stats)

        title_surf = font_title.render(scene.title, True, COLOR_ACCENT)
        screen.blit(title_surf, (40, 44))

        pygame.draw.rect(screen, COLOR_STORY_BG, STORY_RECT)
        pygame.draw.rect(screen, COLOR_BORDER, STORY_RECT, 1)

        body_lines = wrap_text(font_body, scene.body, STORY_RECT.width - 24)
        text_y = STORY_RECT.y + 12
        for line in body_lines:
            surf = font_body.render(line, True, COLOR_TEXT)
            screen.blit(surf, (STORY_RECT.x + 12, text_y))
            text_y += font_body.get_linesize() + 2

        if current_scene_id != "ending":
            hint = font_small.render(
                "Click a choice. Gray options are locked by your earlier path.",
                True,
                COLOR_MUTED,
            )
            screen.blit(hint, (40, 398))

            for i, choice in enumerate(scene.choices):
                rect = pygame.Rect(
                    button_left,
                    button_start_y + i * button_gap,
                    button_width,
                    button_height,
                )
                enabled = choice.enabled_if is None or choice.enabled_if()
                hover = rect.collidepoint(mouse)
                bg = (
                    COLOR_BUTTON_DISABLED
                    if not enabled
                    else (COLOR_BUTTON_HOVER if hover else COLOR_BUTTON)
                )
                pygame.draw.rect(screen, bg, rect)
                pygame.draw.rect(screen, COLOR_BORDER, rect, 1)

                label = choice.label
                if not enabled and choice.locked_reason:
                    label = f"{choice.label}  {choice.locked_reason}"
                text_color = COLOR_MUTED if not enabled else COLOR_TEXT
                txt = font_button.render(label, True, text_color)
                text_rect = txt.get_rect(center=rect.center)
                screen.blit(txt, text_rect)
        else:
            restart_rect = pygame.Rect(button_left, restart_y, 200, button_height)
            rh = restart_rect.collidepoint(mouse)
            pygame.draw.rect(
                screen,
                COLOR_BUTTON_HOVER if rh else COLOR_BUTTON,
                restart_rect,
            )
            pygame.draw.rect(screen, COLOR_BORDER, restart_rect, 1)
            rt = font_button.render("Play again", True, COLOR_TEXT)
            screen.blit(rt, rt.get_rect(center=restart_rect.center))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
