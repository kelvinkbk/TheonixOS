mod database;
mod detector;
mod runtime;
mod converter;

use clap::{Parser, Subcommand};
use database::{Database, Application};
use detector::{SmartDetector, FileFormat};
use runtime::{RuntimeManager, RuntimeProfile};
use converter::PackageConverter;
use std::path::PathBuf;

#[derive(Parser)]
#[command(author, version, about = "Theonix Universal Application Compatibility Layer")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Launch or install an application from a file
    Run {
        #[arg(short, long)]
        file: String,
        /// Override the runtime profile (gaming, office, legacy, portable, development)
        #[arg(short, long, default_value = "auto")]
        profile: String,
    },
    /// List installed applications
    List,
    /// Uninstall an application by ID
    Uninstall {
        #[arg(short, long)]
        id: String,
    },
}

fn main() -> anyhow::Result<()> {
    env_logger::init();
    let cli = Cli::parse();

    let db_path = dirs::config_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("theonix")
        .join("uacl.db");

    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let db = Database::new(db_path)?;

    match &cli.command {
        Commands::Run { file, profile } => {
            let path = PathBuf::from(file);
            if !path.exists() {
                anyhow::bail!("File does not exist: {}", file);
            }

            let format = SmartDetector::detect_format(&path)?;
            println!("Detected format: {:?}", format);

            match format {
                FileFormat::WindowsPE => {
                    println!("Windows executable detected. Routing to Runtime Engine...");
                    let rm = RuntimeManager::new()?;

                    let app_name = path.file_stem().unwrap().to_string_lossy().to_string();
                    let app_id = app_name.to_lowercase().replace(' ', "_");

                    // Phase 6.3: Scan PE import table for missing dependencies
                    println!("Scanning for required dependencies...");
                    let deps = SmartDetector::detect_pe_dependencies(&path)?;
                    if !deps.is_empty() {
                        println!("Auto-installing {} dependencies: {:?}", deps.len(), deps);
                    } else {
                        println!("No additional dependencies required.");
                    }

                    // Phase 6.2: Apply runtime profile
                    let rt_profile = RuntimeProfile::from_str(profile);
                    println!("Using runtime profile: {}", rt_profile.name());

                    let prefix_path = rm.create_wine_prefix(&app_id)?;

                    // Auto install deps first
                    if !deps.is_empty() {
                        rm.auto_install_dependencies(&prefix_path, &deps)?;
                    }

                    // Apply profile (Windows version)
                    rm.apply_profile(&prefix_path, &rt_profile)?;

                    // Apply DXVK if gaming profile
                    if rt_profile.uses_dxvk() {
                        rm.install_dxvk(&prefix_path)?;
                    }

                    rm.run_executable(&prefix_path, &path, &[])?;

                    // Phase 6.1: Register in database with full intelligence fields
                    let app = Application {
                        id: app_id.clone(),
                        name: app_name,
                        original_file_path: path.to_string_lossy().to_string(),
                        install_path: prefix_path.to_string_lossy().to_string(),
                        format_type: "WindowsPE".to_string(),
                        prefix_path: Some(prefix_path.to_string_lossy().to_string()),
                        runtime_version: Some("wine".to_string()),
                        uses_dxvk: rt_profile.uses_dxvk(),
                        uses_vkd3d: false,
                        desktop_shortcut_path: None,
                        icon_path: None,
                        compatibility_rating: 0,
                        launch_count: 1,
                        last_launch: None,
                        known_issues: None,
                        runtime_profile: Some(rt_profile.name().to_string()),
                        recommended_runtime: Some("wine".to_string()),
                        gpu_backend: if rt_profile.uses_dxvk() {
                            Some("dxvk".to_string())
                        } else {
                            Some("none".to_string())
                        },
                        sandbox_enabled: true,
                    };

                    let _ = db.insert_application(&app);
                    db.record_launch(&app_id)?;
                    println!("Registered '{}' in Theonix App Manager.", app_id);
                }

                FileFormat::AppImage | FileFormat::ELF => {
                    println!("AppImage/ELF detected. Launching...");
                    PackageConverter::launch_appimage(&path)?;
                }

                FileFormat::DebianPackage => {
                    println!("Debian package detected. Converting to native package...");
                    PackageConverter::install_deb(&path)?;
                }

                FileFormat::FlatpakBundle => {
                    println!("Flatpak bundle detected. Installing via flatpak...");
                    PackageConverter::install_flatpak(&path)?;
                }

                FileFormat::SnapPackage => {
                    println!("Snap package detected. Installing via snapd...");
                    PackageConverter::install_snap(&path)?;
                }

                FileFormat::ZipArchive | FileFormat::TarArchive => {
                    println!("Archive detected. Extracting and scanning for executables...");
                    PackageConverter::handle_archive(&path)?;
                }

                FileFormat::RpmPackage => {
                    println!("RPM package detected. Routing to debtap pipeline...");
                    println!("Note: RPM support coming in Phase 6.5 update.");
                }

                FileFormat::Unknown => {
                    println!("Unknown format. Cannot process this file.");
                }
            }
        }

        Commands::List => {
            let apps = db.get_applications()?;
            if apps.is_empty() {
                println!("No applications installed yet.");
            } else {
                println!("{:<20} {:<12} {:<10} {:<8} {}", "NAME", "FORMAT", "PROFILE", "LAUNCHES", "RATING");
                println!("{}", "-".repeat(70));
                for app in apps {
                    println!("{:<20} {:<12} {:<10} {:<8} {}★",
                        app.name,
                        app.format_type,
                        app.runtime_profile.unwrap_or_else(|| "auto".to_string()),
                        app.launch_count,
                        app.compatibility_rating,
                    );
                }
            }
        }

        Commands::Uninstall { id } => {
            db.delete_application(id)?;
            println!("Removed '{}' from Theonix App Manager.", id);
        }
    }

    Ok(())
}
