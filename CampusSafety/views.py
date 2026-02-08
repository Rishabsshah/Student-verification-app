from django.shortcuts import redirect, render


def home(request):
    """
    Redirect to ID verification page (signup flow).
    """
    return redirect('id_verification_page')


def triple_lock_test(request):
    """
    Test page for Triple-Lock verification workflow.
    """
    return render(request, 'CampusSafety/triple_lock_test.html')