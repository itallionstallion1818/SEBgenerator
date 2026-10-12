# SEB HackerRank Config Generator

A small Streamlit app for generating Safe Exam Browser (.seb) configuration files tailored for HackerRank contests. It lets you set a contest URL, define a quit/exit password, optionally reuse an existing .seb template, and export a ready-to-use .seb file.

## Features

- Generates a HackerRank-focused SEB config from a contest URL
- Supports a custom quit/exit password that is hashed in the final SEB file
- Lets you reuse an existing unencrypted .seb template and override only key values
- Supports optional launch password encryption for the .seb file
- Includes settings for cookie clearing, private clipboard isolation, and lockdown defaults
- Can also be used from the command line via `seb_generator.py`

## Project Files

- `app.py` — Streamlit web app UI
- `seb_generator.py` — SEB config generation and packaging logic

## Requirements

Python 3.9+ is recommended.

Install the required packages:

```bash
pip install streamlit
```

Optional for encrypted launch passwords:

```bash
pip install rncryptor
```

## Run the Streamlit App

From the project directory:

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Using the App

1. Enter the HackerRank contest URL.
2. Enter a quit/exit password that students or invigilators must use to close SEB.
3. Choose an output filename such as `contest.seb`.
4. Optionally upload a base `.seb` template to preserve custom exam settings.
5. Optionally set a launch password to encrypt the `.seb` file.
6. Click "Generate .seb File".
7. Download the generated file.

## Command-Line Usage

You can also generate a `.seb` file without the UI:

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
- The quit password is stored as a SHA-256 hash in the generated SEB file, as required by SEB.
- If you use a launch password, students must enter it when opening the generated file.

## License

This project is intended for internal or educational use. Add your preferred license if you plan to distribute it publicly.
