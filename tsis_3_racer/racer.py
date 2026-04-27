import pygame, random
from pygame.locals import *

SW, SH = 400, 600

WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
GRAY   = (160, 160, 160)
RED    = (220, 50,  50)
GREEN  = (50,  200, 80)
BLUE   = (50,  100, 220)
GOLD   = (255, 215, 0)
ORANGE = (255, 140, 0)
YELLOW = (240, 230, 0)

CAR_COLOR_MAP = {
    "RED":   (180, 0,   0),
    "BLUE":  (0,   80,  200),
    "GREEN": (0,   160, 60),
    "WHITE": (220, 220, 220),
}

LANE_XS = [80, 160, 240, 320]


def lane_x():
    return random.choice(LANE_XS)

def safe_y(player_rect, margin=120):
    return random.randint(-300, player_rect.top - margin)


# ── Scrolling road ────────────────────────────
class Road:
    def __init__(self):
        raw       = pygame.image.load("AnimatedStreet.png")
        self.img  = pygame.transform.scale(raw, (SW, SH))
        self.y1   = 0
        self.y2   = -SH
        self.speed = 5

    def update(self):
        self.y1 += self.speed
        self.y2 += self.speed
        if self.y1 >= SH:
            self.y1 = self.y2 - SH
        if self.y2 >= SH:
            self.y2 = self.y1 - SH

    def draw(self, surf):
        surf.blit(self.img, (0, self.y1))
        surf.blit(self.img, (0, self.y2))


# ── Player ────────────────────────────────────
class Player(pygame.sprite.Sprite):
    def __init__(self, color_name="RED"):
        super().__init__()
        raw            = pygame.image.load("Player.png")
        self.image     = pygame.transform.scale(raw, (50, 80))
        self.rect      = self.image.get_rect(center=(SW // 2, 500))
        self.color_tag = CAR_COLOR_MAP.get(color_name, (180, 0, 0))
        self.shield    = False
        self.nitro     = False

    def update(self, keys):
        spd = 8 if self.nitro else 5
        if keys[K_LEFT]  and self.rect.left   > 20:      self.rect.x -= spd
        if keys[K_RIGHT] and self.rect.right  < SW - 20: self.rect.x += spd
        if keys[K_UP]    and self.rect.top    > SH // 2: self.rect.y -= spd
        if keys[K_DOWN]  and self.rect.bottom < SH - 10: self.rect.y += spd

    def draw_extras(self, surf):
        if self.shield:
            pygame.draw.circle(surf, (100, 180, 255), self.rect.center, 42, 3)


# ── Enemy ─────────────────────────────────────
class Enemy(pygame.sprite.Sprite):
    _img_cache = None

    def __init__(self, speed, player_rect):
        super().__init__()
        if Enemy._img_cache is None:
            raw = pygame.image.load("Enemy.png")
            Enemy._img_cache = pygame.transform.scale(raw, (50, 80))
        self.image = Enemy._img_cache.copy()
        self.speed = speed + random.uniform(-0.5, 1.5)
        self.rect  = self.image.get_rect(center=(lane_x(), safe_y(player_rect)))

    def update(self, road_speed):
        self.rect.y += self.speed + road_speed * 0.3
        if self.rect.top > SH + 20:
            self.kill()


# ── Coin ─────────────────────────────────────
class Coin(pygame.sprite.Sprite):
    def __init__(self, speed, player_rect, value=1):
        super().__init__()
        self.value = value
        r   = 10 + value * 2
        col = GOLD if value == 1 else (200,200,200) if value == 2 else (180,100,0)
        self.image = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, col, (r, r), r)
        if value > 1:
            lbl = pygame.font.SysFont("Verdana", 10, bold=True).render(str(value), True, BLACK)
            self.image.blit(lbl, lbl.get_rect(center=(r, r)))
        self.rect  = self.image.get_rect(center=(lane_x(), safe_y(player_rect, 60)))
        self.speed = speed

    def update(self, road_speed):
        self.rect.y += self.speed + road_speed * 0.2
        if self.rect.top > SH + 20:
            self.kill()


# ── Obstacle ─────────────────────────────────
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, speed, player_rect):
        super().__init__()
        self.kind  = random.choice(["oil", "pothole", "barrier"])
        self.image, self.effect = self._make()
        self.rect  = self.image.get_rect(center=(lane_x(), safe_y(player_rect)))
        self.speed = speed

    def _make(self):
        if self.kind == "oil":
            s = pygame.Surface((50, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (30, 30, 120, 200), (0, 0, 50, 30))
            lbl = pygame.font.SysFont("Verdana", 9).render("OIL", True, WHITE)
            s.blit(lbl, lbl.get_rect(center=(25, 15)))
            return s, "slow"
        elif self.kind == "pothole":
            s = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(s, (25, 25, 25), (18, 18), 18)
            pygame.draw.circle(s, (60, 40, 20), (18, 18), 12)
            return s, "damage"
        else:
            s = pygame.Surface((60, 20), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 80, 0), (0, 0, 60, 20), border_radius=4)
            pygame.draw.rect(s, WHITE,        (0, 0, 60, 20), 2, border_radius=4)
            lbl = pygame.font.SysFont("Verdana", 9).render("STOP", True, WHITE)
            s.blit(lbl, lbl.get_rect(center=(30, 10)))
            return s, "damage"

    def update(self, road_speed):
        self.rect.y += self.speed + road_speed * 0.2
        if self.rect.top > SH + 20:
            self.kill()


