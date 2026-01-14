from django.shortcuts import redirect


def home(request):
    """
    Redirect to ID verification page (signup flow).
    """
    return redirect('id_verification_page')