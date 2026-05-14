from .services.pipeline import process_onboarding_file


def process_onboarding(template_path, data_path):
    """Backward-compatible wrapper used by older code paths."""
    result = process_onboarding_file(data_path)
    return result["sql_path"].read_text(encoding="utf-8")
