use std::sync::atomic::{AtomicUsize, Ordering};

/// Spatial Grid partition for RTS unit clustering & collision avoidance
#[repr(C)]
pub struct SpatialGrid {
    pub cell_size: f32,
    pub inv_cell_size: f32,
    pub width_cells: usize,
    pub height_cells: usize,
    pub cells: Vec<Vec<u32>>,
    pub unit_positions: Vec<(f32, f32)>,
}

impl SpatialGrid {
    pub fn new(map_width: f32, map_height: f32, cell_size: f32) -> Self {
        let cs = if cell_size <= 0.0 { 128.0 } else { cell_size };
        let w = ((map_width / cs).ceil() as usize).max(1);
        let h = ((map_height / cs).ceil() as usize).max(1);
        let total = w * h;

        Self {
            cell_size: cs,
            inv_cell_size: 1.0 / cs,
            width_cells: w,
            height_cells: h,
            cells: vec![Vec::with_capacity(16); total],
            unit_positions: Vec::with_capacity(4096),
        }
    }

    #[inline(always)]
    fn cell_index(&self, x: f32, z: f32) -> Option<usize> {
        if x < 0.0 || z < 0.0 {
            return None;
        }
        let cx = (x * self.inv_cell_size) as usize;
        let cz = (z * self.inv_cell_size) as usize;
        if cx < self.width_cells && cz < self.height_cells {
            Some(cz * self.width_cells + cx)
        } else {
            None
        }
    }

    pub fn clear(&mut self) {
        for cell in &mut self.cells {
            cell.clear();
        }
        self.unit_positions.clear();
    }

    pub fn insert(&mut self, unit_id: u32, x: f32, z: f32) {
        if let Some(idx) = self.cell_index(x, z) {
            self.cells[idx].push(unit_id);
            let u_idx = unit_id as usize;
            if u_idx >= self.unit_positions.len() {
                self.unit_positions.resize(u_idx + 1, (0.0, 0.0));
            }
            self.unit_positions[u_idx] = (x, z);
        }
    }

    pub fn query_radius(&self, x: f32, z: f32, radius: f32, out: &mut [u32]) -> usize {
        let r2 = radius * radius;
        let min_x = (x - radius).max(0.0);
        let max_x = x + radius;
        let min_z = (z - radius).max(0.0);
        let max_z = z + radius;

        let start_cx = (min_x * self.inv_cell_size) as usize;
        let end_cx = ((max_x * self.inv_cell_size) as usize).min(self.width_cells - 1);
        let start_cz = (min_z * self.inv_cell_size) as usize;
        let end_cz = ((max_z * self.inv_cell_size) as usize).min(self.height_cells - 1);

        let mut count = 0;
        let max_len = out.len();

        for cz in start_cz..=end_cz {
            let row_offset = cz * self.width_cells;
            for cx in start_cx..=end_cx {
                let cell_idx = row_offset + cx;
                for &id in &self.cells[cell_idx] {
                    let u_idx = id as usize;
                    if u_idx < self.unit_positions.len() {
                        let (ux, uz) = self.unit_positions[u_idx];
                        let dx = ux - x;
                        let dz = uz - z;
                        if dx * dx + dz * dz <= r2 {
                            if count < max_len {
                                out[count] = id;
                                count += 1;
                            } else {
                                return count;
                            }
                        }
                    }
                }
            }
        }
        count
    }
}

// ---------------------------------------------------------------------------
// C-ABI Exports for LuaJIT FFI
// ---------------------------------------------------------------------------

static ALLOCATED_GRIDS: AtomicUsize = AtomicUsize::new(0);

#[no_mangle]
pub extern "C" fn bar_perf_core_version() -> u32 {
    100 // v1.0.0
}

#[no_mangle]
pub extern "C" fn bar_spatial_grid_create(map_w: f32, map_h: f32, cell_size: f32) -> *mut SpatialGrid {
    ALLOCATED_GRIDS.fetch_add(1, Ordering::Relaxed);
    Box::into_raw(Box::new(SpatialGrid::new(map_w, map_h, cell_size)))
}

#[no_mangle]
pub extern "C" fn bar_spatial_grid_destroy(grid: *mut SpatialGrid) {
    if !grid.is_null() {
        ALLOCATED_GRIDS.fetch_sub(1, Ordering::Relaxed);
        unsafe {
            drop(Box::from_raw(grid));
        }
    }
}

#[no_mangle]
pub extern "C" fn bar_spatial_grid_clear(grid: *mut SpatialGrid) {
    if let Some(g) = unsafe { grid.as_mut() } {
        g.clear();
    }
}

#[no_mangle]
pub extern "C" fn bar_spatial_grid_insert(grid: *mut SpatialGrid, unit_id: u32, x: f32, z: f32) {
    if let Some(g) = unsafe { grid.as_mut() } {
        g.insert(unit_id, x, z);
    }
}

#[no_mangle]
pub extern "C" fn bar_spatial_grid_query_radius(
    grid: *const SpatialGrid,
    x: f32,
    z: f32,
    radius: f32,
    out_buf: *mut u32,
    out_capacity: usize,
) -> usize {
    if grid.is_null() || out_buf.is_null() || out_capacity == 0 {
        return 0;
    }
    let g = unsafe { &*grid };
    let slice = unsafe { std::slice::from_raw_parts_mut(out_buf, out_capacity) };
    g.query_radius(x, z, radius, slice)
}
