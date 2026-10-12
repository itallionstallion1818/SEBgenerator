import argparse
import gzip
import hashlib
import plistlib
from pathlib import Path
from typing import Optional


def get_default_hackerrank_config() -> dict:
    """
    Returns a strict default SEB configuration dictionary tailored
    for coding contests on HackerRank.
    """
    return {
        "originatorVersion": "SEB_Win_3.7.1",
        "sebConfigPurpose": 0,  # 0 = Starting an exam, 1 = Configuring a client
        "startURL": "https://www.hackerrank.com",
        "startURLAppendQueryParameter": False,
        
        # Quit & Exit Settings
        "allowQuit": True,
        "ignoreExitKeys": False,
        "hashedQuitPassword": "",
        "quitURL": "",
        "quitURLConfirm": True,
        
        # Browser & UI Lockdown
        "browserViewMode": 1,  # 1 = Fullscreen mode, 0 = Window mode
        "mainBrowserWindowWidth": "100%",
        "mainBrowserWindowHeight": "100%",
        "enableBrowserWindowToolbar": False,
        "hideBrowserWindowToolbar": True,
        "showMenuBar": False,
        "showTaskBar": True,
        "taskBarHeight": 40,
        "showReloadButton": True,
        "showTime": True,
        "showInputLanguage": True,
        "allowBrowsingBackForward": True,  # Needed to navigate between contest problems
        "newBrowserWindowByLinkPolicy": 2,  # 2 = Open in same window
        "newBrowserWindowByScriptPolicy": 2,
        
        # Security & Anti-Cheat Restrictions
        "allowSwitchToApplications": False,
        "allowFlashFullscreen": False,
        "allowPDFPlugIn": False,
        "allowDeveloperConsole": False,
        "allowSpellCheck": False,
        "allowDictionaryLookup": False,
        "allowDictation": False,
        "allowSiri": False,
        "allowScreenCapture": False,
        "allowWindowCapture": False,
        "allowScreenSharing": False,
        "allowVirtualMachine": False,
        "enableRightMouse": False,
        "enableAltMouseWheel": False,
        "enableEsc": False,
        "enableCtrlEsc": False,
        "enableAltEsc": False,
        "enableAltTab": False,
        "enableAltF4": False,
        "enableStartMenu": False,
        "enablePrintScreen": False,
        "hookKeys": True,
        
        # Clipboard & Session Policies
        "enablePrivateClipboard": True,  # Isolates copy/paste strictly inside SEB
        "examSessionClearCookiesOnStart": True,  # Forces fresh login at start
        "examSessionClearCookiesOnEnd": True,
        
        # Header Keys
        "sendBrowserExamKey": True,
        "browserURLSalt": True,
    }


def unpack_seb_file(seb_path: Path) -> dict:
    """
    Unpacks an existing unencrypted (.seb) file (either 'plnd' double-gzipped 
    or raw XML plist) into a Python dictionary.
    """
    raw_bytes = seb_path.read_bytes()

    # Check if outer layer is gzipped
    if raw_bytes[:2] == b"\x1f\x8b":
        outer_decompressed = gzip.decompress(raw_bytes)
    else:
        outer_decompressed = raw_bytes

    # Check 4-byte SEB magic prefix
    prefix = outer_decompressed[:4]
    if prefix == b"plnd":
        inner_compressed = outer_decompressed[4:]
        xml_bytes = gzip.decompress(inner_compressed)
    elif prefix in (b"pswd", b"pwcc", b"pkhs", b"phsk"):
        raise ValueError(
            f"Template file uses encrypted header '{prefix.decode()}'. "
            "Save the template without an admin/settings password first."
        )
    elif outer_decompressed.lstrip().startswith(b"<?xml"):
        xml_bytes = outer_decompressed
    else:
        raise ValueError("Unrecognized .seb file structure.")

    return plistlib.loads(xml_bytes)


def pack_seb_bytes(config: dict, entry_password: Optional[str] = None) -> bytes:
    """
    Serializes the config dict into the official SEB binary format:
    - Unencrypted: gzip( b'plnd' + gzip(plist_xml) )
    - Encrypted:   gzip( b'pswd' + RNCryptor_encrypt(gzip(plist_xml), entry_password) )
    """
    xml_bytes = plistlib.dumps(config, fmt=plistlib.FMT_XML, sort_keys=True)
    inner_gzip = gzip.compress(xml_bytes)

    if entry_password:
        try:
            import rncryptor
        except ImportError as exc:
            raise ImportError(
                "Install 'rncryptor' (pip install rncryptor) to encrypt .seb files with an entry password."
            ) from exc
        cryptor = rncryptor.RNCryptor()
        encrypted_payload = cryptor.encrypt(inner_gzip, entry_password)
        payload = b"pswd" + encrypted_payload
    else:
        payload = b"plnd" + inner_gzip

    return gzip.compress(payload)


def create_seb_config(
    contest_url: str,
    quit_password: str,
    output_path: Path,
    template_path: Optional[Path] = None,
    entry_password: Optional[str] = None,
) -> Path:
    """
    Creates a custom .seb file with the specified HackerRank URL and quit password.
    """
    if template_path and template_path.exists():
        config = unpack_seb_file(template_path)
    else:
        config = get_default_hackerrank_config()

    # Hash the quit password with SHA-256 (lowercase hex string required by SEB)
    quit_hash = hashlib.sha256(quit_password.encode("utf-8")).hexdigest().lower()

    # Apply contest overrides
    config["startURL"] = contest_url.strip()
    config["hashedQuitPassword"] = quit_hash
    config["allowQuit"] = True
    config["ignoreExitKeys"] = False
    config["sebConfigPurpose"] = 0

    seb_Binary = pack_seb_bytes(config, entry_password=entry_password)
    output_path.write_bytes(seb_Binary)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate custom .seb files for HackerRank contests.")
    parser.add_argument("--url", required=True, help="HackerRank contest or test link")
    parser.add_argument("--quit-pass", required=True, help="Plaintext password required to exit SEB")
    parser.add_argument("--out", default="contest.seb", help="Output .seb filename (default: contest.seb)")
    parser.add_argument("--template", help="Optional existing .seb file to use as a base template")
    parser.add_argument("--entry-pass", help="Optional password required to open/launch the .seb file")

    args = parser.parse_args()

    out_file = create_seb_config(
        contest_url=args.url,
        quit_password=args.quit_pass,
        output_path=Path(args.out),
        template_path=Path(args.template) if args.template else None,
        entry_password=args.entry_pass,
    )
    print(f"Created SEB configuration: {out_file.resolve()}")