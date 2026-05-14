const form = document.getElementById("upload-form");
const validateButton = document.getElementById("validate-btn");
const statusBox = document.getElementById("status");

function setStatus(message, type = "") {
    statusBox.className = `status ${type}`.trim();
    statusBox.textContent = message;
}

function getBackendUrl() {
    return document.getElementById("backend-url").value.replace(/\/$/, "");
}

function buildPayload() {
    const file = document.getElementById("file").files[0];
    const partyId = document.getElementById("party-id").value.trim();
    const siteRefKey = document.getElementById("site-ref-key").value.trim();
    const payload = new FormData();

    if (!file) {
        throw new Error("Please choose an onboarding Excel file.");
    }

    payload.append("file", file);
    payload.append("party_id", partyId || "SEKURA");
    payload.append("site_ref_key", siteRefKey);
    return payload;
}

async function validateWorkbook() {
    try {
        setStatus("Validating workbook...");
        const response = await fetch(`${getBackendUrl()}/api/onboarding/validate/`, {
            method: "POST",
            body: buildPayload(),
        });
        const data = await response.json();

        if (!response.ok || !data.ok) {
            throw new Error((data.errors || ["Validation failed."]).join(" "));
        }

        const sheets = Object.entries(data.result.sheets)
            .map(([name, count]) => `${name}: ${count} rows`)
            .join(", ");
        setStatus(`Workbook is valid. ${sheets}`, "ok");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function generatePackage(event) {
    event.preventDefault();

    try {
        setStatus("Generating Excel and SQL package...");
        const response = await fetch(`${getBackendUrl()}/api/onboarding/process/`, {
            method: "POST",
            body: buildPayload(),
        });

        if (!response.ok) {
            let message = "Package generation failed.";
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
        setStatus("Package generated. Download started.", "ok");
    } catch (error) {
        setStatus(error.message, "error");
    }
}

form.addEventListener("submit", generatePackage);
validateButton.addEventListener("click", validateWorkbook);
