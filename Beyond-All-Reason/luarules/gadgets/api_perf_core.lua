local gadget = gadget ---@type Gadget

function gadget:GetInfo()
	return {
		name = "Perf Core FFI Bridge",
		desc = "Batch memory and SIMD acceleration via Rust bar_perf_core",
		author = "AstroQuestStudio",
		date = "2026",
		license = "GPL v2",
		layer = -999999, -- Run very early
		enabled = true,
	}
end

if not gadgetHandler:IsSyncedCode() then
	return
end

local ffi = require("ffi")

-- Define C types
ffi.cdef[[
	typedef struct {
		uint32_t id;
		float x, y, z;
		float vx, vz;
		float hp, max_hp;
		uint16_t team_id;
		uint16_t def_id;
		uint32_t flags;
	} UnitStatePacked;

	typedef struct {
		uint32_t id;
		float x, y, z;
		float radius;
		float damage;
		uint16_t team_id;
		uint16_t weapon_def_id;
	} ProjectileInput;

	typedef struct {
		uint32_t projectile_id;
		uint32_t target_unit_id;
		float damage;
		float hit_distance;
	} BatchHitResult;

	uint32_t bar_perf_core_version();
	void* bar_batch_manager_create(float map_w, float map_h, float cell_size);
	void bar_batch_manager_destroy(void* mgr);
	void bar_batch_update_units(void* mgr, const UnitStatePacked* states, size_t count);
	size_t bar_batch_query_radius(const void* mgr, float x, float z, float radius, int32_t team_filter, uint32_t* out_ids, size_t out_cap);
	size_t bar_batch_check_projectile_hits(const void* mgr, const ProjectileInput* projs, size_t proj_count, BatchHitResult* out_hits, size_t max_hits);
]]

local perfLib = nil
local mgr = nil

local function loadLib()
	local paths = {
		"bar_perf_core.dll",
		"target/release/bar_perf_core.dll",
		"crates/bar-perf-core/bar_perf_core.dll",
		"libbar_perf_core.so",
	}
	for _, p in ipairs(paths) do
		local ok, lib = pcall(ffi.load, p)
		if ok and lib then
			return lib
		end
	end
	return nil
end

local MAX_UNITS = 16384
local unitBuffer = ffi.new("UnitStatePacked[?]", MAX_UNITS)
local queryBuffer = ffi.new("uint32_t[?]", 1024)
local hitBuffer = ffi.new("BatchHitResult[?]", 4096)

-- Public GG Interface
GG.PerfCore = {
	isAvailable = false,
	version = 0,
}

function gadget:Initialize()
	perfLib = loadLib()
	if perfLib then
		local ver = perfLib.bar_perf_core_version()
		mgr = perfLib.bar_batch_manager_create(Game.mapSizeX, Game.mapSizeZ, 128.0)
		GG.PerfCore.isAvailable = true
		GG.PerfCore.version = ver
		Spring.Echo(string.format("[PerfCore] Rust DOD Acceleration loaded successfully! (v%d)", ver))
	else
		Spring.Echo("[PerfCore] Rust native core not found, fallback to standard engine path.")
	end
end

function gadget:Shutdown()
	if perfLib and mgr then
		perfLib.bar_batch_manager_destroy(mgr)
		mgr = nil
	end
end

-- Fast Batch Query Export
function GG.PerfCore.QueryRadius(x, z, radius, teamFilter, outTable)
	if not mgr then
		return 0
	end
	local filter = teamFilter or -1
	local count = perfLib.bar_batch_query_radius(mgr, x, z, radius, filter, queryBuffer, 1024)
	if outTable then
		for i = 0, count - 1 do
			outTable[i + 1] = queryBuffer[i]
		end
	end
	return count
end
