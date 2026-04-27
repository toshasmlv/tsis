# NOTE: Using SQLite instead of PostgreSQL due to
# UnicodeDecodeError with psycopg2 on Windows
# (Cyrillic characters in user profile path).
# The schema and queries are identical.

import pygame
import sys
import json
import os
from config import *
from game   import GameState, build_walls
from db     import init_db, save_session, get_top10, get_personal_best

# ── settings helpers ──────────────────────────
SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "snake_color": [0, 200, 0],
    "grid":        False,
    "sound":       True,
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
        for k, v in DEFAULT_SETTINGS.items():
            data.setdefault(k, v)
        return data
    return dict(DEFAULT_SETTINGS)

def save_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)

# ── UI helpers ────────────────────────────────
def draw_bg(surf, W, H):
    surf.fill(DARK_BG)
    for y in range(0, H, 40):
        pygame.draw.line(surf, (20, 20, 35), (0, y), (W, y))

def button(surf, text, rect, color=GRAY, text_color=WHITE, font=None):
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)
    col = tuple(min(255, c + 40) for c in color) if hovered else color
    pygame.draw.rect(surf, col, rect, border_radius=8)
    pygame.draw.rect(surf, ACCENT, rect, 2, border_radius=8)
    if font is None:
        font = pygame.font.SysFont("Verdana", 16, bold=True)
    lbl = font.render(text, True, text_color)
    surf.blit(lbl, lbl.get_rect(center=rect.center))
    return hovered

