import pygame
import random
from config import *


def cell_rect(col, row, info_h):
    return pygame.Rect(col * CELL, info_h + row * CELL, CELL, CELL)


def build_walls():
    walls = set()
    for c in range(COLS):
        walls.add((c, 0))
        walls.add((c, ROWS - 1))
    for r in range(ROWS):
        walls.add((0, r))
        walls.add((COLS - 1, r))
    return walls


def spawn_food(walls, snake, obstacles, existing_foods, food_type=None):
    occupied = walls | set(snake) | obstacles | existing_foods
    free = [
        (c, r)
        for c in range(1, COLS - 1)
        for r in range(1, ROWS - 1)
        if (c, r) not in occupied
    ]
    if not free:
        return None, "normal"
    if food_type is None:
        food_type = random.choices(
            ["normal", "gold", "purple", "poison"],
            weights=[55, 20, 10, 15]
        )[0]
    return random.choice(free), food_type


def spawn_powerup(walls, snake, obstacles, existing_foods):
    occupied = walls | set(snake) | obstacles | existing_foods
    free = [
        (c, r)
        for c in range(1, COLS - 1)
        for r in range(1, ROWS - 1)
        if (c, r) not in occupied
    ]
    if not free:
        return None, None
    kind = random.choice(list(POWERUP_TYPES.keys()))
    return random.choice(free), kind


def spawn_obstacles(walls, snake, count):
    """Place obstacle blocks that don't trap the snake."""
    occupied = walls | set(snake)
    # keep a safe zone around snake head
    hx, hy = snake[0]
    safe = {(hx + dx, hy + dy) for dx in range(-3, 4) for dy in range(-3, 4)}
    free = [
        (c, r)
        for c in range(1, COLS - 1)
        for r in range(1, ROWS - 1)
        if (c, r) not in occupied and (c, r) not in safe
    ]
    random.shuffle(free)
    return set(free[:count])


def reset_game(walls, level=1):
    snake     = [(5, 5), (4, 5), (3, 5)]
    direction = RIGHT
    obstacles = set()
    foods     = {}   # pos -> (food_type, spawn_time)
    pos, ftype = spawn_food(walls, snake, obstacles, set(foods.keys()))
    if pos:
        foods[pos] = (ftype, pygame.time.get_ticks())
    score  = 0
    eaten  = 0
    speed  = BASE_SPEED + (level - 1) * SPEED_STEP
    # place obstacles if level >= 3
    if level >= OBSTACLE_START_LEVEL:
        obstacles = spawn_obstacles(walls, snake,
                                    OBSTACLES_PER_LEVEL * (level - 2))
    return snake, direction, foods, obstacles, score, eaten, speed


