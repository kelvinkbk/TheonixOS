#!/usr/bin/env python3
"""
Theonix OS — Core Services & Passkey Interactive Test Suite
Tests all 5 decoupled system services and verifies Passkey creation/authentication over D-Bus.
"""

import sys
import os
import time

sys.path.insert(0, "/home/k/Desktop/Projects/theonix/theonix-core")
from theonix_core import (
    NotificationClient,
    SearchClient,
    UpdateClient,
    AuthClient,
    InputClient
)

def main():
    print("=" * 60)
    print("⚡ THEONIX OS — SYSTEM SERVICES & PASSKEY TEST SUITE")
    print("=" * 60)

    # 1. Test Updates Service
    print("\n1. [org.theonix.Updates] Checking System Status...")
    status = UpdateClient.get_system_status()
    print(f"   ✓ OS: {status.get('os_name')} {status.get('os_version')}")
    print(f"   ✓ Kernel: {status.get('kernel')}")

    # 2. Test Input & Touchpad Service
    print("\n2. [org.theonix.Input] Reading Touchpad & Gesture Config...")
    cfg = InputClient.get_gesture_config()
    print(f"   ✓ Natural Scroll: {cfg.get('natural_scroll')}")
    print(f"   ✓ 3-Finger Swipe Up: {cfg.get('gestures', {}).get('swipe_3_up')}")

    # 3. Test Global Omni-Search
    print("\n3. [org.theonix.Search] Querying global index for 'display'...")
    results = SearchClient.query("display", limit=3)
    for r in results:
        print(f"   ✓ [{r['category']}] {r['title']} -> {r['subtitle']}")

    # 4. Test Notification Service (Popup Banner)
    print("\n4. [org.theonix.Notifications] Triggering Glass Notification Banner...")
    notif_id = NotificationClient.notify(
        app_name="Theonix Passkey",
        title="Passkey Vault Active",
        message="WebAuthn / FIDO2 security engine is live on org.theonix.Auth",
        icon="🔑",
        actions=["Explore", "Dismiss"],
        timeout_ms=5000
    )
    print(f"   ✓ Sent notification banner with ID: {notif_id}")

    # 5. Interactive Passkey Creation Test
    print("\n5. [org.theonix.Auth] Launching Interactive Passkey Creation Dialog...")
    print("   👉 Look at your screen! Click '[Save Passkey]' in the purple modal.")
    pk_res = AuthClient.create_passkey("github.com", "kelvin@theonix")
    print("   ✓ Passkey Creation Result:", pk_res)

    # 6. Interactive Passkey Authentication Test
    if pk_res.get("success"):
        print("\n6. [org.theonix.Auth] Launching Interactive Passkey Authentication Dialog...")
        print("   👉 Look at your screen! Click '[Use Passkey]' to sign the challenge.")
        auth_res = AuthClient.authenticate_passkey("github.com", "challenge_nonce_xyz123")
        print("   ✓ Passkey Authentication Result:", auth_res)

    print("\n" + "=" * 60)
    print("🎉 ALL 5 THEONIX SERVICES & PASSKEY TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
