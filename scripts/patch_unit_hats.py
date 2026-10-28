path = r'c:\Users\trufa\Documents\BAR\Beyond-All-Reason\luarules\gadgets\unit_hats.lua'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """local function UpdateGameFrameCallIn()
\tif spawnAwardsProcessed and next(unitsWearingHats) == nil then
\t\tgadgetHandler:RemoveCallIn("GameFrame")
\telse
\t\tgadgetHandler:UpdateCallIn("GameFrame")
\tend
end"""

replacement = """local function UpdateHatCallIns()
\tlocal hasHats = (next(unitsWearingHats) ~= nil)
\tif spawnAwardsProcessed and not hasHats then
\t\tgadgetHandler:RemoveCallIn("GameFrame")
\telse
\t\tgadgetHandler:UpdateCallIn("GameFrame")
\tend
\tif hasHats then
\t\tgadgetHandler:UpdateCallIn("UnitDamaged")
\t\tgadgetHandler:UpdateCallIn("UnitCloaked")
\t\tgadgetHandler:UpdateCallIn("UnitDecloaked")
\telse
\t\tgadgetHandler:RemoveCallIn("UnitDamaged")
\t\tgadgetHandler:RemoveCallIn("UnitCloaked")
\t\tgadgetHandler:RemoveCallIn("UnitDecloaked")
\tend
end

local UpdateGameFrameCallIn = UpdateHatCallIns

function gadget:Initialize()
\tUpdateHatCallIns()
end"""

assert target in content, "target not found in unit_hats.lua"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Pristine replacement applied to unit_hats.lua!")
