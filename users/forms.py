from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model


class CustomUserCreationForm(UserCreationForm):
    """
    User creation form.
    """
    class Meta(UserCreationForm):
        model = get_user_model()
        fields = ('email', )


class CustomUserChangeForm(UserChangeForm):
    """
     Form for changing user's data.
    """
    class Meta:
        model = get_user_model()
        fields = ('email', )
