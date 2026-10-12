import streamlit as st
from pathlib import Path
import tempfile
from seb_generator import (
    get_default_hackerrank_config,
    unpack_seb_file,
    pack_seb_bytes,
)
import hashlib

st.set_page_config(page_title="SEB Config Generator", page_icon="🔒", layout="centered")
st.title("🔒 HackerRank .seb Generator")

with st.form("seb_form"):
    contest_url = st.text_input(
        "HackerRank Contest URL",
        placeholder="https://www.hackerrank.com/contests/your-contest-slug",
    )
    quit_password = st.text_input(
        "Quit / Exit Password",
        type="password",
        help="Password students/invigilators enter after pressing Ctrl+Q / Cmd+Q to close SEB.",
    )
    output_filename = st.text_input("Output Filename", value="contest.seb")

    with st.expander("Advanced Options (Template & Launch Password)"):
        template_file = st.file_uploader(
            "Base .seb Template (Optional)",
            type=["seb"],
            help="Upload an existing unencrypted .seb file to preserve its exact rules while replacing the URL and quit password.",
        )
        entry_password = st.text_input(
            "SEB Launch Password (Optional)",
            type="password",
            help="Encrypts the .seb file itself (requires 'pip install rncryptor'). Students must enter this password when launching the file.",
        )
        clear_cookies = st.checkbox("Clear cookies on start & end", value=True)
        private_clipboard = st.checkbox("Isolate clipboard (prevent pasting from outside SEB)", value=True)

    submitted = st.form_submit_button("Generate .seb File")

if submitted:
    if not contest_url or not quit_password:
        st.error("Both the HackerRank Contest URL and Quit Password are required.")
    else:
        try:
            if template_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".seb") as tmp:
                    tmp.write(template_file.read())
                    tmp_path = Path(tmp.name)
                config = unpack_seb_file(tmp_path)
                tmp_path.unlink(missing_ok=True)
            else:
                config = get_default_hackerrank_config()
                config["examSessionClearCookiesOnStart"] = clear_cookies
                config["examSessionClearCookiesOnEnd"] = clear_cookies
                config["enablePrivateClipboard"] = private_clipboard

            config["startURL"] = contest_url.strip()
            config["hashedQuitPassword"] = hashlib.sha256(quit_password.encode("utf-8")).hexdigest().lower()
            config["allowQuit"] = True
            config["ignoreExitKeys"] = False
            config["sebConfigPurpose"] = 0

            seb_bytes = pack_seb_bytes(config, entry_password=entry_password or None)

            if not output_filename.endswith(".seb"):
                output_filename += ".seb"

            st.success(f"Generated `{output_filename}`!")
            st.download_button(
                label=f"⬇️ Download {output_filename}",
                data=seb_bytes,
                file_name=output_filename,
                mime="application/octet-stream",
            )
        except Exception as e:
            st.error(f"Failed to generate .seb file: {e}")