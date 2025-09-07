-- Place this LocalScript in StarterPlayerScripts or StarterGui in Roblox Studio
-- This script handles UI updates and sound effects for the hill race game

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local player = Players.LocalPlayer

-- UI Setup
local screenGui = Instance.new("ScreenGui")
screenGui.Name = "HillRaceUI"
screenGui.Parent = player:WaitForChild("PlayerGui")

local leaderboardFrame = Instance.new("Frame")
leaderboardFrame.Size = UDim2.new(0, 250, 0, 180)
leaderboardFrame.Position = UDim2.new(1, -260, 0, 20)
leaderboardFrame.BackgroundTransparency = 0.3
leaderboardFrame.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
leaderboardFrame.Parent = screenGui

local leaderboardTitle = Instance.new("TextLabel")
leaderboardTitle.Size = UDim2.new(1, 0, 0, 30)
leaderboardTitle.BackgroundTransparency = 1
leaderboardTitle.Text = "🏆 Leaderboard"
leaderboardTitle.TextColor3 = Color3.new(1,1,0.5)
leaderboardTitle.Font = Enum.Font.SourceSansBold
leaderboardTitle.TextSize = 22
leaderboardTitle.Parent = leaderboardFrame

local leaderboardList = Instance.new("Frame")
leaderboardList.Size = UDim2.new(1, 0, 1, -30)
leaderboardList.Position = UDim2.new(0, 0, 0, 30)
leaderboardList.BackgroundTransparency = 1
leaderboardList.Parent = leaderboardFrame

-- Sound Setup
local treasureSound = Instance.new("Sound")
treasureSound.SoundId = "rbxassetid://1843529632" -- Example sound asset
 treasureSound.Volume = 1
treasureSound.Parent = screenGui

local powerUpSound = Instance.new("Sound")
powerUpSound.SoundId = "rbxassetid://12222242" -- Example sound asset
powerUpSound.Volume = 1
powerUpSound.Parent = screenGui

-- Helper to update leaderboard UI
def updateLeaderboardUI(leaderboardData)
	for _, child in ipairs(leaderboardList:GetChildren()) do
		if child:IsA("TextLabel") then child:Destroy() end
	end
	for i, entry in ipairs(leaderboardData) do
		local userId = entry.userId or entry[1]
		local score = entry.score or entry[2]
		local name = "Player" .. tostring(userId)
		local playerObj = Players:GetPlayerByUserId(userId)
		if playerObj then name = playerObj.Name end
		local label = Instance.new("TextLabel")
		label.Size = UDim2.new(1, 0, 0, 28)
		label.Position = UDim2.new(0, 0, 0, (i-1)*28)
		label.BackgroundTransparency = 1
		label.Text = i .. ". " .. name .. " - " .. tostring(score)
		label.TextColor3 = Color3.new(1,1,1)
		label.Font = Enum.Font.SourceSans
		label.TextSize = 20
		label.Parent = leaderboardList
	end
end

-- Listen for leaderboard updates
local SharedEvents = ReplicatedStorage:WaitForChild("SharedEvents")
local leaderboardEvent = SharedEvents:FindFirstChild("LeaderboardUpdated")
if leaderboardEvent then
	leaderboardEvent.OnClientEvent:Connect(function(leaderboardData)
		updateLeaderboardUI(leaderboardData)
	end)
end

-- Listen for treasure and power-up collection
local treasureEvent = SharedEvents:FindFirstChild("TreasureCollected")
if treasureEvent then
	treasureEvent.OnClientEvent:Connect(function()
		treasureSound:Play()
	end)
end

local powerUpEvent = SharedEvents:FindFirstChild("PowerUpCollected")
if powerUpEvent then
	powerUpEvent.OnClientEvent:Connect(function(player, powerUpType)
		powerUpSound:Play()
		-- Optionally show a notification
		local notif = Instance.new("TextLabel")
		notif.Size = UDim2.new(0, 200, 0, 40)
		notif.Position = UDim2.new(0.5, -100, 0.2, 0)
		notif.BackgroundTransparency = 0.3
		notif.BackgroundColor3 = Color3.fromRGB(0, 180, 255)
		notif.Text = "Power-Up: " .. tostring(powerUpType)
		notif.TextColor3 = Color3.new(1,1,1)
		notif.Font = Enum.Font.SourceSansBold
		notif.TextSize = 24
		notif.Parent = screenGui
		game:GetService("Debris"):AddItem(notif, 2)
	end)
end
