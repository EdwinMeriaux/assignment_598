//! Offline visibility precomputation. Students do not need Rust.
use rayon::prelude::*;
use serde_json::json;
use std::{collections::BTreeMap, env, fs::File, io::BufWriter};

fn clear(a: (i32, i32), b: (i32, i32), pixels: &[u8], width: usize) -> bool {
    let (mut x, mut y) = a;
    let (dx, dy) = ((b.0 - x).abs(), (b.1 - y).abs());
    let (sx, sy) = (if x < b.0 { 1 } else { -1 }, if y < b.1 { 1 } else { -1 });
    let mut err = dx - dy;
    loop {
        if pixels[y as usize * width + x as usize] == 0 { return false; }
        if (x, y) == b { return true; }
        let twice = 2 * err;
        if twice > -dy { err -= dy; x += sx; }
        if twice < dx { err += dx; y += sy; }
    }
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = env::args_os().collect();
    if args.len() != 3 {
        return Err("Usage: cadence_visibility INPUT.png OUTPUT.json".into());
    }
    let img = image::open(&args[1])?.to_luma8();
    let (width, height) = img.dimensions();
    let pixels = img.into_raw();
    if pixels.iter().any(|&v| v != 0 && v != 255) {
        return Err("Map must contain only black (0) and white (255) pixels.".into());
    }
    let all: Vec<_> = (0..height as i32).flat_map(|y| (0..width as i32).map(move |x| (x, y))).collect();
    let free: Vec<_> = all.iter().copied().filter(|&(x,y)| pixels[y as usize * width as usize + x as usize] != 0).collect();
    let blocked: Vec<_> = all.iter().copied().filter(|p| !free.contains(p)).collect();
    let mut data: BTreeMap<String, serde_json::Value> = free.par_iter().map(|&a| {
        // Checking both directions makes raster visibility mutual at Bresenham ties.
        let visible: Vec<_> = free.iter().copied().filter(|&b|
            clear(a, b, &pixels, width as usize) && clear(b, a, &pixels, width as usize)
        ).collect();
        (format!("({}, {})", a.0, a.1), json!(visible))
    }).collect();
    for &(x, y) in &blocked { data.insert(format!("({}, {})", x, y), json!([])); }
    data.insert("all".into(), json!(all));
    data.insert("blocked".into(), json!(blocked));
    serde_json::to_writer(BufWriter::new(File::create(&args[2])?), &data)?;
    println!("Generated {}x{} visibility data ({} free cells).", width, height, free.len());
    Ok(())
}

fn main() {
    if let Err(error) = run() { eprintln!("{error}"); std::process::exit(1); }
}
