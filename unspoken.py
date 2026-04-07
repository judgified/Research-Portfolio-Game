#!/usr/bin/env python3
"""
Unspoken — a narrative choice game built with Pygame.
Explores constrained identity through Omar's story (fictional setting).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import pygame

# --- Display -----------------------------------------------------------------
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
# Story panel sits below the title so text is not covered by the HUD.
STORY_RECT = pygame.Rect(40, 72, 720, 320)
TITLE = "Unspoken"

# Colors (RGB) — dark olive slate / white / green / red / beige
COLOR_BG = (18, 22, 16)
COLOR_STORY_BG = (22, 30, 22)
COLOR_BORDER = (130, 38, 42)
COLOR_TEXT = (255, 255, 255)
COLOR_MUTED = (196, 186, 168)
COLOR_BUTTON = (28, 112, 58)
COLOR_BUTTON_HOVER = (46, 158, 82)
COLOR_BUTTON_DISABLED = (38, 36, 34)
COLOR_ACCENT = (232, 218, 188)
COLOR_TITLE_SHADOW = (28, 10, 12)
COLOR_TITLE_OUTLINE = (150, 44, 48)

# Start screen (not a narrative scene; `current_scene_id == "start"` before play)
START_BUTTON_RECT = pygame.Rect(230, 348, 340, 72)
BUTTON_CORNER_RADIUS = 14
CHOICE_NUMBER_STRIP_W = 44

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


def draw_vertical_gradient(
    surface: pygame.Surface,
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
) -> None:
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))


def blit_tracked_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    center_x: int,
    center_y: int,
    tracking: int = 5,
) -> pygame.Rect:
    glyphs: list[pygame.Surface] = [font.render(ch, True, color) for ch in text]
    total_w = sum(g.get_width() for g in glyphs) + max(0, len(glyphs) - 1) * tracking
    x0 = center_x - total_w // 2
    top = center_y - font.get_height() // 2
    out_rect = pygame.Rect(x0, top, total_w, font.get_height())
    offset = 0
    for i, surf in enumerate(glyphs):
        surface.blit(surf, (x0 + offset, top))
        offset += surf.get_width()
        if i < len(glyphs) - 1:
            offset += tracking
    return out_rect


def draw_rounded_fill(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    radius: int = BUTTON_CORNER_RADIUS,
) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_rounded_border(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    width: int,
    radius: int = BUTTON_CORNER_RADIUS,
) -> None:
    pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)


def draw_primary_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    main_label: str,
    font_main: pygame.font.Font,
    *,
    hover: bool,
    sublabel: str | None,
    font_sub: pygame.font.Font | None,
) -> None:
    fill = COLOR_BUTTON_HOVER if hover else COLOR_BUTTON
    draw_rounded_fill(surface, rect, fill)
    draw_rounded_border(surface, rect, COLOR_BORDER, 3 if hover else 2)
    if sublabel and font_sub:
        main_s = font_main.render(main_label, True, COLOR_TEXT)
        sub_s = font_sub.render(sublabel, True, COLOR_MUTED)
        gap = 6
        stack_h = main_s.get_height() + gap + sub_s.get_height()
        y = rect.centery - stack_h // 2
        surface.blit(main_s, main_s.get_rect(midtop=(rect.centerx, y)))
        surface.blit(
            sub_s,
            sub_s.get_rect(midtop=(rect.centerx, y + main_s.get_height() + gap)),
        )
    else:
        main_s = font_main.render(main_label, True, COLOR_TEXT)
        surface.blit(main_s, main_s.get_rect(center=rect.center))


def draw_choice_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    index_1based: int,
    label: str,
    font: pygame.font.Font,
    *,
    enabled: bool,
    hover: bool,
) -> None:
    if not enabled:
        draw_rounded_fill(surface, rect, COLOR_BUTTON_DISABLED)
        draw_rounded_border(surface, rect, (80, 70, 68), 1)
    else:
        draw_rounded_fill(surface, rect, COLOR_BUTTON_HOVER if hover else COLOR_BUTTON)
        draw_rounded_border(surface, rect, COLOR_BORDER, 3 if hover else 2)
    strip = pygame.Rect(rect.left, rect.top, CHOICE_NUMBER_STRIP_W, rect.height)
    pygame.draw.rect(
        surface,
        (48, 22, 24) if enabled else (32, 30, 28),
        strip,
        border_top_left_radius=BUTTON_CORNER_RADIUS,
        border_bottom_left_radius=BUTTON_CORNER_RADIUS,
    )
    num = font.render(str(index_1based), True, COLOR_ACCENT if enabled else COLOR_MUTED)
    surface.blit(num, num.get_rect(center=strip.center))
    text_x = rect.left + CHOICE_NUMBER_STRIP_W + 14
    lines = wrap_text(font, label, rect.right - text_x - 14)
    line_h = font.get_linesize()
    y = rect.centery - (len(lines) * line_h) // 2
    for line in lines:
        surf = font.render(line, True, COLOR_TEXT if enabled else COLOR_MUTED)
        surface.blit(surf, (text_x, y))
        y += line_h


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
    font_subtitle = pygame.font.SysFont("arial", 21)
    font_body = pygame.font.SysFont("arial", 18)
    font_small = pygame.font.SysFont("arial", 15)
    font_button = pygame.font.SysFont("arial", 17)
    font_cta = pygame.font.SysFont("arial", 24, bold=True)
    font_cta_hint = pygame.font.SysFont("arial", 14)

    scenes = build_scenes()
    # Begin on the start screen; "start" is not in `scenes`.
    current_scene_id = "start"
    ending_key: str | None = None

    # Button layout
    button_width = 700
    button_height = 54
    button_left = 50
    button_start_y = 424
    button_gap = 60
    restart_y = 508

    running = True
    while running:
        mouse = pygame.mouse.get_pos()
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                if current_scene_id == "start":
                    current_scene_id = "naming"
                elif current_scene_id == "ending":
                    family_honor = 50
                    religious_conformity = 50
                    state_suspicion = 0
                    ending_key = None
                    current_scene_id = "start"
                    scenes = build_scenes()
            elif event.type == pygame.KEYDOWN and current_scene_id in (
                "naming",
                "family",
                "authority",
                "violence",
            ):
                key_map = {
                    pygame.K_1: 0,
                    pygame.K_2: 1,
                    pygame.K_3: 2,
                    pygame.K_KP1: 0,
                    pygame.K_KP2: 1,
                    pygame.K_KP3: 2,
                }
                idx = key_map.get(event.key)
                if idx is not None:
                    scene_k = scenes[current_scene_id]
                    if idx < len(scene_k.choices):
                        choice = scene_k.choices[idx]
                        enabled = choice.enabled_if is None or choice.enabled_if()
                        if enabled:
                            apply_deltas(*choice.deltas)
                            order = ["naming", "family", "authority", "violence", "ending"]
                            j = order.index(current_scene_id)
                            if j < len(order) - 1:
                                current_scene_id = order[j + 1]
                            if current_scene_id == "ending":
                                ending_key = resolve_ending()
                                scenes["ending"].body = ENDING_TEXT[ending_key]
                                scenes["ending"].title = "V — What remained unspoken"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if current_scene_id == "start":
                    if START_BUTTON_RECT.collidepoint(event.pos):
                        current_scene_id = "naming"
                    continue
                scene = scenes[current_scene_id]
                if current_scene_id == "ending":
                    restart_rect = pygame.Rect(
                        START_BUTTON_RECT.x,
                        restart_y,
                        START_BUTTON_RECT.w,
                        START_BUTTON_RECT.h,
                    )
                    if restart_rect.collidepoint(event.pos):
                        family_honor = 50
                        religious_conformity = 50
                        state_suspicion = 0
                        ending_key = None
                        current_scene_id = "start"
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
        if current_scene_id == "start":
            draw_vertical_gradient(screen, (28, 36, 28), COLOR_BG)
        else:
            screen.fill(COLOR_BG)

        if current_scene_id == "start":
            cx = WINDOW_WIDTH // 2
            hero_y = 108
            track = 10
            pulse_scale = 1.0 + 0.03 * math.sin(now * 0.0048)
            title_font_size = max(74, int(90 * pulse_scale))
            font_start_pulse = pygame.font.SysFont("arial", title_font_size, bold=True)
            for dx, dy in ((5, 5), (3, 3), (1, 1)):
                blit_tracked_text(
                    screen,
                    font_start_pulse,
                    TITLE,
                    COLOR_TITLE_SHADOW,
                    cx + dx,
                    hero_y + dy,
                    tracking=track,
                )
            title_bounds = blit_tracked_text(
                screen,
                font_start_pulse,
                TITLE,
                COLOR_ACCENT,
                cx,
                hero_y,
                tracking=track,
            )
            underline_y = title_bounds.bottom + 24
            pygame.draw.line(
                screen,
                COLOR_TITLE_OUTLINE,
                (title_bounds.left, underline_y),
                (title_bounds.right, underline_y),
                3,
            )
            sub = font_subtitle.render(
                "A choice based story about identity under pressure",
                True,
                COLOR_MUTED,
            )
            screen.blit(sub, sub.get_rect(center=(cx, underline_y + 28)))
            blurb = (
                "You play as Omar. There is no winning, only paths shaped by "
                "family, faith, and the state. When you are ready, begin below."
            )
            blurb_y = underline_y + 54
            for i, line in enumerate(wrap_text(font_body, blurb, 640)):
                row = font_body.render(line, True, COLOR_TEXT)
                screen.blit(row, row.get_rect(center=(cx, blurb_y + i * 22)))

            sh = START_BUTTON_RECT.collidepoint(mouse)
            draw_primary_button(
                screen,
                START_BUTTON_RECT,
                "Begin story",
                font_cta,
                hover=sh,
                sublabel="Click here",
                font_sub=font_cta_hint,
            )

            esc_hint = font_small.render("Esc - quit", True, COLOR_MUTED)
            screen.blit(esc_hint, (40, WINDOW_HEIGHT - 32))
            alpha = 130 + int(90 * (0.5 + 0.5 * math.sin(now * 0.0065)))
            enter_prompt = font_small.render("Press Enter to begin", True, COLOR_ACCENT)
            enter_prompt.set_alpha(alpha)
            screen.blit(
                enter_prompt,
                enter_prompt.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30)),
            )
        else:
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

        if current_scene_id not in ("start", "ending"):
            hint = font_small.render(
                "Choose a numbered option | click or press 1 / 2 / 3 (gray = locked by your path)",
                True,
                COLOR_MUTED,
            )
            screen.blit(hint, (40, STORY_RECT.bottom + 10))

            for i, choice in enumerate(scene.choices):
                rect = pygame.Rect(
                    button_left,
                    button_start_y + i * button_gap,
                    button_width,
                    button_height,
                )
                enabled = choice.enabled_if is None or choice.enabled_if()
                hover = rect.collidepoint(mouse)
                label = choice.label
                if not enabled and choice.locked_reason:
                    label = f"{choice.label}  {choice.locked_reason}"
                draw_choice_button(
                    screen,
                    rect,
                    i + 1,
                    label,
                    font_button,
                    enabled=enabled,
                    hover=hover,
                )
        elif current_scene_id == "ending":
            restart_rect = pygame.Rect(
                START_BUTTON_RECT.x,
                restart_y,
                START_BUTTON_RECT.w,
                START_BUTTON_RECT.h,
            )
            rh = restart_rect.collidepoint(mouse)
            draw_primary_button(
                screen,
                restart_rect,
                "Play again",
                font_cta,
                hover=rh,
                sublabel="Return to title | click or Enter",
                font_sub=font_cta_hint,
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
