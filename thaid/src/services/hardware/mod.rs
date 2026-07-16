// =============================================================================
// thaid — Hardware Detection (GPU backend for Ollama)
// =============================================================================

use sysinfo::System;
use tracing::info;

/// Which GPU compute backend Ollama should use.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GpuBackend {
    /// NVIDIA GPU with CUDA support
    Cuda,
    /// AMD GPU with ROCm support
    Rocm,
    /// Intel Arc with SYCL/oneAPI (experimental)
    Sycl,
    /// No GPU — CPU-only inference (slow but works)
    CpuOnly,
}

impl std::fmt::Display for GpuBackend {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GpuBackend::Cuda => write!(f, "cuda"),
            GpuBackend::Rocm => write!(f, "rocm"),
            GpuBackend::Sycl => write!(f, "sycl"),
            GpuBackend::CpuOnly => write!(f, "cpu-only"),
        }
    }
}

/// System hardware information relevant to AI performance.
#[derive(Debug, Clone)]
pub struct HardwareInfo {
    pub gpu_backend: GpuBackend,
    pub total_ram_mb: u64,
    pub cpu_count: usize,
    pub cpu_name: String,
}

impl HardwareInfo {
    /// Detect GPU and memory at startup.
    /// This is a best-effort detection — never fails.
    pub fn detect() -> Self {
        let gpu_backend = detect_gpu_backend();
        let (ram, cpus, cpu_name) = detect_system_info();

        let info = Self {
            gpu_backend,
            total_ram_mb: ram,
            cpu_count: cpus,
            cpu_name,
        };

        // Warn the user if running CPU-only with little RAM
        if info.gpu_backend == GpuBackend::CpuOnly {
            info!(
                "No GPU detected — AI responses will use CPU inference (slower). \
                 Consider a system with a dedicated GPU for best experience."
            );
        }
        if info.total_ram_mb < 8192 {
            info!(
                total_ram_mb = info.total_ram_mb,
                "Low RAM detected. Recommend >=8GB for AI features. \
                 Using smaller models automatically."
            );
        }

        info
    }

    /// Recommend an appropriate model size based on available hardware.
    pub fn recommended_model(&self) -> &'static str {
        let has_gpu = self.gpu_backend != GpuBackend::CpuOnly;
        match (has_gpu, self.total_ram_mb) {
            (true, ram) if ram >= 16_384 => "llama3:8b",
            (true, ram) if ram >= 8_192 => "llama3:8b",
            (false, ram) if ram >= 16_384 => "llama3:8b",
            (false, ram) if ram >= 8_192 => "phi3:mini",
            _ => "gemma:2b",
        }
    }
}

// ---------------------------------------------------------------------------
// Private detection functions
// ---------------------------------------------------------------------------

fn detect_gpu_backend() -> GpuBackend {
    // Check for NVIDIA GPU via nvidia-smi
    if std::path::Path::new("/proc/driver/nvidia/version").exists() {
        info!("NVIDIA GPU detected — using CUDA backend");
        return GpuBackend::Cuda;
    }
    if which_gpu("nvidia") {
        info!("NVIDIA GPU detected via PCI — using CUDA backend");
        return GpuBackend::Cuda;
    }

    // Check for AMD GPU via ROCm
    if std::path::Path::new("/dev/kfd").exists() {
        info!("AMD GPU detected (KFD present) — using ROCm backend");
        return GpuBackend::Rocm;
    }
    if which_gpu("amd") || which_gpu("radeon") {
        info!("AMD GPU detected via PCI — using ROCm backend");
        return GpuBackend::Rocm;
    }

    // Check for Intel Arc
    if which_gpu("intel") && std::path::Path::new("/dev/dri/renderD128").exists() {
        // Heuristic: if Intel and renderD128 exists, assume Arc capable
        info!("Intel GPU detected — using SYCL backend (experimental)");
        return GpuBackend::Sycl;
    }

    info!("No dedicated GPU detected — using CPU-only inference");
    GpuBackend::CpuOnly
}

/// Check if any PCI device description contains the given GPU vendor keyword.
fn which_gpu(vendor: &str) -> bool {
    // Read /sys/bus/pci/devices/*/class and cross-reference with modalias
    // A simpler approach: check /proc/bus/pci/devices for display controllers
    std::fs::read_to_string("/proc/bus/pci/devices")
        .unwrap_or_default()
        .to_lowercase()
        .contains(vendor)
}

fn detect_system_info() -> (u64, usize, String) {
    let mut sys = System::new_all();
    sys.refresh_all();

    let total_ram_mb = sys.total_memory() / 1024 / 1024;
    let cpu_count = sys.cpus().len();
    let cpu_name = sys
        .cpus()
        .first()
        .map(|c| c.brand().to_string())
        .unwrap_or_else(|| "Unknown CPU".to_string());

    (total_ram_mb, cpu_count, cpu_name)
}
