/**
 * Theonix OS — Control Center Interactive Design Showroom Master Script
 * Vanilla JavaScript // Zero external dependencies
 */

document.addEventListener('DOMContentLoaded', () => {
    // State Store
    const state = {
        wifi: true,
        bluetooth: true,
        airplane: false,
        darkmode: true,
        nightlight: false,
        dnd: false,
        batterySaver: false,
        performanceMode: 'Balanced', // Balanced, Performance, Power Saver
        volume: 72,
        isMuted: false,
        prevVolume: 72,
        brightness: 80,
        audioDevice: 'speakers',
        activeSSID: 'Theonix-Home',
        activeIP: '192.168.1.42',
        mediaPlaying: true,
        currentTrackIndex: 0,
        accent: 'cyan',
        tileSize: 'medium',
        gridCols: 3,
        styleParadigm: 'glass',
        wallpaper: 1
    };

    const playlist = [
        { title: "Theonix — Neural Dreams", album: "Theonix Collection" },
        { title: "Cyber-Obsidian Ambience", album: "OS Soundscapes Vol. 1" },
        { title: "Kernel 6.x Velocity", album: "Theonix Synthwave" }
    ];

    // =========================================================================
    // 1. SIDEBAR NAVIGATION
    // =========================================================================
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            const section = item.getAttribute('data-section');
            handleNavigation(section);
        });
    });

    function handleNavigation(section) {
        if (section === 'customization') {
            document.getElementById('customizer-column').scrollIntoView({ behavior: 'smooth' });
        } else if (section === 'toggles') {
            document.getElementById('quick-toggles-grid').scrollIntoView({ behavior: 'smooth' });
        } else if (section === 'audio' || section === 'display') {
            document.querySelector('.cc-sliders-card').scrollIntoView({ behavior: 'smooth' });
        } else if (section === 'network') {
            document.querySelector('.cc-network-card').scrollIntoView({ behavior: 'smooth' });
        } else if (section === 'media') {
            document.querySelector('.cc-media-card').scrollIntoView({ behavior: 'smooth' });
        } else if (section === 'thaid') {
            document.querySelector('.cc-thaid-card').scrollIntoView({ behavior: 'smooth' });
        } else if (section === 'notifications') {
            document.querySelector('.cc-notifications-card').scrollIntoView({ behavior: 'smooth' });
        } else {
            document.getElementById('desktop-mockup').scrollIntoView({ behavior: 'smooth' });
        }
    }

    // Live clock in sidebar
    function updateClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const el = document.getElementById('sidebar-time');
        if (el) el.textContent = timeStr;
    }
    setInterval(updateClock, 1000);
    updateClock();

    // =========================================================================
    // 2. QUICK TOGGLES INTERACTION
    // =========================================================================
    const tileWifi = document.getElementById('tile-wifi');
    const tileBt = document.getElementById('tile-bluetooth');
    const tileAirplane = document.getElementById('tile-airplane');
    const tileDark = document.getElementById('tile-darkmode');
    const tileNight = document.getElementById('tile-nightlight');
    const tileDnd = document.getElementById('tile-dnd');
    const tileBat = document.getElementById('tile-battery');
    const tilePerf = document.getElementById('tile-performance');
    const tileThaid = document.getElementById('tile-thaid');

    // Wi-Fi Toggle
    tileWifi.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        if (state.airplane) return;
        state.wifi = !state.wifi;
        updateWifiUI();
    });

    function updateWifiUI() {
        if (state.wifi) {
            tileWifi.classList.add('active');
            document.getElementById('wifi-status-text').textContent = 'Connected';
            document.getElementById('chip-wifi-status').textContent = '● Wi-Fi Connected';
            document.getElementById('chip-wifi-status').style.display = 'inline-block';
            document.querySelector('.net-badge').textContent = 'Connected';
            document.querySelector('.net-badge').className = 'net-badge connected';
        } else {
            tileWifi.classList.remove('active');
            document.getElementById('wifi-status-text').textContent = 'Off';
            document.getElementById('chip-wifi-status').textContent = '○ Wi-Fi Off';
            document.querySelector('.net-badge').textContent = 'Disconnected';
            document.querySelector('.net-badge').className = 'net-badge';
        }
    }

    // Bluetooth Toggle
    tileBt.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        if (state.airplane) return;
        state.bluetooth = !state.bluetooth;
        if (state.bluetooth) {
            tileBt.classList.add('active');
            document.getElementById('bt-status-text').textContent = 'Connected';
            document.getElementById('chip-bt-status').textContent = '● Bluetooth On';
        } else {
            tileBt.classList.remove('active');
            document.getElementById('bt-status-text').textContent = 'Off';
            document.getElementById('chip-bt-status').textContent = '○ Bluetooth Off';
        }
    });

    // Airplane Mode Toggle
    tileAirplane.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        state.airplane = !state.airplane;
        const banner = document.getElementById('airplane-banner');
        if (state.airplane) {
            tileAirplane.classList.add('active');
            document.getElementById('airplane-status-text').textContent = 'On';
            banner.style.display = 'block';

            // Disable Wi-Fi & Bluetooth
            state.wifi = false;
            state.bluetooth = false;
            updateWifiUI();
            tileBt.classList.remove('active');
            document.getElementById('bt-status-text').textContent = 'Off';
            document.getElementById('chip-bt-status').textContent = '○ Bluetooth Off';
        } else {
            tileAirplane.classList.remove('active');
            document.getElementById('airplane-status-text').textContent = 'Off';
            banner.style.display = 'none';

            // Re-enable Wi-Fi & BT
            state.wifi = true;
            state.bluetooth = true;
            updateWifiUI();
            tileBt.classList.add('active');
            document.getElementById('bt-status-text').textContent = 'Connected';
            document.getElementById('chip-bt-status').textContent = '● Bluetooth On';
        }
    });

    // Dark Mode Toggle
    tileDark.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        state.darkmode = !state.darkmode;
        if (state.darkmode) {
            document.body.classList.remove('theme-light');
            document.body.classList.add('theme-dark');
            tileDark.classList.add('active');
            document.getElementById('darkmode-status-text').textContent = 'Dark';
        } else {
            document.body.classList.remove('theme-dark');
            document.body.classList.add('theme-light');
            tileDark.classList.remove('active');
            document.getElementById('darkmode-status-text').textContent = 'Light';
        }
    });

    // Night Light Toggle
    tileNight.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        state.nightlight = !state.nightlight;
        const overlay = document.getElementById('night-light-overlay');
        if (state.nightlight) {
            tileNight.classList.add('active');
            document.getElementById('nightlight-status-text').textContent = 'Warm 4500K';
            overlay.classList.add('active');
        } else {
            tileNight.classList.remove('active');
            document.getElementById('nightlight-status-text').textContent = 'Off';
            overlay.classList.remove('active');
        }
    });

    // DND Toggle
    tileDnd.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        state.dnd = !state.dnd;
        if (state.dnd) {
            tileDnd.classList.add('active');
            document.getElementById('dnd-status-text').textContent = 'DND Active';
        } else {
            tileDnd.classList.remove('active');
            document.getElementById('dnd-status-text').textContent = 'Off';
        }
    });

    // Battery Saver Toggle
    tileBat.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        state.batterySaver = !state.batterySaver;
        const batPill = document.getElementById('battery-status-pill');
        if (state.batterySaver) {
            tileBat.classList.add('active');
            document.getElementById('battery-status-text').textContent = 'Saver Active';
            batPill.style.borderColor = 'var(--accent-amber)';
            batPill.querySelector('.bat-text').textContent = '88% (Eco)';
        } else {
            tileBat.classList.remove('active');
            document.getElementById('battery-status-text').textContent = 'Off';
            batPill.style.borderColor = 'var(--glass-border)';
            batPill.querySelector('.bat-text').textContent = '88%';
        }
    });

    // Performance Mode Cycling
    tilePerf.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        const modes = ['Balanced', 'Performance', 'Power Saver'];
        const nextIdx = (modes.indexOf(state.performanceMode) + 1) % modes.length;
        state.performanceMode = modes[nextIdx];
        document.getElementById('perf-status-text').textContent = state.performanceMode;
    });

    // THAID AI Quick Tile -> Opens Assistant
    tileThaid.addEventListener('click', (e) => {
        if (e.target.classList.contains('drag-handle')) return;
        openThaidModal();
    });

    // =========================================================================
    // 3. SLIDERS & AUDIO SECTION
    // =========================================================================
    const sliderVol = document.getElementById('slider-volume');
    const volLabel = document.getElementById('volume-label');
    const volFill = document.getElementById('volume-slider-fill');
    const btnMute = document.getElementById('btn-volume-mute');

    sliderVol.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        state.volume = val;
        state.isMuted = val === 0;
        updateVolumeUI();
    });

    btnMute.addEventListener('click', () => {
        state.isMuted = !state.isMuted;
        if (state.isMuted) {
            state.prevVolume = state.volume;
            state.volume = 0;
            sliderVol.value = 0;
        } else {
            state.volume = state.prevVolume || 72;
            sliderVol.value = state.volume;
        }
        updateVolumeUI();
    });

    function updateVolumeUI() {
        volLabel.textContent = `Volume ${state.volume}%`;
        const pct = (state.volume / 150) * 100;
        volFill.style.width = `${pct}%`;
        btnMute.textContent = state.isMuted || state.volume === 0 ? '🔇' : '🔊';
    }

    // Brightness Slider
    const sliderBright = document.getElementById('slider-brightness');
    const brightLabel = document.getElementById('brightness-label');
    const brightFill = document.getElementById('brightness-slider-fill');

    sliderBright.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        state.brightness = val;
        brightLabel.textContent = `Brightness ${val}%`;
        brightFill.style.width = `${val}%`;
    });

    // Audio Output Dropdown
    document.getElementById('audio-device-select').addEventListener('change', (e) => {
        state.audioDevice = e.target.value;
    });

    // =========================================================================
    // 4. NETWORK CARD & MODAL
    // =========================================================================
    const netModal = document.getElementById('network-modal');
    document.getElementById('btn-open-network-modal').addEventListener('click', () => {
        netModal.classList.add('active');
    });
    document.getElementById('btn-close-net-modal').addEventListener('click', () => {
        netModal.classList.remove('active');
    });

    document.querySelectorAll('.net-row').forEach(row => {
        row.addEventListener('click', () => {
            const ssid = row.getAttribute('data-ssid');
            const ip = row.getAttribute('data-ip');
            state.activeSSID = ssid;
            state.activeIP = ip;

            document.getElementById('active-ssid').textContent = ssid;
            document.getElementById('active-ip').textContent = ip;
            document.querySelectorAll('.net-row').forEach(r => r.classList.remove('active'));
            row.classList.add('active');

            state.wifi = true;
            updateWifiUI();
            netModal.classList.remove('active');
        });
    });

    document.getElementById('btn-net-disconnect').addEventListener('click', () => {
        state.wifi = false;
        updateWifiUI();
    });

    // =========================================================================
    // 5. MEDIA PLAYER
    // =========================================================================
    const btnPlay = document.getElementById('btn-media-play');
    const btnPrev = document.getElementById('btn-media-prev');
    const btnNext = document.getElementById('btn-media-next');
    const trackNameEl = document.getElementById('track-name');
    const progFill = document.getElementById('media-progress-fill');

    btnPlay.addEventListener('click', () => {
        state.mediaPlaying = !state.mediaPlaying;
        btnPlay.textContent = state.mediaPlaying ? '⏸' : '▶';
    });

    btnNext.addEventListener('click', () => {
        state.currentTrackIndex = (state.currentTrackIndex + 1) % playlist.length;
        updateTrackUI();
    });

    btnPrev.addEventListener('click', () => {
        state.currentTrackIndex = (state.currentTrackIndex - 1 + playlist.length) % playlist.length;
        updateTrackUI();
    });

    function updateTrackUI() {
        const item = playlist[state.currentTrackIndex];
        trackNameEl.textContent = item.title;
        progFill.style.width = '10%';
    }

    // Animated progress simulation
    setInterval(() => {
        if (state.mediaPlaying) {
            let curr = parseFloat(progFill.style.width) || 42;
            curr = (curr + 1) % 100;
            progFill.style.width = `${curr}%`;
        }
    }, 1000);

    // =========================================================================
    // 6. THAID AI DIALOG & BUTTONS
    // =========================================================================
    const thaidModal = document.getElementById('thaid-dialog-modal');
    document.getElementById('btn-ask-thaid').addEventListener('click', openThaidModal);
    document.getElementById('btn-thaid-assistant').addEventListener('click', openThaidModal);
    document.getElementById('btn-thaid-voice').addEventListener('click', () => {
        openThaidModal();
        addThaidMessage("bot", "🎙️ Voice Mode Listening... Say a command like 'Increase volume to 90%'");
    });
    document.getElementById('btn-close-thaid-modal').addEventListener('click', () => {
        thaidModal.classList.remove('active');
    });

    function openThaidModal() {
        thaidModal.classList.add('active');
        document.getElementById('thaid-user-input').focus();
    }

    const thaidForm = document.getElementById('thaid-input-form');
    const thaidInput = document.getElementById('thaid-user-input');
    const chatLog = document.getElementById('thaid-chat-log');

    thaidForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = thaidInput.value.trim();
        if (!text) return;

        addThaidMessage('user', text);
        thaidInput.value = '';

        // Simulate THAID Assistant Response & Command Execution
        setTimeout(() => {
            handleThaidCommand(text.toLowerCase());
        }, 500);
    });

    function addThaidMessage(sender, text) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}`;
        bubble.innerHTML = `<span>${text}</span>`;
        chatLog.appendChild(bubble);
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    function handleThaidCommand(cmd) {
        if (cmd.includes('dark') || cmd.includes('light')) {
            tileDark.click();
            addThaidMessage('bot', `✓ Toggled display theme.`);
        } else if (cmd.includes('dnd') || cmd.includes('disturb')) {
            tileDnd.click();
            addThaidMessage('bot', `✓ Do Not Disturb is now ${state.dnd ? 'active' : 'disabled'}.`);
        } else if (cmd.includes('volume') || cmd.includes('mute')) {
            btnMute.click();
            addThaidMessage('bot', `✓ Volume state updated.`);
        } else if (cmd.includes('battery')) {
            addThaidMessage('bot', `🔋 Battery is at 88% capacity (Charging). Health is optimal.`);
        } else {
            addThaidMessage('bot', `✓ Understood: "${cmd}". In Theonix OS, THAID will execute this task via UACL.`);
        }
    }

    // =========================================================================
    // 7. NOTIFICATIONS
    // =========================================================================
    document.querySelectorAll('.notif-dismiss-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const item = document.getElementById(targetId);
            if (item) {
                item.style.opacity = '0';
                item.style.transform = 'translateX(20px)';
                setTimeout(() => {
                    item.remove();
                    updateNotifCount();
                }, 200);
            }
        });
    });

    document.getElementById('btn-clear-all-notifs').addEventListener('click', () => {
        document.getElementById('notif-list').innerHTML = '';
        updateNotifCount();
    });

    function updateNotifCount() {
        const count = document.querySelectorAll('.notif-item').length;
        const pill = document.getElementById('notif-count-pill');
        const emptyState = document.getElementById('notif-empty');
        if (pill) pill.textContent = count;
        if (count === 0 && emptyState) {
            emptyState.style.display = 'block';
            pill.style.display = 'none';
        }
    }

    // =========================================================================
    // 8. CUSTOMIZATION & DRAG-AND-DROP REORDERING
    // =========================================================================
    const gridContainer = document.getElementById('quick-toggles-grid');
    let draggedTile = null;

    function initDragAndDrop() {
        const tiles = gridContainer.querySelectorAll('.toggle-tile');
        tiles.forEach(tile => {
            tile.addEventListener('dragstart', (e) => {
                draggedTile = tile;
                tile.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            });

            tile.addEventListener('dragend', () => {
                draggedTile = null;
                tiles.forEach(t => t.classList.remove('dragging', 'drag-over'));
            });

            tile.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                tile.classList.add('drag-over');
            });

            tile.addEventListener('dragleave', () => {
                tile.classList.remove('drag-over');
            });

            tile.addEventListener('drop', (e) => {
                e.preventDefault();
                tile.classList.remove('drag-over');
                if (draggedTile && draggedTile !== tile) {
                    const allTiles = Array.from(gridContainer.children);
                    const fromIdx = allTiles.indexOf(draggedTile);
                    const toIdx = allTiles.indexOf(tile);

                    if (fromIdx < toIdx) {
                        gridContainer.insertBefore(draggedTile, tile.nextSibling);
                    } else {
                        gridContainer.insertBefore(draggedTile, tile);
                    }
                }
            });
        });
    }
    initDragAndDrop();

    // Accent Color Switcher
    document.querySelectorAll('.color-swatch-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.color-swatch-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const color = btn.getAttribute('data-color');
            document.body.setAttribute('data-accent', color);
            state.accent = color;
        });
    });

    // Tile Size Selector
    document.querySelectorAll('#tile-size-control .segment-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#tile-size-control .segment-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const size = btn.getAttribute('data-size');
            state.tileSize = size;
            gridContainer.querySelectorAll('.toggle-tile').forEach(t => t.setAttribute('data-size', size));
        });
    });

    // Grid Columns Selector
    document.querySelectorAll('#grid-columns-control .segment-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#grid-columns-control .segment-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const cols = btn.getAttribute('data-cols');
            state.gridCols = parseInt(cols);
            document.body.setAttribute('data-grid', cols);
        });
    });

    // Panel Style Paradigm Selector
    document.querySelectorAll('#style-paradigm-control .segment-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#style-paradigm-control .segment-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const st = btn.getAttribute('data-style');
            state.styleParadigm = st;
            document.getElementById('control-center-panel').setAttribute('data-style', st);
        });
    });

    // Wallpaper Switcher
    document.querySelectorAll('.wallpaper-thumb').forEach(thumb => {
        thumb.addEventListener('click', () => {
            document.querySelectorAll('.wallpaper-thumb').forEach(t => t.classList.remove('active'));
            thumb.classList.add('active');
            const wp = thumb.getAttribute('data-wp');
            state.wallpaper = wp;
            document.body.className = `theme-${state.darkmode ? 'dark' : 'light'} wallpaper-${wp}`;
        });
    });

    // Toggle Customizer Visibility / Focus
    document.getElementById('btn-toggle-customizer').addEventListener('click', () => {
        document.getElementById('customizer-column').scrollIntoView({ behavior: 'smooth' });
    });

    // Reset Defaults
    document.getElementById('btn-reset-default').addEventListener('click', () => {
        document.body.setAttribute('data-accent', 'cyan');
        document.body.setAttribute('data-grid', '3');
        document.body.className = 'theme-dark wallpaper-1';
        document.getElementById('control-center-panel').setAttribute('data-style', 'glass');
        gridContainer.querySelectorAll('.toggle-tile').forEach(t => t.setAttribute('data-size', 'medium'));
        
        // Reset active buttons in customizer
        document.querySelectorAll('.color-swatch-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('.color-swatch-btn[data-color="cyan"]').classList.add('active');

        document.querySelectorAll('.wallpaper-thumb').forEach(b => b.classList.remove('active'));
        document.querySelector('.wallpaper-thumb[data-wp="1"]').classList.add('active');

        document.querySelectorAll('#grid-columns-control .segment-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('#grid-columns-control .segment-btn[data-cols="3"]').classList.add('active');

        document.querySelectorAll('#tile-size-control .segment-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('#tile-size-control .segment-btn[data-size="medium"]').classList.add('active');

        document.querySelectorAll('#style-paradigm-control .segment-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('#style-paradigm-control .segment-btn[data-style="glass"]').classList.add('active');

        showToast("✓ Restored Theonix defaults");
    });

    // Apply Configuration Button
    document.getElementById('btn-apply-config').addEventListener('click', () => {
        showToast("✓ Control Center configuration saved! Ready to compile into Theonix OS.");
    });

    function showToast(msg) {
        const toast = document.getElementById('apply-toast');
        if (msg) toast.querySelector('p').textContent = msg;
        toast.classList.add('active');
        setTimeout(() => {
            toast.classList.remove('active');
        }, 4000);
    }
});
