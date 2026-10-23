const form = document.querySelector("#generator-form");
const generateButton = document.querySelector("#generate-button");
const buttonLabel = generateButton.querySelector(".button-label");
const message = document.querySelector("#form-message");
const templateInput = document.querySelector("#template-file");
const maxTemplateSize = 4 * 1024 * 1024;

function showMessage(text, kind = "error") {
  message.textContent = text;
  message.classList.toggle("success", kind === "success");
  message.hidden = false;
}

function hideMessage() {
  message.hidden = true;
  message.textContent = "";
  message.classList.remove("success");
}

templateInput.addEventListener("change", () => {
  const file = templateInput.files[0];
  if (file && file.size > maxTemplateSize) {
    showMessage("The template is too large. Choose a file smaller than 4 MB.");
  } else {
    hideMessage();
  }
});

document.querySelectorAll(".password-toggle").forEach((toggleButton) => {
  toggleButton.addEventListener("click", () => {
    const targetId = toggleButton.dataset.target;
    const input = document.getElementById(targetId);
    if (!input) return;

    const isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";
    toggleButton.setAttribute("aria-pressed", isPassword ? "true" : "false");
    toggleButton.setAttribute(
      "aria-label",
      isPassword ? "Hide password" : "Show password"
    );
    toggleButton.setAttribute(
      "title",
      isPassword ? "Hide password" : "Show password"
    );
    input.focus();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();

  const template = templateInput.files[0];
  if (template && template.size > maxTemplateSize) {
    showMessage("The template is too large. Choose a file smaller than 4 MB.");
    return;
  }

  generateButton.disabled = true;
  buttonLabel.textContent = "Generating…";

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      body: new FormData(form),
    });

    if (!response.ok) {
      const result = await response.json();
      showMessage(result.error || "The configuration could not be generated.");
      return;
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const download = document.createElement("a");
    download.href = objectUrl;
    download.download = response.headers
      .get("Content-Disposition")
      ?.match(/filename="?([^";]+)"?/)?.[1] || "contest.seb";
    document.body.append(download);
    download.click();
    download.remove();
    URL.revokeObjectURL(objectUrl);
    showMessage("Your .seb configuration is ready and has been downloaded.", "success");
  } catch {
    showMessage("Could not reach the generator. Check your connection and try again.");
  } finally {
    generateButton.disabled = false;
    buttonLabel.textContent = "Generate configuration";
  }
});
