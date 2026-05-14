class ApiCorsMiddleware:
    """Allow the static upload page to call Django API endpoints."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/") and request.method == "OPTIONS":
            response = self._empty_response()
        else:
            response = self.get_response(request)

        if request.path.startswith("/api/"):
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response["Access-Control-Expose-Headers"] = "Content-Disposition, X-Onboarding-Summary"
        return response

    def _empty_response(self):
        from django.http import HttpResponse

        return HttpResponse(status=204)
