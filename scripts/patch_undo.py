path = r'c:\Users\trufa\Documents\BAR\Beyond-All-Reason\luarules\gadgets\cmd_undo.lua'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """\tfunction gadget:Initialize()
\t\tgadgetHandler:RegisterUnitCommand(CMD.ANY)
\tend"""

replacement = """\tfunction gadget:Initialize()
\t\tgadgetHandler:RegisterUnitCommand(CMD.ANY)
\t\tif not enableAlertEchos and not nullifyFriendlySelfdDgunDamage then
\t\t\tgadgetHandler:RemoveCallIn("UnitPreDamaged")
\t\tend
\tend"""

assert target in content, "target not found in cmd_undo.lua"
content = content.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Pristine replacement applied to cmd_undo.lua!")
