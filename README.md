# SEB HackerRank Config Generator

A web app for generating Safe Exam Browser (`.seb`) configuration files for HackerRank contests. The interface and Python generation endpoint are served together, so the complete app can be deployed to Vercel.

## Features

- Generates a HackerRank-focused SEB config from a contest URL
- Hashes the quit/exit password with SHA-256
- Accepts an optional unencrypted `.seb` template and preserves its exam settings
- Optionally encrypts the generated file with a launch password
- Supports cookie clearing and private clipboard settings for default configs
- Includes a command-line interface

## Run locally

Python 3.9+ is recommended.

```bash
pip install -r requirements.txt
flask --app app run
```

Open <http://127.0.0.1:5000>.

## Deploy to Vercel

1. Push this project to a GitHub repository.
2. In Vercel, create a project by importing that repository.
3. Keep the project root at the directory containing `app.py` and `requirements.txt`. Vercel detects the Python app and installs its dependencies.
4. Deploy. The generated Vercel URL serves the frontend and its `/api/generate` endpoint.

The app does not store uploaded templates or passwords. Template uploads are limited to 4 MB to fit within serverless request limits. Use HTTPS when sharing the public deployment.

## Using the web app

1. Enter the HackerRank contest URL and a quit/exit password.
2. Choose an output filename.
3. Optionally open **Advanced options** to upload an unencrypted base `.seb` template or set a launch password.
4. Generate and download the configuration.

The cookie and clipboard options apply to a generated default config. When a template is uploaded, its existing settings are preserved while the contest URL and quit password are replaced.

## Command-line usage

```bash
python seb_generator.py --url "https://www.hackerrank.com/contests/your-contest-slug" --quit-pass "your-exit-password" --out contest.seb
```

Optional template and launch password:

```bash
python seb_generator.py \
  --url "https://www.hackerrank.com/contests/your-contest-slug" \
  --quit-pass "your-exit-password" \
  --template existing-template.seb \
  --entry-pass "launch-password" \
  --out contest.seb
```

## Notes

- Template files must be unencrypted before being uploaded or used as a base config.
- The quit password is stored as a SHA-256 hash in the generated SEB file.
- If you set a launch password, students must enter it when opening the file.
