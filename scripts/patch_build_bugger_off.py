path = r'c:\Users\trufa\Documents\BAR\Beyond-All-Reason\luarules\gadgets\cmd_build_bugger_off.lua'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Module-level table pools
target_decl = "local areaCommandCooldown = {}"
replacement_decl = """local areaCommandCooldown = {}

-- Pre-allocated static buffers to avoid GC table churning in GameFrame
local visitedTeams = {}
local visitedUnits = {}
local cylinderCache = {}
local deferRemove = {}
local deferSlow = {}
local deferSlowRemove = {}
local deferWatch = {}"""

assert target_decl in content, "target_decl not found"
content = content.replace(target_decl, replacement_decl, 1)

target_gameframe = """\tlocal visitedTeams = {}
\tlocal visitedUnits = {}
\tlocal cylinderCache = {} -- Cache GetUnitsInCylinder results per location

\tlocal moveParams = insertMoveParams

\t-- Collect deferred actions to avoid modifying tables during pairs() iteration
\tlocal deferRemove = {}
\tlocal deferSlow = {}
\tlocal deferRemoveCount = 0
\tlocal deferSlowCount = 0"""

replacement_gameframe = """\t-- Reuse pooled buffers to prevent GC allocations
\tfor k in pairs(visitedTeams) do visitedTeams[k] = nil end
\tfor k in pairs(visitedUnits) do visitedUnits[k] = nil end
\tfor k in pairs(cylinderCache) do cylinderCache[k] = nil end

\tlocal moveParams = insertMoveParams

\t-- Reset counts for pre-allocated deferred arrays
\tlocal deferRemoveCount = 0
\tlocal deferSlowCount = 0"""

assert target_gameframe in content, "target_gameframe not found"
content = content.replace(target_gameframe, replacement_gameframe, 1)

target_slow = """\tlocal deferSlowRemove = {}
\tlocal deferWatch = {}
\tlocal deferSlowRemoveCount = 0
\tlocal deferWatchCount = 0"""

replacement_slow = """\tlocal deferSlowRemoveCount = 0
\tlocal deferWatchCount = 0"""

assert target_slow in content, "target_slow not found"
content = content.replace(target_slow, replacement_slow, 1)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Pristine replacement applied to cmd_build_bugger_off.lua!")
