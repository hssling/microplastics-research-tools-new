
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local SharedEvents = {}

SharedEvents.PlayerJoined = Instance.new("RemoteEvent")
SharedEvents.PlayerJoined.Name = "PlayerJoined"
SharedEvents.PlayerJoined.Parent = ReplicatedStorage

SharedEvents.TreasureCollected = Instance.new("RemoteEvent")
SharedEvents.TreasureCollected.Name = "TreasureCollected"
SharedEvents.TreasureCollected.Parent = ReplicatedStorage

-- New: Leaderboard update event
SharedEvents.LeaderboardUpdated = Instance.new("RemoteEvent")
SharedEvents.LeaderboardUpdated.Name = "LeaderboardUpdated"
SharedEvents.LeaderboardUpdated.Parent = ReplicatedStorage

-- New: Power-up collected event
SharedEvents.PowerUpCollected = Instance.new("RemoteEvent")
SharedEvents.PowerUpCollected.Name = "PowerUpCollected"
SharedEvents.PowerUpCollected.Parent = ReplicatedStorage

return SharedEvents