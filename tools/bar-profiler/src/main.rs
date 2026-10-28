use std::env;
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::path::Path;
use flate2::read::GzDecoder;
use byteorder::{LittleEndian, ReadBytesExt};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct DemoMetadata {
    pub engine_version: String,
    pub unix_timestamp: i64,
    pub script_size: u32,
    pub demo_stream_size: u32,
    pub map_name: String,
    pub game_name: String,
    pub num_players: usize,
    pub total_chunks: usize,
    pub estimated_duration_sec: f32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FramePacingStats {
    pub total_packets: usize,
    pub chunks_analyzed: usize,
    pub max_chunk_bytes: usize,
    pub avg_chunk_bytes: f64,
}

fn extract_script_value(script: &str, key: &str) -> String {
    for line in script.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with(key) {
            if let Some(pos) = trimmed.find('=') {
                let val = trimmed[pos + 1..].trim().trim_end_matches(';');
                return val.to_string();
            }
        }
    }
    String::new()
}

fn parse_demo(path: &Path) -> Result<(), Box<dyn std::error::Error>> {
    println!("\x1b[1;36m==================================================\x1b[0m");
    println!("\x1b[1;32m  BAR Demo & Performance Profiler (Rust Edition)\x1b[0m");
    println!("\x1b[1;36m==================================================\x1b[0m");
    println!("Analyzing: {}", path.display());

    let file = File::open(path)?;
    let mut gz = GzDecoder::new(file);

    // Read magic (16 bytes)
    let mut magic = [0u8; 16];
    gz.read_exact(&mut magic)?;
    let magic_str = String::from_utf8_lossy(&magic);
    if !magic_str.starts_with("spring demofile") {
        return Err("Not a valid Spring/Recoil demo file".into());
    }

    let version = gz.read_u32::<LittleEndian>()?;
    let header_size = gz.read_u32::<LittleEndian>()?;

    let mut version_buf = [0u8; 256];
    gz.read_exact(&mut version_buf)?;
    let engine_version = version_buf
        .split(|&b| b == 0)
        .next()
        .map(|s| String::from_utf8_lossy(s).to_string())
        .unwrap_or_default();

    let mut game_id = [0u8; 16];
    gz.read_exact(&mut game_id)?;

    let unix_time = gz.read_i64::<LittleEndian>()?;
    let script_size = gz.read_u32::<LittleEndian>()?;
    let demo_stream_size = gz.read_u32::<LittleEndian>()?;
    let game_time = gz.read_f32::<LittleEndian>()?;
    let wallclock_time = gz.read_f32::<LittleEndian>()?;

    // Skip remaining header bytes
    let read_so_far = 16 + 8 + 256 + 16 + 24;
    if header_size > read_so_far {
        let skip = (header_size - read_so_far) as usize;
        let mut skip_buf = vec![0u8; skip];
        gz.read_exact(&mut skip_buf)?;
    }

    // Read script
    let mut script_buf = vec![0u8; script_size as usize];
    gz.read_exact(&mut script_buf)?;
    let script_str = String::from_utf8_lossy(&script_buf);

    let map_name = extract_script_value(&script_str, "mapname");
    let game_name = extract_script_value(&script_str, "gametype");
    let num_players = script_str.matches("[player").count();

    println!("\n\x1b[1mMatch Setup:\x1b[0m");
    println!("  • Engine Version : {}", engine_version);
    println!("  • Map Name       : {}", if map_name.is_empty() { "Unknown" } else { &map_name });
    println!("  • Game / Mod     : {}", if game_name.is_empty() { "Beyond All Reason" } else { &game_name });
    println!("  • Players count  : {}", num_players);
    println!("  • Demo Stream    : {:.2} MB", demo_stream_size as f64 / 1_048_576.0);

    // Read stream chunks
    let mut total_chunks = 0;
    let mut total_bytes = 0usize;
    let mut max_chunk_len = 0usize;
    let mut last_time = 0.0f32;

    while let Ok(chunk_time) = gz.read_f32::<LittleEndian>() {
        let chunk_len = match gz.read_u32::<LittleEndian>() {
            Ok(len) => len as usize,
            Err(_) => break,
        };

        if chunk_len == 0 || chunk_len > 10_000_000 {
            break;
        }

        let mut chunk_buf = vec![0u8; chunk_len];
        if gz.read_exact(&mut chunk_buf).is_err() {
            break;
        }

        total_chunks += 1;
        total_bytes += chunk_len;
        if chunk_len > max_chunk_len {
            max_chunk_len = chunk_len;
        }
        last_time = chunk_time;
    }

    let avg_chunk = if total_chunks > 0 { total_bytes as f64 / total_chunks as f64 } else { 0.0 };

    println!("\n\x1b[1mSimulation & Pacing Stream:\x1b[0m");
    println!("  • Total Chunks    : {}", total_chunks);
    println!("  • Peak Chunk Size : {} bytes", max_chunk_len);
    println!("  • Avg Chunk Size  : {:.1} bytes", avg_chunk);
    println!("  • Stream Duration : {:.1}s ({:.1} min)", last_time, last_time / 60.0);
    println!("\n\x1b[1;32m✓ Replay parsed and validated successfully in Rust!\x1b[0m\n");

    Ok(())
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("Usage: bar-profiler <path_to_demo.sdfz>");
        return;
    }

    let path = Path::new(&args[1]);
    if let Err(e) = parse_demo(path) {
        eprintln!("\x1b[1;31mError analyzing demo: {}\x1b[0m", e);
    }
}
