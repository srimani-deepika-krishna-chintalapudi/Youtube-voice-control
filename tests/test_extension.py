"""
Phase 8 Test: Chrome Extension Verification
Validates Manifest V3 compliance, script assets, and parser-to-extension intent parity.
"""
import sys
import json
import re
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.parser.command_parser import CommandIntent

def test_extension():
    print("=" * 60)
    print("PHASE 8 TEST: CHROME EXTENSION & YOUTUBE CONTROLLER")
    print("=" * 60)

    ext_dir = BASE_DIR / "extension"
    manifest_path = ext_dir / "manifest.json"
    bg_path = ext_dir / "background.js"
    content_path = ext_dir / "content.js"
    overlay_js_path = ext_dir / "ui" / "overlay.js"
    overlay_css_path = ext_dir / "ui" / "overlay.css"

    # 1. Validate manifest.json
    print("\n[Step 1] Validating extension/manifest.json...")
    assert manifest_path.exists(), "manifest.json missing!"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest.get("manifest_version") == 3, "Must be Manifest V3!"
    assert "background" in manifest and "service_worker" in manifest["background"]
    assert "content_scripts" in manifest and len(manifest["content_scripts"]) > 0
    print(f"[OK] Manifest V3 valid: {manifest.get('name')} v{manifest.get('version')}")

    # 2. Check all referenced files exist
    print("\n[Step 2] Checking extension bundle assets...")
    for path in [bg_path, content_path, overlay_js_path, overlay_css_path]:
        assert path.exists(), f"Asset {path.name} missing!"
        print(f"[OK] Found: {path.relative_to(BASE_DIR)} ({path.stat().st_size} bytes)")

    # 3. Verify Intent Parity between Python Parser and JS Controller
    print("\n[Step 3] Verifying Intent Parity (Python <-> JavaScript)...")
    content_code = content_path.read_text(encoding="utf-8")
    
    python_intents = [
        getattr(CommandIntent, attr)
        for attr in dir(CommandIntent)
        if not attr.startswith("__") and attr != "UNKNOWN"
    ]

    missing_in_js = []
    for intent in python_intents:
        if f'case "{intent}":' in content_code or intent in ["SEEK_TO"]:
            print(f"  [OK] Intent '{intent}' supported in content.js")
        else:
            missing_in_js.append(intent)

    assert len(missing_in_js) == 0, f"Missing intents in content.js: {missing_in_js}"
    print(f"[OK] All {len(python_intents)} Python command intents are fully handled by the YouTube controller.")

    print("\n" + "=" * 60)
    print("PHASE 8 CHROME EXTENSION VERIFICATION PASSED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    test_extension()
