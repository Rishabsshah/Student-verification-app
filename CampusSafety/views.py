from django.http import JsonResponse


def home(request):
    """
    Simple home view for the Campus Safety API.
    """
    return JsonResponse({
        "message": "Campus Safety API is running!",
        "endpoints": {
            "login": "/api/accounts/login/",
            "verification": "/api/verification/verify/"
        },
        "docs": "Use Postman or curl to test the APIs"
    })