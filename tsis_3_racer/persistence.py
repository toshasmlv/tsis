import json, os

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE    = "settings.json"

DEFAULT_SETTINGS = {
    "sound":      True,
    "car_color":  "RED",
    "difficulty": "Normal",
}

# ── leaderboard ──────────────────────────────
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    return []

def save_leaderboard(entries):
    entries.sort(key=lambda e: e["score"], reverse=True)
    entries = entries[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(entries, f, indent=2)
    return entries

def add_entry(name, score, distance):
    entries = load_leaderboard()
    entries.append({"name": name, "score": score, "distance": int(distance)})
    return save_leaderboard(entries)

# ── settings ─────────────────────────────────
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        # fill missing keys with defaults
        for k, v in DEFAULT_SETTINGS.items():
            data.setdefault(k, v)
        return data
    return dict(DEFAULT_SETTINGS)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)