class GameState:
    def __init__(self, walls, settings, personal_best=0, start_level=1):
        self.walls         = walls
        self.settings      = settings
        self.personal_best = personal_best
        self.level         = start_level

        (self.snake, self.direction, self.foods,
         self.obstacles, self.score,
         self.eaten, self.speed) = reset_game(walls, start_level)

        self.next_dir      = self.direction
        self.active_pu     = None   # current power-up kind
        self.pu_end_time   = 0
        self.field_pu      = None   # (pos, kind, spawn_time) or None
        self.shield_ready  = False
        self.shield_used   = False

    def handle_key(self, key):
        if key == pygame.K_UP    and self.direction != DOWN:  self.next_dir = UP
        if key == pygame.K_DOWN  and self.direction != UP:    self.next_dir = DOWN
        if key == pygame.K_LEFT  and self.direction != RIGHT: self.next_dir = LEFT
        if key == pygame.K_RIGHT and self.direction != LEFT:  self.next_dir = RIGHT

    def update(self):
        """Advance one game tick. Returns 'dead' or 'ok'."""
        now = pygame.time.get_ticks()
        self.direction = self.next_dir

        # ── expire food ───────────────────────
        expired = [p for p, (ft, st) in self.foods.items()
                   if now - st > FOOD_TYPES[ft]["time"]]
        for p in expired:
            del self.foods[p]

        # spawn a new food if none exist
        if not self.foods:
            pos, ft = spawn_food(self.walls, self.snake,
                                 self.obstacles, set(self.foods.keys()))
            if pos:
                self.foods[pos] = (ft, now)

        # ── spawn / expire power-up on field ──
        if self.field_pu is None and random.random() < 0.002:
            pos, kind = spawn_powerup(
                self.walls, self.snake,
                self.obstacles, set(self.foods.keys()))
            if pos:
                self.field_pu = (pos, kind, now)
        if self.field_pu and now - self.field_pu[2] > POWERUP_FIELD_TIME:
            self.field_pu = None

        # ── expire active power-up effect ─────
        if self.active_pu and self.active_pu != "shield":
            if now > self.pu_end_time:
                self.active_pu = None

        # ── move snake ────────────────────────
        head     = self.snake[0]
        new_head = (head[0] + self.direction[0],
                    head[1] + self.direction[1])

        # collision checks
        hit_wall = new_head in self.walls
        hit_self = new_head in self.snake
        hit_obs  = new_head in self.obstacles

        if hit_wall or hit_self or hit_obs:
            if self.active_pu == "shield" and not self.shield_used:
                self.shield_used = True
                self.active_pu   = None
                # bounce back — just don't move
                return "ok"
            return "dead"

        self.snake.insert(0, new_head)

        # ── eat food ──────────────────────────
        if new_head in self.foods:
            ft, _ = self.foods.pop(new_head)
            if ft == "poison":
                # shorten by 2
                for _ in range(2):
                    if len(self.snake) > 1:
                        self.snake.pop()
                if len(self.snake) <= 1:
                    return "dead"
            else:
                pts = FOOD_TYPES[ft]["points"]
                self.score += pts
                self.eaten += 1
                if self.eaten >= FOOD_PER_LEVEL:
                    self.level += 1
                    self.eaten  = 0
                    self.speed  = min(BASE_SPEED + (self.level - 1) * SPEED_STEP, 30)
                    # add obstacles on new level
                    if self.level >= OBSTACLE_START_LEVEL:
                        new_obs = spawn_obstacles(
                            self.walls, self.snake,
                            OBSTACLES_PER_LEVEL * (self.level - 2))
                        self.obstacles |= new_obs
            # spawn replacement food
            pos, nft = spawn_food(self.walls, self.snake,
                                  self.obstacles, set(self.foods.keys()))
            if pos:
                self.foods[pos] = (nft, pygame.time.get_ticks())
        else:
            self.snake.pop()

        # ── collect power-up ──────────────────
        if self.field_pu and new_head == self.field_pu[0]:
            kind = self.field_pu[1]
            self.field_pu  = None
            self.active_pu = kind
            self.shield_used = False
            if kind == "speed":
                self.speed    = min(self.speed + 4, 30)
                self.pu_end_time = now + POWERUP_EFFECT_TIME
            elif kind == "slow":
                self.speed    = max(self.speed - 3, 3)
                self.pu_end_time = now + POWERUP_EFFECT_TIME
            elif kind == "shield":
                pass   # lasts until triggered

        return "ok"

    def draw(self, screen, info_h, font, font_small):
        snake_color = tuple(self.settings.get("snake_color", list(GREEN)))
        snake_dark  = tuple(max(0, c - 60) for c in snake_color)

        screen.fill(DARK_BG)

        # grid overlay
        if self.settings.get("grid", False):
            for c in range(COLS):
                for r in range(ROWS):
                    pygame.draw.rect(screen, (25, 25, 40),
                                     cell_rect(c, r, info_h), 1)

        # walls
        for (c, r) in self.walls:
            pygame.draw.rect(screen, WALL_COLOR, cell_rect(c, r, info_h))

        # obstacles
        for (c, r) in self.obstacles:
            pygame.draw.rect(screen, (120, 80, 40), cell_rect(c, r, info_h))
            pygame.draw.rect(screen, (80, 50, 20),  cell_rect(c, r, info_h), 2)

        # foods
        now = pygame.time.get_ticks()
        for pos, (ft, st) in self.foods.items():
            color = FOOD_TYPES[ft]["color"]
            # flash when about to expire
            time_left = FOOD_TYPES[ft]["time"] - (now - st)
            if time_left < 2000 and (now // 200) % 2 == 0:
                color = WHITE
            pygame.draw.ellipse(screen, color, cell_rect(*pos, info_h))

        # power-up on field
        if self.field_pu:
            fpos, fkind, _ = self.field_pu
            pcol = POWERUP_TYPES[fkind]["color"]
            plbl = POWERUP_TYPES[fkind]["label"]
            pygame.draw.rect(screen, pcol, cell_rect(*fpos, info_h), border_radius=4)
            lbl = font_small.render(plbl, True, BLACK)
            r   = cell_rect(*fpos, info_h)
            screen.blit(lbl, lbl.get_rect(center=r.center))

        # snake
        for i, (c, r) in enumerate(self.snake):
            col = snake_dark if i == 0 else snake_color
            pygame.draw.rect(screen, col, cell_rect(c, r, info_h))
            pygame.draw.rect(screen, BLACK, cell_rect(c, r, info_h), 1)

        # shield ring around head
        if self.active_pu == "shield":
            hx, hy = self.snake[0]
            cr = cell_rect(hx, hy, info_h)
            pygame.draw.rect(screen, BLUE, cr.inflate(6, 6), 3)

        # HUD
        pygame.draw.rect(screen, BLACK, (0, 0, COLS * CELL, info_h))
        sc  = font.render(f"Score: {self.score}", True, WHITE)
        lv  = font.render(f"Level: {self.level}", True, GOLD)
        pb  = font.render(f"Best: {self.personal_best}", True, LIGHT_GRAY)
        screen.blit(sc,  (10, 10))
        screen.blit(lv,  (COLS * CELL // 2 - lv.get_width() // 2, 10))
        screen.blit(pb,  (COLS * CELL - pb.get_width() - 10, 10))

        # active power-up indicator
        if self.active_pu:
            now2 = pygame.time.get_ticks()
            if self.active_pu != "shield":
                secs = max(0, (self.pu_end_time - now2) // 1000)
                txt  = f"[{self.active_pu.upper()} {secs}s]"
            else:
                txt = "[SHIELD]"
            col  = POWERUP_TYPES[self.active_pu]["color"]
            pu_s = font.render(txt, True, col)
            screen.blit(pu_s, pu_s.get_rect(center=(COLS * CELL // 2, info_h + 20)))