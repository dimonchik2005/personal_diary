from .forms import UserProfileForm


def profile_settings(request):
    if not request.user.is_authenticated:
        return {}

    return {
        "profile_form": UserProfileForm(
            instance=request.user,
            prefix="profile",
        )
    }
