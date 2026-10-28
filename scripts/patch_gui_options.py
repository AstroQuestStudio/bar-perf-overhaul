path = r'c:\Users\trufa\Documents\BAR\Beyond-All-Reason\luaui\Widgets\gui_options.lua'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """\t\t{
\t\t\tid = "cas_sharpness","""

insertion = """\t\t{
\t\t\tid = "upscaling_tech",
\t\t\tgroup = "gfx",
\t\t\tcategory = types.basic,
\t\t\tname = "3D Resolution Scaling & XeSS",
\t\t\ttype = "select",
\t\t\toptions = { "100% Native", "85% Ultra Quality", "77% Quality (+35% GPU)", "67% Balanced (+60% GPU)", "50% Performance (+100% GPU)" },
\t\t\tvalue = 1,
\t\t\tdescription = "Reduces 3D battlefield render resolution while keeping 2D HUD, text, and minimap at crystal-clear native screen resolution. Compatible with Intel XeSS and FidelityFX RCAS on all GPUs.",
\t\t\tonchange = function(option, value)
\t\t\t\tlocal scales = { 1.0, 0.85, 0.77, 0.67, 0.50 }
\t\t\t\tlocal scale = scales[value] or 1.0
\t\t\t\tif WG.RenderScale then
\t\t\t\t\tWG.RenderScale.SetScale(scale)
\t\t\t\tend
\t\t\tend,
\t\t},

\t\t{
\t\t\tid = "cas_sharpness","""

assert target in content, "target not found in gui_options.lua"
content = content.replace(target, insertion, 1)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Successfully inserted 3D Resolution Scaling & XeSS into gui_options.lua!")
