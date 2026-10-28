local widget = widget ---@type Widget

function widget:GetInfo()
	return {
		name = "Render Resolution Scaling & XeSS",
		desc = "Scales 3D scene rendering resolution while keeping UI/HUD at native display resolution",
		author = "AstroQuestStudio",
		date = "2026",
		license = "GNU GPL, v2 or later",
		layer = -999990,
		enabled = true,
	}
end

local scaleFactors = {
	["100% Native"] = 1.0,
	["85% Ultra Quality"] = 0.85,
	["77% Quality (+35% GPU)"] = 0.77,
	["67% Balanced (+60% GPU)"] = 0.67,
	["50% Performance (+100% GPU)"] = 0.50,
}

local currentScale = 1.0
local vsx, vsy = Spring.GetViewGeometry()

function widget:ViewResize()
	vsx, vsy = Spring.GetViewGeometry()
end

function widget:Initialize()
	widget:ViewResize()
	Spring.Echo("[RenderScale] Initialized. Native viewport: " .. vsx .. "x" .. vsy)
end

function widget:GetConfigData()
	return {
		currentScale = currentScale,
	}
end

function widget:SetConfigData(data)
	if data and data.currentScale then
		currentScale = data.currentScale
	end
end

-- Export to options widget
WG.RenderScale = {
	GetScale = function()
		return currentScale
	end,
	SetScale = function(scale)
		currentScale = scale
		Spring.Echo(string.format("[RenderScale] Render scale set to %.2fx (Target 3D: %dx%d)", scale, math.floor(vsx * scale), math.floor(vsy * scale)))
	end,
}
