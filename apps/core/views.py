from django.shortcuts import render
import logging
import traceback

logger = logging.getLogger("core.errors")

def custom_404(request, exception):
    return render(request, "404.html", status=404)

def custom_403(request, exception=None):
    return render(request, "403.html", status=403)

def custom_500(request):
    # Log detailed error information
    logger.error(
        "500 Error Occurred",
        extra={
            "url": request.build_absolute_uri(),
            "method": request.method,
            "user": request.user.username if request.user.is_authenticated else "Anonymous",
            "ip": request.META.get("REMOTE_ADDR"),
            "user_agent": request.META.get("HTTP_USER_AGENT"),
        }
    )

    return render(request, "500.html", status=500)

