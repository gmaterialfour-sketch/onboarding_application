import logging
import tempfile
from pathlib import Path

from django.core.files.base import File
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import OnboardingJob
from .serializers import OnboardingUploadSerializer
from .services.exceptions import ValidationError
from .services.pipeline import process_onboarding_file, validate_only

logger = logging.getLogger(__name__)


def _save_temp_upload(upload):
    suffix = Path(upload.name).suffix or ".xlsx"
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    with temp:
        for chunk in upload.chunks():
            temp.write(chunk)
    return Path(temp.name)


def _persist_job_artifacts(job, result):
    for field, path_key in [
        ("output_excel", "excel_path"),
        ("output_sql", "sql_path"),
        ("output_zip", "zip_path"),
    ]:
        path = result[path_key]
        with open(path, "rb") as handle:
            getattr(job, field).save(path.name, File(handle), save=False)
    job.site_ref_key = result["summary"]["site_ref_key"]
    job.summary = result["summary"]
    job.status = "COMPLETED"
    job.save()


def upload_view(request):
    if request.method == 'POST':
        serializer = OnboardingUploadSerializer(request.FILES, request.POST)
        if not serializer.is_valid():
            return render(request, 'onboarding/upload.html', {"errors": serializer.errors})

        payload = serializer.validated_data
        temp_path = _save_temp_upload(payload.file)
        payload.file.seek(0)
        job = OnboardingJob.objects.create(
            original_filename=payload.file.name,
            uploaded_file=payload.file,
            party_id=payload.party_id,
            site_ref_key=payload.site_ref_key,
            status="PROCESSING",
        )
        try:
            result = process_onboarding_file(temp_path, party_id=payload.party_id, site_ref_key=payload.site_ref_key or None)
            _persist_job_artifacts(job, result)
            return FileResponse(open(result["zip_path"], "rb"), as_attachment=True, filename=result["zip_path"].name)
        except ValidationError as exc:
            job.status = "FAILED"
            job.error_message = "\n".join(exc.errors)
            job.save(update_fields=["status", "error_message", "updated_at"])
            return render(request, 'onboarding/upload.html', {"errors": {"workbook": exc.errors}})
        except Exception as exc:
            logger.exception("Onboarding failed")
            job.status = "FAILED"
            job.error_message = str(exc)
            job.save(update_fields=["status", "error_message", "updated_at"])
            return render(request, 'onboarding/upload.html', {"errors": {"server": str(exc)}})
        finally:
            temp_path.unlink(missing_ok=True)

    return render(request, 'onboarding/upload.html')


@csrf_exempt
@require_POST
def process_api(request):
    serializer = OnboardingUploadSerializer(request.FILES, request.POST)
    if not serializer.is_valid():
        return JsonResponse({"ok": False, "errors": serializer.errors}, status=400)

    payload = serializer.validated_data
    temp_path = _save_temp_upload(payload.file)
    try:
        result = process_onboarding_file(temp_path, party_id=payload.party_id, site_ref_key=payload.site_ref_key or None)
        response = FileResponse(open(result["zip_path"], "rb"), as_attachment=True, filename=result["zip_path"].name)
        response["X-Onboarding-Summary"] = str(result["summary"])
        return response
    except ValidationError as exc:
        return JsonResponse({"ok": False, "errors": exc.errors}, status=400)
    except Exception as exc:
        logger.exception("Onboarding API failed")
        return JsonResponse({"ok": False, "errors": [str(exc)]}, status=500)
    finally:
        temp_path.unlink(missing_ok=True)


@csrf_exempt
@require_POST
def validate_api(request):
    serializer = OnboardingUploadSerializer(request.FILES, request.POST)
    if not serializer.is_valid():
        return JsonResponse({"ok": False, "errors": serializer.errors}, status=400)

    temp_path = _save_temp_upload(serializer.validated_data.file)
    try:
        return JsonResponse({"ok": True, "result": validate_only(temp_path)})
    except ValidationError as exc:
        return JsonResponse({"ok": False, "errors": exc.errors}, status=400)
    finally:
        temp_path.unlink(missing_ok=True)
