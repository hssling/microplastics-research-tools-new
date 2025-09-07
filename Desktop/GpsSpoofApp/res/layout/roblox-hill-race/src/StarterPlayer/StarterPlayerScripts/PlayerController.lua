local PlayerController = {}

function PlayerController:movePlayer(player, direction)
    local character = player.Character
    if character then
        local humanoid = character:FindFirstChildOfClass("Humanoid")
        if humanoid then
            local moveDirection = Vector3.new(direction.x, 0, direction.z).unit
            humanoid:Move(moveDirection, true)
        end
    end
end

function PlayerController:jump(player)
    local character = player.Character
    if character then
        local humanoid = character:FindFirstChildOfClass("Humanoid")
        if humanoid and humanoid:GetState() == Enum.HumanoidStateType.Freefall then
            humanoid:ChangeState(Enum.HumanoidStateType.Jumping)
        end
    end
end


function PlayerController:interactWithTreasure(player)
    -- Logic for interacting with treasure goes here
    -- Could trigger UI feedback or sound
end

-- New: Power-up interaction
function PlayerController:collectPowerUp(player, powerUpType)
    -- Logic for collecting power-up (e.g., apply effect, show UI, play sound)
    print(player.Name .. " collected power-up: " .. tostring(powerUpType))
    -- Example: show a message or play a sound here
end

-- New: UI polish hook (to be implemented in LocalScript)
function PlayerController:updateLeaderboardUI(leaderboardData)
    -- Update the leaderboard UI for the player
    -- This should be implemented in a LocalScript with ScreenGui
end

return PlayerController