import pygame
from persistence import load_leaderboard, load_settings, save_settings

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GRAY   = (180, 180, 180)
DGRAY  = (80,  80,  80)
RED    = (220, 50,  50)
GREEN  = (50,  200, 80)
BLUE   = (50,  100, 220)
GOLD   = (255, 215, 0)
DARK   = (20,  20,  30)
ACCENT = (255, 180, 0)

SW, SH = 400, 600


def draw_bg(surf):
    surf.fill(DARK)
    for y in range(0, SH, 40):
        pygame.draw.line(surf, (30, 30, 45), (0, y), (SW, y))


def button(surf, text, rect, color=DGRAY, text_color=WHITE, font=None):
    """Draw a rounded button. Returns True if mouse is hovering."""
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my)
    col = tuple(min(255, c + 40) for c in color) if hovered else color
    pygame.draw.rect(surf, col, rect, border_radius=8)
    pygame.draw.rect(surf, ACCENT, rect, 2, border_radius=8)
    if font is None:
        font = pygame.font.SysFont("Verdana", 18, bold=True)
    lbl = font.render(text, True, text_color)
    surf.blit(lbl, lbl.get_rect(center=rect.center))
    return hovered


# ── username entry screen ────────────────────
def username_screen(surf, clock):
    font_big  = pygame.font.SysFont("Verdana", 32, bold=True)
    font_med  = pygame.font.SysFont("Verdana", 20)
    font_hint = pygame.font.SysFont("Verdana", 14)
    name = ""
    btn  = pygame.Rect(130, 380, 140, 44)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
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

        draw_bg(surf)
        t = font_big.render("ENTER NAME", True, ACCENT)
        surf.blit(t, t.get_rect(center=(SW//2, 180)))

        # input box
        box = pygame.Rect(60, 280, 280, 48)
        pygame.draw.rect(surf, (40, 40, 60), box, border_radius=6)
        pygame.draw.rect(surf, ACCENT, box, 2, border_radius=6)
        nt = font_med.render(name + "|", True, WHITE)
        surf.blit(nt, nt.get_rect(midleft=(box.left + 10, box.centery)))

        button(surf, "START", btn, GREEN)
        hint = font_hint.render("Press Enter or click START", True, GRAY)
        surf.blit(hint, hint.get_rect(center=(SW//2, 440)))

        pygame.display.flip()
        clock.tick(60)


# ── main menu ────────────────────────────────
def main_menu(surf, clock):
    font_title = pygame.font.SysFont("Verdana", 42, bold=True)
    btns = {
        "Play":        pygame.Rect(125, 220, 150, 48),
        "Leaderboard": pygame.Rect(100, 285, 200, 48),
        "Settings":    pygame.Rect(125, 350, 150, 48),
        "Quit":        pygame.Rect(125, 415, 150, 48),
    }
    colors = {"Play": GREEN, "Leaderboard": BLUE,
              "Settings": DGRAY, "Quit": RED}

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN:
                for name, rect in btns.items():
                    if rect.collidepoint(event.pos):
                        return name

        draw_bg(surf)
        t = font_title.render("RACER", True, ACCENT)
        surf.blit(t, t.get_rect(center=(SW//2, 130)))
        sub = pygame.font.SysFont("Verdana", 16).render("Dodge · Collect · Survive", True, GRAY)
        surf.blit(sub, sub.get_rect(center=(SW//2, 175)))

        for name, rect in btns.items():
            button(surf, name, rect, colors[name])

        pygame.display.flip()
        clock.tick(60)


# ── settings screen ──────────────────────────
def settings_screen(surf, clock):
    settings  = load_settings()
    font_big  = pygame.font.SysFont("Verdana", 28, bold=True)
    font_med  = pygame.font.SysFont("Verdana", 18)

    CAR_COLORS  = ["RED", "BLUE", "GREEN", "WHITE"]
    DIFFICULTIES = ["Easy", "Normal", "Hard"]

    back_btn = pygame.Rect(130, 500, 140, 44)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # sound toggle
                if pygame.Rect(240, 190, 100, 36).collidepoint(mx, my):
                    settings["sound"] = not settings["sound"]
                    save_settings(settings)
                # car color
                if pygame.Rect(240, 265, 100, 36).collidepoint(mx, my):
                    idx = (CAR_COLORS.index(settings["car_color"]) + 1) % len(CAR_COLORS)
                    settings["car_color"] = CAR_COLORS[idx]
                    save_settings(settings)
                # difficulty
                if pygame.Rect(240, 340, 100, 36).collidepoint(mx, my):
                    idx = (DIFFICULTIES.index(settings["difficulty"]) + 1) % len(DIFFICULTIES)
                    settings["difficulty"] = DIFFICULTIES[idx]
                    save_settings(settings)
                # back
                if back_btn.collidepoint(mx, my):
                    return settings

        draw_bg(surf)
        t = font_big.render("SETTINGS", True, ACCENT)
        surf.blit(t, t.get_rect(center=(SW//2, 120)))

        rows = [
            ("Sound",      "ON" if settings["sound"] else "OFF", 190),
            ("Car Color",  settings["car_color"],                 265),
            ("Difficulty", settings["difficulty"],                340),
        ]
        for label, val, y in rows:
            lbl = font_med.render(label, True, WHITE)
            surf.blit(lbl, (60, y + 8))
            button(surf, val, pygame.Rect(240, y, 100, 36), BLUE)

        button(surf, "Back", back_btn, DGRAY)
        pygame.display.flip()
        clock.tick(60)


# ── leaderboard screen ───────────────────────
def leaderboard_screen(surf, clock):
    font_big  = pygame.font.SysFont("Verdana", 28, bold=True)
    font_med  = pygame.font.SysFont("Verdana", 16)
    font_sm   = pygame.font.SysFont("Verdana", 14)
    back_btn  = pygame.Rect(130, 530, 140, 44)
    entries   = load_leaderboard()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.collidepoint(event.pos):
                    return

        draw_bg(surf)
        t = font_big.render("LEADERBOARD", True, GOLD)
        surf.blit(t, t.get_rect(center=(SW//2, 60)))

        header = font_sm.render(f"{'#':<3} {'Name':<14} {'Score':>7} {'Dist':>7}", True, GRAY)
        surf.blit(header, (30, 105))
        pygame.draw.line(surf, GRAY, (30, 125), (370, 125))

        for i, e in enumerate(entries[:10]):
            col  = GOLD if i == 0 else (GRAY if i < 3 else WHITE)
            rank = f"{i+1:<3}"
            name = e.get("name", "?")[:13]
            row  = font_med.render(
                f"{rank} {name:<14} {e['score']:>7} {e['distance']:>6}m", True, col)
            surf.blit(row, (30, 135 + i * 36))

        if not entries:
            no = font_med.render("No scores yet!", True, GRAY)
            surf.blit(no, no.get_rect(center=(SW//2, 300)))

        button(surf, "Back", back_btn, DGRAY)
        pygame.display.flip()
        clock.tick(60)


# ── game over screen ─────────────────────────
def game_over_screen(surf, clock, score, distance, coins):
    font_big = pygame.font.SysFont("Verdana", 36, bold=True)
    font_med = pygame.font.SysFont("Verdana", 20)
    retry_btn = pygame.Rect(60,  440, 120, 46)
    menu_btn  = pygame.Rect(220, 440, 120, 46)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN:
                if retry_btn.collidepoint(event.pos):
                    return "retry"
                if menu_btn.collidepoint(event.pos):
                    return "menu"

        draw_bg(surf)
        go = font_big.render("GAME OVER", True, RED)
        surf.blit(go, go.get_rect(center=(SW//2, 160)))

        lines = [
            (f"Score:    {score}",    WHITE),
            (f"Distance: {int(distance)} m", WHITE),
            (f"Coins:    {coins}",    GOLD),
        ]
        for i, (text, col) in enumerate(lines):
            lbl = font_med.render(text, True, col)
            surf.blit(lbl, lbl.get_rect(center=(SW//2, 270 + i * 46)))

        button(surf, "Retry",     retry_btn, GREEN)
        button(surf, "Main Menu", menu_btn,  BLUE)
        pygame.display.flip()
        clock.tick(60)