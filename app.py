import hashlib
import io
from urllib.parse import urlsplit

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from seb_generator import (
    get_default_hackerrank_config,
    pack_seb_bytes,
    unpack_seb_bytes,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4_400_000
app.config["TEMPLATES_AUTO_RELOAD"] = False


@app.get("/")
def index():
    return render_template("index.html")


@app.errorhandler(RequestEntityTooLarge)
def request_too_large(_error):
    return jsonify(error="The upload is too large. Choose a template smaller than 4 MB."), 413


@app.post("/api/generate")
def generate():
    contest_url = request.form.get("contest_url", "").strip()
    quit_password = request.form.get("quit_password", "")
    if not contest_url or not quit_password:
        return jsonify(error="Both the HackerRank Contest URL and Quit Password are required."), 400

    try:
        parsed_url = urlsplit(contest_url)
    except ValueError:
        return jsonify(error="Enter a valid URL beginning with http:// or https://."), 400
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return jsonify(error="Enter a valid URL beginning with http:// or https://."), 400

    output_filename = secure_filename(request.form.get("output_filename", "").strip())
    if not output_filename:
        output_filename = "contest.seb"
    if not output_filename.lower().endswith(".seb"):
        output_filename += ".seb"

    template_file = request.files.get("template")
    has_template = template_file is not None and bool(template_file.filename)

    try:
        if has_template:
            config = unpack_seb_bytes(template_file.read())
        else:
            config = get_default_hackerrank_config()
            clear_cookies = request.form.get("clear_cookies") == "true"
            config["examSessionClearCookiesOnStart"] = clear_cookies
            config["examSessionClearCookiesOnEnd"] = clear_cookies
            config["enablePrivateClipboard"] = request.form.get("private_clipboard") == "true"

        config["startURL"] = contest_url
        config["hashedQuitPassword"] = hashlib.sha256(
            quit_password.encode("utf-8")
        ).hexdigest().lower()
        config["allowQuit"] = True
        config["ignoreExitKeys"] = False
        config["sebConfigPurpose"] = 0
        config["sendBrowserExamKey"] = False
        config["browserURLSalt"] = False
        if config.get("newBrowserWindowByLinkPolicy") == 2:
            config["newBrowserWindowByLinkPolicy"] = 1
        if config.get("newBrowserWindowByScriptPolicy") == 2:
            config["newBrowserWindowByScriptPolicy"] = 1

        seb_bytes = pack_seb_bytes(
            config,
            entry_password=request.form.get("entry_password") or None,
        )
    except (ValueError, ImportError) as error:
        return jsonify(error=str(error)), 400
    except Exception:
        app.logger.exception("Failed to generate SEB configuration")
        return jsonify(error="The configuration could not be generated. Check the template and try again."), 500

    return send_file(
        io.BytesIO(seb_bytes),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=output_filename,
    )


if __name__ == "__main__":
    app.run()
