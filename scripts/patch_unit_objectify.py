path = r'c:\Users\trufa\Documents\BAR\Beyond-All-Reason\luarules\gadgets\unit_objectify.lua'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target1 = """if gadgetHandler:IsSyncedCode() then
\tlocal numDecorations = 0
\tlocal numObjects = 0

\tfunction gadget:Initialize()
\t\tgadgetHandler:RegisterAllowCommand(CMD.ATTACK)
\t\tgadgetHandler:RegisterAllowCommand(CMD.BUILD)
\t\tfor _, unitID in pairs(Spring.GetAllUnits()) do
\t\t\tgadget:UnitCreated(unitID, spGetUnitDefID(unitID))
\t\tend
\tend"""

replacement1 = """if gadgetHandler:IsSyncedCode() then
\tlocal numDecorations = 0
\tlocal numObjects = 0

\tlocal function updatePreDamagedCallin()
\t\tif (numDecorations + numObjects) > 0 then
\t\t\tgadgetHandler:UpdateCallIn("UnitPreDamaged")
\t\telse
\t\t\tgadgetHandler:RemoveCallIn("UnitPreDamaged")
\t\tend
\tend

\tfunction gadget:Initialize()
\t\tgadgetHandler:RegisterAllowCommand(CMD.ATTACK)
\t\tgadgetHandler:RegisterAllowCommand(CMD.BUILD)
\t\tfor _, unitID in pairs(Spring.GetAllUnits()) do
\t\t\tgadget:UnitCreated(unitID, spGetUnitDefID(unitID))
\t\tend
\t\tupdatePreDamagedCallin()
\tend"""

assert target1 in content, "target1 not found"
content = content.replace(target1, replacement1, 1)

target2 = """\tfunction gadget:UnitDestroyed(unitID, unitDefID, unitTeam, attackerID, attackerDefID, attackerTeam, weaponDefID)
\t\tif isDecoration[unitDefID] then
\t\t\tnumDecorations = numDecorations - 1
\t\tend
\t\tif isObject[unitDefID] then
\t\t\tnumObjects = numObjects - 1
\t\tend
\tend

\tfunction gadget:UnitCreated(unitID, unitDefID, teamID, builderID)
\t\tif isDecoration[unitDefID] then
\t\t\tnumDecorations = numDecorations + 1
\t\t\tdecorationUnit(unitID)
\t\tend
\t\tif isObject[unitDefID] then
\t\t\tnumObjects = numObjects + 1
\t\t\tobjectifyUnit(unitID)
\t\tend
\tend"""

replacement2 = """\tfunction gadget:UnitDestroyed(unitID, unitDefID, unitTeam, attackerID, attackerDefID, attackerTeam, weaponDefID)
\t\tif isDecoration[unitDefID] then
\t\t\tnumDecorations = numDecorations - 1
\t\t\tupdatePreDamagedCallin()
\t\tend
\t\tif isObject[unitDefID] then
\t\t\tnumObjects = numObjects - 1
\t\t\tupdatePreDamagedCallin()
\t\tend
\tend

\tfunction gadget:UnitCreated(unitID, unitDefID, teamID, builderID)
\t\tif isDecoration[unitDefID] then
\t\t\tnumDecorations = numDecorations + 1
\t\t\tdecorationUnit(unitID)
\t\t\tupdatePreDamagedCallin()
\t\tend
\t\tif isObject[unitDefID] then
\t\t\tnumObjects = numObjects + 1
\t\t\tobjectifyUnit(unitID)
\t\t\tupdatePreDamagedCallin()
\t\tend
\tend"""

assert target2 in content, "target2 not found"
content = content.replace(target2, replacement2, 1)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Pristine replacement applied to unit_objectify.lua!")