# ── screens ───────────────────────────────────
def username_screen(surf, clock, W, H):
    font_big  = pygame.font.SysFont("Verdana", 30, bold=True)
    font_med  = pygame.font.SysFont("Verdana", 18)
    font_hint = pygame.font.SysFont("Verdana", 13)
    name = ""
    btn  = pygame.Rect(W//2 - 70, 380, 140, 44)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip():
                    return name.strip()
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif len(name) < 16 and event.unicode.isprintable():
                    name += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn.collidepoint(event.pos) and name.strip():
                    return name.strip()

        draw_bg(surf, W, H)
        t = font_big.render("ENTER YOUR NAME", True, ACCENT)
        surf.blit(t, t.get_rect(center=(W//2, 180)))

        box = pygame.Rect(W//2 - 140, 280, 280, 48)
        pygame.draw.rect(surf, (30, 30, 50), box, border_radius=6)
        pygame.draw.rect(surf, ACCENT, box, 2, border_radius=6)
        nt = font_med.render(name + "|", True, WHITE)
        surf.blit(nt, nt.get_rect(midleft=(box.left + 10, box.centery)))

        button(surf, "START", btn, GREEN)
        hint = font_hint.render("Press Enter or click START", True, LIGHT_GRAY)
        surf.blit(hint, hint.get_rect(center=(W//2, 440)))

        pygame.display.flip()
        clock.tick(60)


def main_menu(surf, clock, W, H):
    font_title = pygame.font.SysFont("Verdana", 48, bold=True)
    btns = {
        "Play":        pygame.Rect(W//2-75, 220, 150, 48),
        "Leaderboard": pygame.Rect(W//2-100, 285, 200, 48),
        "Settings":    pygame.Rect(W//2-75, 350, 150, 48),
        "Quit":        pygame.Rect(W//2-75, 415, 150, 48),
    }
    colors = {"Play": GREEN, "Leaderboard": BLUE,
              "Settings": GRAY, "Quit": RED}

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for name, rect in btns.items():
                    if rect.collidepoint(event.pos):
                        return name

        draw_bg(surf, W, H)
        t = font_title.render("SNAKE", True, GREEN)
        surf.blit(t, t.get_rect(center=(W//2, 130)))

        for name, rect in btns.items():
            button(surf, name, rect, colors[name])

        pygame.display.flip()
        clock.tick(60)


def leaderboard_screen(surf, clock, W, H):
    font_big = pygame.font.SysFont("Verdana", 26, bold=True)
    font_med = pygame.font.SysFont("Verdana", 15)
    font_sm  = pygame.font.SysFont("Verdana", 13)
    back_btn = pygame.Rect(W//2-70, H-70, 140, 44)

    try:
        entries = get_top10()
    except Exception:
        entries = []

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.collidepoint(event.pos):
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        draw_bg(surf, W, H)
        t = font_big.render("TOP 10 LEADERBOARD", True, GOLD)
        surf.blit(t, t.get_rect(center=(W//2, 50)))

        header = font_sm.render(
            f"{'#':<3} {'Name':<14} {'Score':>6} {'Lvl':>4} {'Date':>8}",
            True, LIGHT_GRAY)
        surf.blit(header, (40, 90))
        pygame.draw.line(surf, LIGHT_GRAY, (40, 110), (W-40, 110))

        for i, (name, score, level, date) in enumerate(entries[:10]):
            col  = GOLD if i == 0 else (LIGHT_GRAY if i < 3 else WHITE)
            date_str = date if date else "N/A"
            row  = font_med.render(
                f"{i+1:<3} {name[:13]:<14} {score:>6} {level:>4} {date_str:>8}",
                True, col)
            surf.blit(row, (40, 120 + i * 34))

        if not entries:
            no = font_med.render("No scores yet!", True, LIGHT_GRAY)
            surf.blit(no, no.get_rect(center=(W//2, 300)))

        button(surf, "Back", back_btn, GRAY)
        pygame.display.flip()
        clock.tick(60)


def settings_screen(surf, clock, W, H, settings):
    font_big = pygame.font.SysFont("Verdana", 26, bold=True)
    font_med = pygame.font.SysFont("Verdana", 17)

    COLOR_OPTIONS = [
        ("Green",  [0, 200, 0]),
        ("Blue",   [50, 100, 220]),
        ("Red",    [220, 50, 50]),
        ("Yellow", [240, 220, 0]),
        ("White",  [220, 220, 220]),
    ]
    color_idx = 0
    cur = settings.get("snake_color", [0,200,0])
    for i, (_, c) in enumerate(COLOR_OPTIONS):
        if c == cur:
            color_idx = i

    grid_btn  = pygame.Rect(W//2+20, 230, 110, 36)
    sound_btn = pygame.Rect(W//2+20, 290, 110, 36)
    color_btn = pygame.Rect(W//2+20, 350, 110, 36)
    save_btn  = pygame.Rect(W//2-70, H-80, 140, 44)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if grid_btn.collidepoint(event.pos):
                    settings["grid"] = not settings.get("grid", False)
                if sound_btn.collidepoint(event.pos):
                    settings["sound"] = not settings.get("sound", True)
                if color_btn.collidepoint(event.pos):
                    color_idx = (color_idx + 1) % len(COLOR_OPTIONS)
                    settings["snake_color"] = COLOR_OPTIONS[color_idx][1]
                if save_btn.collidepoint(event.pos):
                    save_settings(settings)
                    return settings

        draw_bg(surf, W, H)
        t = font_big.render("SETTINGS", True, ACCENT)
        surf.blit(t, t.get_rect(center=(W//2, 120)))

        rows = [
            ("Grid overlay", "ON" if settings.get("grid") else "OFF",   grid_btn,  BLUE),
            ("Sound",        "ON" if settings.get("sound", True) else "OFF", sound_btn, BLUE),
            ("Snake color",  COLOR_OPTIONS[color_idx][0],               color_btn, tuple(COLOR_OPTIONS[color_idx][1])),
        ]
        for label, val, rect, col in rows:
            lbl = font_med.render(label, True, WHITE)
            surf.blit(lbl, (W//2 - 160, rect.centery - 10))
            button(surf, val, rect, col)

        button(surf, "Save & Back", save_btn, GREEN)
        pygame.display.flip()
        clock.tick(60)


def game_over_screen(surf, clock, W, H, score, level, personal_best):
    font_big = pygame.font.SysFont("Verdana", 36, bold=True)
    font_med = pygame.font.SysFont("Verdana", 19)
    retry_btn = pygame.Rect(W//2-140, 420, 120, 46)
    menu_btn  = pygame.Rect(W//2+20,  420, 120, 46)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_btn.collidepoint(event.pos):
                    return "retry"
                if menu_btn.collidepoint(event.pos):
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "retry"
                if event.key == pygame.K_q:
                    return "menu"

        draw_bg(surf, W, H)
        go = font_big.render("GAME OVER", True, RED)
        surf.blit(go, go.get_rect(center=(W//2, 160)))

        lines = [
            (f"Score:         {score}",        WHITE),
            (f"Level reached: {level}",         WHITE),
            (f"Personal best: {personal_best}", GOLD),
        ]
        for i, (text, col) in enumerate(lines):
            lbl = font_med.render(text, True, col)
            surf.blit(lbl, lbl.get_rect(center=(W//2, 260 + i*50)))

        button(surf, "Retry",     retry_btn, GREEN)
        button(surf, "Main Menu", menu_btn,  BLUE)
        pygame.display.flip()
        clock.tick(60)


# ── main entry ────────────────────────────────
def main():
    pygame.init()

    W = CELL * COLS
    H = CELL * ROWS + 40   # 40px HUD

    surf  = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Snake — TSIS 4")
    clock = pygame.time.Clock()

    font     = pygame.font.SysFont("Verdana", 16, bold=True)
    font_sm  = pygame.font.SysFont("Verdana", 11)

    # init DB
    try:
        init_db()
        db_ok = True
    except Exception as e:
        print(f"DB error: {e}")
        db_ok = False

    settings = load_settings()
    walls    = build_walls()
    username = None

    while True:
        choice = main_menu(surf, clock, W, H)

        if choice == "Quit":
            pygame.quit(); sys.exit()

        elif choice == "Leaderboard":
            leaderboard_screen(surf, clock, W, H)

        elif choice == "Settings":
            settings = settings_screen(surf, clock, W, H, settings)

        elif choice == "Play":
            if username is None:
                username = username_screen(surf, clock, W, H)

            personal_best = 0
            if db_ok:
                try:
                    personal_best = get_personal_best(username)
                except Exception:
                    pass

            result = "retry"
            while result == "retry":
                gs = GameState(walls, settings, personal_best)

                # game loop
                outcome = "ok"
                while outcome == "ok":
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit(); sys.exit()
                        if event.type == pygame.KEYDOWN:
                            gs.handle_key(event.key)

                    outcome = gs.update()
                    gs.draw(surf, 40, font, font_sm)
                    pygame.display.flip()
                    clock.tick(gs.speed)

                # save to DB
                if db_ok:
                    try:
                        save_session(username, gs.score, gs.level)
                        personal_best = max(personal_best, gs.score)
                    except Exception as e:
                        print(f"Save error: {e}")

                result = game_over_screen(
                    surf, clock, W, H,
                    gs.score, gs.level, personal_best)


if __name__ == "__main__":
    main()