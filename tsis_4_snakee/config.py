# Database connection settings
# Change PASSWORD to the password you set during PostgreSQL installation
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "snake_db",
    "user":     "postgres",
    "password": "1234",   # <-- change this to your password
}

# Game grid
CELL = 20
COLS = 30
ROWS = 30

# Colors
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = (0,   200, 0)
DARK_GREEN = (0,   140, 0)
RED        = (220, 0,   0)
DARK_RED   = (120, 0,   0)
GRAY       = (40,  40,  40)
LIGHT_GRAY = (160, 160, 160)
WALL_COLOR = (80,  80,  80)
GOLD       = (255, 215, 0)
PURPLE     = (180, 0,   180)
ORANGE     = (255, 140, 0)
BLUE       = (50,  100, 220)
CYAN       = (0,   220, 220)
DARK_BG    = (15,  15,  25)
ACCENT     = (255, 180, 0)

# Directions
UP    = (0,  -1)
DOWN  = (0,   1)
LEFT  = (-1,  0)
RIGHT = (1,   0)

# Food types
FOOD_TYPES = {
    "normal":  {"color": RED,      "points": 10, "time": 8000},
    "gold":    {"color": GOLD,     "points": 30, "time": 5000},
    "purple":  {"color": PURPLE,   "points": 50, "time": 3000},
    "poison":  {"color": DARK_RED, "points":  0, "time": 6000},
}

# Level settings
FOOD_PER_LEVEL = 3
BASE_SPEED     = 8
SPEED_STEP     = 2

# Power-up durations (ms)
POWERUP_FIELD_TIME = 8000   # disappears from field after 8s
POWERUP_EFFECT_TIME = 5000  # effect lasts 5s

POWERUP_TYPES = {
    "speed":  {"color": ORANGE, "label": "SPD"},
    "slow":   {"color": CYAN,   "label": "SLO"},
    "shield": {"color": BLUE,   "label": "SHD"},
}

# Obstacles start at level 3
OBSTACLE_START_LEVEL = 3
OBSTACLES_PER_LEVEL  = 5