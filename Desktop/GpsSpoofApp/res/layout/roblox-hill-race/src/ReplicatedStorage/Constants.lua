local Constants = {}


Constants.OBSTACLE_TYPES = {
    "Rock",
    "Pitfall",
    "Mud",
    "Log",
    "Spike"
}

-- New: Power-up types
Constants.POWERUP_TYPES = {
    "SpeedBoost",
    "Shield",
    "DoublePoints"
}

-- New: Leaderboard settings
Constants.LEADERBOARD_SIZE = 5 -- Show top 5 players

Constants.TREASURE_LOCATION = Vector3.new(0, 50, 0) -- Example coordinates for treasure location

Constants.RACE_DURATION = 300 -- Duration of the race in seconds
Constants.PLAYER_COUNT_LIMIT = 10 -- Maximum number of players allowed in a race

return Constants