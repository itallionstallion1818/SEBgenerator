import gzip
import hashlib
import io
import unittest

from app import app
from seb_generator import get_default_hackerrank_config, pack_seb_bytes, unpack_seb_bytes


class GeneratorWebAppTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_homepage_serves_generator_form(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"HackerRank contest URL", response.data)
        self.assertIn(b"/static/app.js", response.data)

    def test_generates_default_config_and_sanitizes_filename(self):
        response = self.client.post(
            "/api/generate",
            data={
                "contest_url": "https://www.hackerrank.com/contests/sample",
                "quit_password": "exit-secret",
                "output_filename": "../my exam",
                "clear_cookies": "true",
                "private_clipboard": "true",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('filename=my_exam.seb', response.headers["Content-Disposition"])
        config = unpack_seb_bytes(response.data)
        self.assertEqual(config["startURL"], "https://www.hackerrank.com/contests/sample")
        self.assertEqual(
            config["hashedQuitPassword"],
            hashlib.sha256(b"exit-secret").hexdigest(),
        )
        self.assertTrue(config["examSessionClearCookiesOnStart"])
        self.assertTrue(config["examSessionClearCookiesOnEnd"])
        self.assertTrue(config["enablePrivateClipboard"])

    def test_template_settings_are_preserved(self):
        template_config = get_default_hackerrank_config()
        template_config["enablePrivateClipboard"] = False
        template_config["showTaskBar"] = False
        template = pack_seb_bytes(template_config)

        response = self.client.post(
            "/api/generate",
            data={
                "contest_url": "https://www.hackerrank.com/contests/sample",
                "quit_password": "exit-secret",
                "clear_cookies": "true",
                "private_clipboard": "true",
                "template": (io.BytesIO(template), "base.seb"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        config = unpack_seb_bytes(response.data)
        self.assertFalse(config["enablePrivateClipboard"])
        self.assertFalse(config["showTaskBar"])
        self.assertEqual(config["startURL"], "https://www.hackerrank.com/contests/sample")

    def test_invalid_required_fields_and_urls_are_rejected(self):
        missing_password = self.client.post(
            "/api/generate",
            data={"contest_url": "https://www.hackerrank.com/contests/sample"},
        )
        invalid_url = self.client.post(
            "/api/generate",
            data={"contest_url": "javascript:alert(1)", "quit_password": "exit-secret"},
        )

        self.assertEqual(missing_password.status_code, 400)
        self.assertEqual(invalid_url.status_code, 400)

    def test_corrupt_template_returns_a_client_error(self):
        response = self.client.post(
            "/api/generate",
            data={
                "contest_url": "https://www.hackerrank.com/contests/sample",
                "quit_password": "exit-secret",
                "template": (io.BytesIO(b"not a SEB file"), "bad.seb"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Unrecognized .seb file structure", response.data)

    def test_oversized_upload_returns_a_client_error(self):
        response = self.client.post(
            "/api/generate",
            data={
                "contest_url": "https://www.hackerrank.com/contests/sample",
                "quit_password": "exit-secret",
                "template": (io.BytesIO(b"x" * 4_400_000), "large.seb"),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 413)

    def test_optional_launch_password_encrypts_the_configuration(self):
        response = self.client.post(
            "/api/generate",
            data={
                "contest_url": "https://www.hackerrank.com/contests/sample",
                "quit_password": "exit-secret",
                "entry_password": "launch-secret",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(gzip.decompress(response.data)[:4], b"pswd")

    def test_hackerrank_freeze_prevention_settings(self):
        response = self.client.post(
            "/api/generate",
            data={
                "contest_url": "https://www.hackerrank.com/contests/sample",
                "quit_password": "exit-secret",
            },
        )
        self.assertEqual(response.status_code, 200)
        config = unpack_seb_bytes(response.data)

        # Ensure links open in same window to avoid frozen/unfocused background windows
        self.assertEqual(config["newBrowserWindowByLinkPolicy"], 1)
        self.assertEqual(config["newBrowserWindowByScriptPolicy"], 1)

        # Ensure Browser Exam Key request hashing is disabled (prevents network stall on HackerRank SPA)
        self.assertFalse(config["sendBrowserExamKey"])
        self.assertFalse(config["browserURLSalt"])

        # Ensure Esc key is allowed so Monaco editor autocompletion does not trap focus
        self.assertTrue(config["enableEsc"])

        # Ensure camera and microphone access are permitted for proctoring without hanging
        self.assertTrue(config["allowVideoCapture"])
        self.assertTrue(config["allowAudioCapture"])


if __name__ == "__main__":
    unittest.main()
