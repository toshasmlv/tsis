import pygame, sys, random
from pygame.locals import *

from racer       import (Road, Player, Enemy, Coin, Obstacle,
                         NitroStrip, PowerUp, SW, SH)
from ui          import (main_menu, username_screen, settings_screen,
                         leaderboard_screen, game_over_screen)
from persistence import load_settings, add_entry

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GRAY   = (160, 160, 160)
RED    = (220, 50,  50)
GREEN  = (50,  200, 80)
BLUE   = (50,  100, 220)
GOLD   = (255, 215, 0)
ORANGE = (255, 140, 0)

DIFF_CONFIG = {
    "Easy":   {"road_speed": 4, "enemy_extra": 0,   "spawn_obs": 0.004},
    "Normal": {"road_speed": 5, "enemy_extra": 0.5, "spawn_obs": 0.008},
    "Hard":   {"road_speed": 7, "enemy_extra": 1.0, "spawn_obs": 0.015},
}

def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None

def play_bg(use_sound):
    if use_sound:
        try:
            pygame.mixer.music.load("background.wav")
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

def stop_bg():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass

def play_crash(use_sound, crash_sound):
    if use_sound and crash_sound:
        crash_sound.play()


def run_game(surf, clock, username, settings, crash_sound):
    font_med = pygame.font.SysFont("Verdana", 16, bold=True)
    font_sm  = pygame.font.SysFont("Verdana", 13)

    diff    = DIFF_CONFIG[settings.get("difficulty", "Normal")]
    use_snd = settings.get("sound", True)
    car_col = settings.get("car_color", "RED")

    play_bg(use_snd)

    road        = Road()
    road.speed  = diff["road_speed"]
    player      = Player(car_col)

    all_sprites  = pygame.sprite.Group(player)
    enemies      = pygame.sprite.Group()
    coins        = pygame.sprite.Group()
    obstacles    = pygame.sprite.Group()
    powerups     = pygame.sprite.Group()
    nitro_strips = pygame.sprite.Group()

    score    = 0
    coins_n  = 0
    distance = 0.0
    frame    = 0

    active_pu      = None
    pu_frames_left = 0
    NITRO_DUR      = 300
    SHIELD_DUR     = 600
    slow_frames    = 0

    base_enemy_speed = 4 + diff["enemy_extra"]
    enemy_count      = 1
    spawn_obs        = diff["spawn_obs"]

    while True:
        frame += 1
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == QUIT:
                stop_bg(); pygame.quit(); sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                stop_bg()
                return "menu", score, distance, coins_n

        if frame % 600 == 0:
            road.speed       = min(road.speed + 0.5, 14)
            base_enemy_speed = min(base_enemy_speed + 0.3, 12)
            spawn_obs        = min(spawn_obs + 0.001, 0.03)
        if frame % 1800 == 0:
            enemy_count = min(enemy_count + 1, 5)

        cur_spd = road.speed if slow_frames <= 0 else road.speed * 0.4

        if len(enemies) < enemy_count and random.random() < 0.02:
            e = Enemy(base_enemy_speed, player.rect)
            enemies.add(e); all_sprites.add(e)

        if random.random() < 0.015:
            v = random.choices([1, 2, 3], [70, 20, 10])[0]
            c = Coin(cur_spd, player.rect, v)
            coins.add(c); all_sprites.add(c)

        if random.random() < spawn_obs:
            o = Obstacle(cur_spd, player.rect)
            obstacles.add(o); all_sprites.add(o)

        if random.random() < 0.004 and active_pu is None:
            p = PowerUp(cur_spd, player.rect)
            powerups.add(p); all_sprites.add(p)

        if random.random() < 0.003:
            ns = NitroStrip(cur_spd, player.rect)
            nitro_strips.add(ns); all_sprites.add(ns)

        player.nitro  = (active_pu == "nitro")
        player.shield = (active_pu == "shield")
        player.update(keys)
        road.update()
        enemies.update(cur_spd)
        coins.update(cur_spd)
        obstacles.update(cur_spd)
        powerups.update(cur_spd)
        nitro_strips.update(cur_spd)
        distance += cur_spd / 60.0

        if active_pu in ("nitro", "shield"):
            pu_frames_left -= 1
            if pu_frames_left <= 0:
                active_pu = None
        if slow_frames > 0:
            slow_frames -= 1

        for c in pygame.sprite.spritecollide(player, coins, True):
            coins_n += c.value

        for pu in pygame.sprite.spritecollide(player, powerups, True):
            if active_pu is None:
                active_pu = pu.kind
                pu_frames_left = NITRO_DUR if pu.kind == "nitro" else SHIELD_DUR

        if pygame.sprite.spritecollide(player, nitro_strips, True) and active_pu is None:
            active_pu      = "nitro"
            pu_frames_left = NITRO_DUR

        for o in pygame.sprite.spritecollide(player, obstacles, True):
            if player.shield:
                active_pu = None
            elif o.effect == "slow":
                slow_frames = 180
            else:
                play_crash(use_snd, crash_sound)
                stop_bg()
                return "dead", score, distance, coins_n

        if pygame.sprite.spritecollideany(player, enemies):
            if player.shield:
                active_pu = None
                for e in enemies:
                    if e.rect.colliderect(player.rect):
                        e.rect.y -= 100
            else:
                play_crash(use_snd, crash_sound)
                stop_bg()
                return "dead", score, distance, coins_n

        score = int(coins_n * 10 + distance * 2)

        road.draw(surf)
        all_sprites.draw(surf)
        player.draw_extras(surf)

        surf.blit(font_med.render(f"Score: {score}", True, WHITE), (10, 10))
        co = font_med.render(f"Coins: {coins_n}", True, GOLD)
        surf.blit(co, (SW - co.get_width() - 10, 10))
        surf.blit(font_sm.render(f"Dist: {int(distance)} m", True, GRAY), (10, 34))
        sp = font_sm.render(f"Speed: {road.speed:.1f}", True, GRAY)
        surf.blit(sp, (SW - sp.get_width() - 10, 34))

        if active_pu:
            secs = pu_frames_left // 60 if active_pu in ("nitro", "shield") else 0
            col  = ORANGE if active_pu=="nitro" else (100,150,255) if active_pu=="shield" else GREEN
            pu_lbl = font_med.render(
                f"[{active_pu.upper()}]" + (f" {secs}s" if secs else ""), True, col)
            surf.blit(pu_lbl, pu_lbl.get_rect(center=(SW//2, 20)))

        if slow_frames > 0:
            sl = font_sm.render("SLOW!", True, (100, 100, 255))
            surf.blit(sl, sl.get_rect(center=(SW//2, 44)))

        pygame.display.flip()
        clock.tick(60)


def main():
    pygame.init()
    pygame.mixer.init()

    surf  = pygame.display.set_mode((SW, SH))
    pygame.display.set_caption("Racer — TSIS 3")
    clock = pygame.time.Clock()

    crash_sound = load_sound("crash.wav")
    settings    = load_settings()
    username    = None

    while True:
        choice = main_menu(surf, clock)

        if choice == "Quit":
            pygame.quit(); sys.exit()
        elif choice == "Leaderboard":
            leaderboard_screen(surf, clock)
        elif choice == "Settings":
            settings = settings_screen(surf, clock)
        elif choice == "Play":
            if username is None:
                username = username_screen(surf, clock)

            result = "retry"
            while result == "retry":
                outcome, score, distance, coins_n = run_game(
                    surf, clock, username, settings, crash_sound)
                add_entry(username, score, distance)
                if outcome == "dead":
                    result = game_over_screen(surf, clock, score, distance, coins_n)
                else:
                    result = "menu"


if __name__ == "__main__":
    main()