use anyhow::Result;
use std::fs::File;
use std::io::Read;
use std::path::Path;

#[derive(Debug, PartialEq, Clone)]
pub enum FileFormat {
    WindowsPE, // .exe, .dll, .sys, .msi
    AppImage,
    DebianPackage, // .deb
    RpmPackage,    // .rpm
    FlatpakBundle, // .flatpak
    SnapPackage,   // .snap
    ZipArchive,    // .zip
    TarArchive,    // .tar.gz, .tar.bz2, .tar.xz
    ELF,           // standard linux binary
    Unknown,
}

/// PE import table known DLL → winetricks component mapping
pub const DEPENDENCY_MAP: &[(&str, &str)] = &[
    ("MSVCP140.dll",     "vcrun2015"),
    ("MSVCP141.dll",     "vcrun2017"),
    ("MSVCP142.dll",     "vcrun2019"),
    ("VCRUNTIME140.dll", "vcrun2015"),
    ("VCRUNTIME141.dll", "vcrun2017"),
    ("MSVCR120.dll",     "vcrun2013"),
    ("MSVCR110.dll",     "vcrun2012"),
    ("MSVCR100.dll",     "vcrun2010"),
    ("MSVCR90.dll",      "vcrun2008"),
    ("MSVCR80.dll",      "vcrun2005"),
    ("d3dx9_43.dll",     "d3dx9"),
    ("d3dx11_43.dll",    "d3dx11_43"),
    ("D3DCOMPILER_47.dll","d3dcompiler_47"),
    ("XINPUT1_3.dll",    "xinput"),
    ("XINPUT1_4.dll",    "xinput"),
    ("clr.dll",          "dotnet48"),
    ("mscorlib.dll",     "dotnet48"),
    ("hostfxr.dll",      "dotnet6"),
];

pub struct SmartDetector;

impl SmartDetector {
    /// Determines the executable format by reading the magic bytes of a file.
    pub fn detect_format<P: AsRef<Path>>(path: P) -> Result<FileFormat> {
        let mut file = File::open(path.as_ref())?;
        let mut buffer = [0u8; 64];
        let bytes_read = file.read(&mut buffer)?;

        if bytes_read < 4 {
            return Ok(FileFormat::Unknown);
        }

        // Windows MZ header → PE executable
        if buffer[0] == 0x4D && buffer[1] == 0x5A {
            return Ok(FileFormat::WindowsPE);
        }

        // ELF magic bytes
        if buffer[0] == 0x7F && buffer[1] == b'E' && buffer[2] == b'L' && buffer[3] == b'F' {
            // AppImage type 2 magic at offset 8
            if bytes_read >= 11 && buffer[8] == 0x41 && buffer[9] == 0x49 && buffer[10] == 0x02 {
                return Ok(FileFormat::AppImage);
            }
            return Ok(FileFormat::ELF);
        }

        // Debian package: starts with "!<arch>\n"
        if buffer.starts_with(b"!<arch>") {
            return Ok(FileFormat::DebianPackage);
        }

        // RPM magic: ed ab ee db
        if buffer[0] == 0xED && buffer[1] == 0xAB && buffer[2] == 0xEE && buffer[3] == 0xDB {
            return Ok(FileFormat::RpmPackage);
        }

        // ZIP / Flatpak / Snap (all ZIP-based)
        if buffer[0] == 0x50 && buffer[1] == 0x4B && buffer[2] == 0x03 && buffer[3] == 0x04 {
            let ext = path.as_ref()
                .extension()
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .to_lowercase();

            return Ok(match ext.as_str() {
                "flatpak" => FileFormat::FlatpakBundle,
                "snap"    => FileFormat::SnapPackage,
                _         => FileFormat::ZipArchive,
            });
        }

        // GZip / BZip2 / XZ → assume tar archive
        if (buffer[0] == 0x1F && buffer[1] == 0x8B)   // gzip
        || (buffer[0] == 0x42 && buffer[1] == 0x5A)   // bzip2
        || (buffer[0] == 0xFD && &buffer[1..6] == b"7zXZ") // xz
        {
            return Ok(FileFormat::TarArchive);
        }

        Ok(FileFormat::Unknown)
    }

    /// Scans a Windows PE import table for known DLL dependencies.
    /// Returns a list of winetricks component names that should be installed.
    pub fn detect_pe_dependencies<P: AsRef<Path>>(path: P) -> Result<Vec<&'static str>> {
        let content = std::fs::read(path.as_ref())?;
        let content_str = String::from_utf8_lossy(&content);
        let mut needed = Vec::new();

        for (dll_name, component) in DEPENDENCY_MAP {
            // Case-insensitive search for DLL name in binary
            if content_str.to_uppercase().contains(&dll_name.to_uppercase()) {
                if !needed.contains(component) {
                    needed.push(*component);
                }
            }
        }

        Ok(needed)
    }
}
