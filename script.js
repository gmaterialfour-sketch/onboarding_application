const form = document.getElementById("upload-form");
const statusBox = document.getElementById("status");
const submitButton = form.querySelector("button");
const DEFAULT_BACKEND_URL = "http://127.0.0.1:8002";

function showStatus(message, type) {
    statusBox.hidden = false;
    statusBox.className = `status ${type}`;
    statusBox.textContent = message;
}

function hideStatus() {
    statusBox.hidden = true;
    statusBox.textContent = "";
}

function buildPayload() {
    const file = document.getElementById("file").files[0];
    const payload = new FormData();

    if (!file) {
        throw new Error("Select Excel file.");
    }

    payload.append("file", file);
    payload.append("party_id", document.getElementById("party-id").value || "SEKURA");
    payload.append("site_ref_key", document.getElementById("site-ref-key").value || "");
    return payload;
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideStatus();
    submitButton.disabled = true;
    submitButton.textContent = "Processing...";

    try {
        const configuredBackend = document.getElementById("backend-url").value || DEFAULT_BACKEND_URL;
        const backendUrl = configuredBackend.replace(/\/$/, "");
        const response = await fetch(`${backendUrl}/api/onboarding/process/`, {
            method: "POST",
            body: buildPayload(),
        });

        if (!response.ok) {
            let message = "Output generation failed.";
            try {
                const data = await response.json();
                message = (data.errors || [message]).join(" ");
            } catch {
                message = await response.text();
            }
            throw new Error(message);
        }

        const blob = await response.blob();
        const downloadUrl = URL.createObjectURL(blob);
        const link = document.createElement("a");
        const disposition = response.headers.get("Content-Disposition") || "";
        const match = disposition.match(/filename="?([^"]+)"?/);

        link.href = downloadUrl;
        link.download = match ? match[1] : "onboarding_output.zip";
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(downloadUrl);
        hideStatus();
    } catch (error) {
        const message = error.message === "Failed to fetch"
            ? "Backend not reachable. Start Django on http://127.0.0.1:8002 or deploy Django and set that backend URL in index.html."
            : error.message;
        showStatus(message, "error");
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Download Output";
    }
});
