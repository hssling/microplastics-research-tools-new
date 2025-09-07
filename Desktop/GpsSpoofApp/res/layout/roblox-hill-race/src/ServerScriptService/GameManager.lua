local GameManager = {}

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SharedEvents = require(ReplicatedStorage:WaitForChild("SharedEvents"))


local raceActive = false
local playerData = {}

-- New: Leaderboard data
local leaderboard = {}

-- New: Power-up tracking
local playerPowerUps = {}


function GameManager:startRace()
    if not raceActive then
        raceActive = true
        playerData = {}
        leaderboard = {}
        playerPowerUps = {}
        for _, player in ipairs(Players:GetPlayers()) do
            playerData[player.UserId] = {hasTreasure = false, score = 0}
            leaderboard[player.UserId] = 0
            playerPowerUps[player.UserId] = {}
            SharedEvents.PlayerJoined:Fire(player)
        end
        SharedEvents.RaceStarted:Fire()
    end
end


function GameManager:endRace()
    if raceActive then
        raceActive = false
        -- Sort leaderboard
        local sorted = {}
        for userId, score in pairs(leaderboard) do
            table.insert(sorted, {userId = userId, score = score})
        end
        table.sort(sorted, function(a, b) return a.score > b.score end)
        SharedEvents.LeaderboardUpdated:Fire(sorted)
        SharedEvents.RaceEnded:Fire(playerData)
    end
end


function GameManager:checkForTreasure(player)
    if playerData[player.UserId] and not playerData[player.UserId].hasTreasure then
        playerData[player.UserId].hasTreasure = true
        -- Award points for treasure
        leaderboard[player.UserId] = (leaderboard[player.UserId] or 0) + 10
        SharedEvents.TreasureCollected:Fire(player)
        SharedEvents.LeaderboardUpdated:Fire(leaderboard)
    end
end

-- New: Power-up collection
function GameManager:collectPowerUp(player, powerUpType)
    if not playerPowerUps[player.UserId] then
        playerPowerUps[player.UserId] = {}
    end
    table.insert(playerPowerUps[player.UserId], powerUpType)
    -- Award points for power-up
    leaderboard[player.UserId] = (leaderboard[player.UserId] or 0) + 2
    SharedEvents.PowerUpCollected:Fire(player, powerUpType)
    SharedEvents.LeaderboardUpdated:Fire(leaderboard)
end

return GameManager