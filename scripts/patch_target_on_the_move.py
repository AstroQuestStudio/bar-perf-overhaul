path = r'c:\Users\trufa\Documents\BAR\Beyond-All-Reason\luarules\gadgets\unit_target_on_the_move.lua'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """\tfunction gadget:GameFrame(frame)
\t\tteamQueryCaches = {}
\t\tif frame % 15 == 0 then"""

replacement = """\tfunction gadget:GameFrame(frame)
\t\tfor allyTeam, teamCache in pairs(teamQueryCaches) do
\t\t\tfor hash in pairs(teamCache) do
\t\t\t\tteamCache[hash] = nil
\t\t\tend
\t\tend
\t\tif frame % 15 == 0 then"""

assert target in content, "target not found in unit_target_on_the_move.lua"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Pristine replacement applied to unit_target_on_the_move.lua!")
