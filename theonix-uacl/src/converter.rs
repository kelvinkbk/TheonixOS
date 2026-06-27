use anyhow::Result;
use std::path::Path;
use std::process::Command;
use log::{info, warn};

pub struct PackageConverter;

impl PackageConverter {
    /// Uses debtap to convert a .deb file to an Arch package and install it via pacman
    pub fn install_deb<P: AsRef<Path>>(deb_path: P) -> Result<()> {
        let deb_path = deb_path.as_ref();
        info!("Converting Debian package: {:?}", deb_path);

        let status = Command::new("debtap")
            .arg("-q")
            .arg(deb_path)
            .status()?;

        if !status.success() {
            anyhow::bail!("Debtap conversion failed");
        }

        let file_stem = deb_path.file_stem().unwrap().to_string_lossy().to_string();
        let current_dir = std::env::current_dir()?;

        for entry in std::fs::read_dir(current_dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_file() {
                if let Some(ext) = path.extension() {
                    if ext == "zst" && path.to_string_lossy().contains(&*file_stem) {
                        info!("Installing converted package: {:?}", path);
                        Command::new("sudo")
                            .args(["pacman", "-U", "--noconfirm"])
                            .arg(&path)
                            .status()?;
                        let _ = std::fs::remove_file(path);
                        break;
                    }
                }
            }
        }

        Ok(())
    }

    /// Installs a Flatpak bundle file
    pub fn install_flatpak<P: AsRef<Path>>(flatpak_path: P) -> Result<()> {
        let path = flatpak_path.as_ref();
        info!("Installing Flatpak bundle: {:?}", path);

        let status = Command::new("flatpak")
            .args(["install", "--noninteractive", "--user"])
            .arg(path)
            .status()?;

        if !status.success() {
            anyhow::bail!("Flatpak installation failed");
        }

        Ok(())
    }

    /// Installs a Snap package
    pub fn install_snap<P: AsRef<Path>>(snap_path: P) -> Result<()> {
        let path = snap_path.as_ref();
        info!("Installing Snap package: {:?}", path);

        let status = Command::new("sudo")
            .args(["snap", "install", "--dangerous"])
            .arg(path)
            .status()?;

        if !status.success() {
            anyhow::bail!("Snap installation failed");
        }

        Ok(())
    }

    /// Handles ZIP and TAR archives: extracts, then scans for ELF or PE executables
    pub fn handle_archive<P: AsRef<Path>>(archive_path: P) -> Result<()> {
        let path = archive_path.as_ref();
        let extract_dir = path.with_extension("");

        std::fs::create_dir_all(&extract_dir)?;

        let ext_str = path.to_string_lossy().to_lowercase();

        if ext_str.ends_with(".zip") {
            Command::new("unzip")
                .arg("-o")
                .arg(path)
                .arg("-d")
                .arg(&extract_dir)
                .status()?;
        } else {
            Command::new("tar")
                .arg("-xf")
                .arg(path)
                .arg("-C")
                .arg(&extract_dir)
                .status()?;
        }

        info!("Extracted archive to {:?}. Scanning for executables...", extract_dir);

        // Look for ELF or shell scripts to run
        for entry in std::fs::read_dir(&extract_dir)? {
            let entry = entry?;
            let p = entry.path();
            if p.is_file() {
                let name = p.file_name().unwrap().to_string_lossy().to_lowercase();
                if name.ends_with(".sh") || name.ends_with(".exe") || name == "run" {
                    use std::os::unix::fs::PermissionsExt;
                    let mut perms = std::fs::metadata(&p)?.permissions();
                    perms.set_mode(0o755);
                    std::fs::set_permissions(&p, perms)?;
                    Command::new(&p).spawn()?;
                    break;
                }
            }
        }

        Ok(())
    }

    /// Marks an AppImage or ELF executable and launches it
    pub fn launch_appimage<P: AsRef<Path>>(appimage_path: P) -> Result<()> {
        let path = appimage_path.as_ref();
        info!("Launching: {:?}", path);

        use std::os::unix::fs::PermissionsExt;
        let mut perms = std::fs::metadata(path)?.permissions();
        perms.set_mode(0o755);
        std::fs::set_permissions(path, perms)?;

        Command::new(path).spawn()?;

        Ok(())
    }
}