# ── Nitro strip ──────────────────────────────
class NitroStrip(pygame.sprite.Sprite):
    def __init__(self, speed, player_rect):
        super().__init__()
        w = SW - 40
        self.image = pygame.Surface((w, 18), pygame.SRCALPHA)
        for i in range(0, w, 20):
            col = ORANGE if (i // 20) % 2 == 0 else YELLOW
            pygame.draw.rect(self.image, col, (i, 0, 20, 18))
        lbl = pygame.font.SysFont("Verdana", 10, bold=True).render("NITRO BOOST", True, BLACK)
        self.image.blit(lbl, lbl.get_rect(center=(w // 2, 9)))
        self.rect  = self.image.get_rect(topleft=(20, safe_y(player_rect, 80)))
        self.speed = speed
        self.timer = 240

    def update(self, road_speed):
        self.rect.y += self.speed + road_speed * 0.2
        self.timer  -= 1
        if self.rect.top > SH + 20 or self.timer <= 0:
            self.kill()


# ── Power-up ──────────────────────────────────
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, speed, player_rect):
        super().__init__()
        self.kind  = random.choice(["nitro", "shield", "repair"])
        self.image = self._make()
        self.rect  = self.image.get_rect(center=(lane_x(), safe_y(player_rect, 80)))
        self.speed = speed
        self.timer = 300

    def _make(self):
        s = pygame.Surface((38, 38), pygame.SRCALPHA)
        if self.kind == "nitro":
            pygame.draw.polygon(s, ORANGE, [(19,2),(36,36),(2,36)])
            letter, tc = "N", BLACK
        elif self.kind == "shield":
            pygame.draw.circle(s, BLUE, (19, 19), 19)
            letter, tc = "S", WHITE
        else:
            pygame.draw.rect(s, GREEN, (0, 0, 38, 38), border_radius=8)
            letter, tc = "R", BLACK
        lbl = pygame.font.SysFont("Verdana", 14, bold=True).render(letter, True, tc)
        s.blit(lbl, lbl.get_rect(center=(19, 19)))
        return s

    def update(self, road_speed):
        self.rect.y += self.speed + road_speed * 0.2
        self.timer  -= 1
        if self.rect.top > SH + 20 or self.timer <= 0:
            self.kill()