use pyo3::prelude::*;
use rosu_pp::DifficultyAttributes::Osu;
use rosu_pp::{Beatmap, BeatmapExt};
use std::{collections::BTreeMap, fs::File};

#[pyfunction]
#[pyo3(text_signature = "(file_path, count_100, count_50, count_miss, combo, mods, /)")]
fn calculate_pp_with_counts(
    file_path: &str,
    count_100: usize,
    count_50: usize,
    count_miss: usize,
    combo: usize,
    mods: usize,
) -> PyResult<f64> {
    let file = match File::open(file_path) {
        Ok(file) => file,
        Err(why) => panic!("Could not open file: {}", why),
    };

    // Parse the map yourself
    let map = match Beatmap::parse(file) {
        Ok(map) => map,
        Err(why) => panic!("Error while parsing map: {}", why),
    };

    let result = map
        .pp()
        .mods(mods.try_into().unwrap_or(0)) // HDHR
        .combo(combo)
        .misses(count_miss)
        .n100(count_100)
        .n50(count_50)
        .calculate();

    Ok(result.pp())
}

#[pyfunction]
fn calculate_pp_with_accuracy(file_path: &str, accuracy: f64, mods: usize) -> PyResult<f64> {
    let file = match File::open(file_path) {
        Ok(file) => file,
        Err(why) => panic!("Could not open file: {}", why),
    };

    // Parse the map yourself
    let map = match Beatmap::parse(file) {
        Ok(map) => map,
        Err(why) => panic!("Error while parsing map: {}", why),
    };

    let result = map
        .pp()
        .mods(mods.try_into().unwrap_or(0))
        .accuracy(accuracy)
        .calculate();

    Ok(result.pp())
}

#[pyfunction]
fn get_beatmap_info(file_path: &str, mods: usize) -> PyResult<BTreeMap<&str, f64>> {
    let file = match File::open(file_path) {
        Ok(file) => file,
        Err(why) => panic!("Could not open file: {}", why),
    };

    // Parse the map yourself
    let map = match Beatmap::parse(file) {
        Ok(map) => map,
        Err(why) => panic!("Error while parsing map: {}", why),
    };

    let result = map.pp().mods(mods.try_into().unwrap_or(0)).calculate(); // HDHR

    let mut map_data: BTreeMap<&str, f64> = BTreeMap::new();
    map_data.insert("stars", result.stars());
    map_data.insert("ar", map.ar as f64);
    map_data.insert("cs", map.cs as f64);
    map_data.insert("hp", map.hp as f64);
    map_data.insert("od", map.od as f64);

    if let Osu(diff_attr) = result.difficulty_attributes() {
        map_data.insert("max_combo", diff_attr.max_combo as f64);
    }

    Ok(map_data)
}

#[pymodule]
fn pp_calc(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_pp_with_counts, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_pp_with_accuracy, m)?)?;
    m.add_function(wrap_pyfunction!(get_beatmap_info, m)?)?;
    Ok(())
}
