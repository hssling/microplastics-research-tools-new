local ObstacleSpawner = {}


local Constants = require(game.ReplicatedStorage.Constants)
local obstacleTypes = Constants.OBSTACLE_TYPES
local powerUpTypes = Constants.POWERUP_TYPES
local spawnInterval = 2 -- seconds
local powerUpInterval = 8 -- seconds
local hillModel = game.Workspace.HillModel


function ObstacleSpawner.spawnObstacle()
    local obstacle = Instance.new("Model")
    obstacle.Name = obstacleTypes[math.random(1, #obstacleTypes)]
    obstacle.Parent = hillModel
    local randomX = math.random(-50, 50)
    local randomZ = math.random(-50, 50)
    if hillModel.PrimaryPart then
        obstacle:SetPrimaryPartCFrame(hillModel.PrimaryPart.CFrame * CFrame.new(randomX, 5, randomZ))
    end
end

-- New: Power-up spawning
function ObstacleSpawner.spawnPowerUp()
    local powerUp = Instance.new("Part")
    powerUp.Name = powerUpTypes[math.random(1, #powerUpTypes)]
    powerUp.Size = Vector3.new(2,2,2)
    powerUp.BrickColor = BrickColor.Random()
    powerUp.Anchored = true
    powerUp.CanCollide = true
    powerUp.Parent = hillModel
    local randomX = math.random(-50, 50)
    local randomZ = math.random(-50, 50)
    if hillModel.PrimaryPart then
        powerUp.Position = hillModel.PrimaryPart.Position + Vector3.new(randomX, 5, randomZ)
    end
end

function ObstacleSpawner.configureObstacleSettings(settings)
    spawnInterval = settings.spawnInterval or spawnInterval
end


function ObstacleSpawner.startSpawning()
    spawn(function()
        while true do
            ObstacleSpawner.spawnObstacle()
            wait(spawnInterval)
        end
    end)
    spawn(function()
        while true do
            ObstacleSpawner.spawnPowerUp()
            wait(powerUpInterval)
        end
    end)
end

return ObstacleSpawner