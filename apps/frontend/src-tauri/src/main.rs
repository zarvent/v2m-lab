// Previene una ventana de consola adicional en Windows en modo release, ¡¡NO ELIMINAR!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    frontend_lib::run()
}
