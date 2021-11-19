use pyo3::prelude::*;
use rosu_pp::{Beatmap, BeatmapExt};
use std::fs::File;

#[pyfunction]
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
fn calculate_pp_with_accuracy(
    file_path: &str,
    accuracy: f64,
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
        .mods(mods.try_into().unwrap_or(0))
        .accuracy(accuracy)
        .calculate();

    Ok(result.pp()) 
}

#[pymodule]
fn pp_calc(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(calculate_pp_with_counts, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_pp_with_accuracy, m)?)?;
    Ok(())
}