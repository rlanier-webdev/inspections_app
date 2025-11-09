from django import forms
from django.contrib.auth.models import User
from .models import AppUser

class AppUserForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = AppUser
        fields = ['role', 'phone_number', 'is_staff', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # populate initial values from linked User safely
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = getattr(self.instance.user, 'first_name', '')
            self.fields['last_name'].initial = getattr(self.instance.user, 'last_name', '')
            self.fields['email'].initial = getattr(self.instance.user, 'email', '')
        else:
            # Disable name/email fields if user is missing
            self.fields['first_name'].widget.attrs['readonly'] = True
            self.fields['last_name'].widget.attrs['readonly'] = True
            self.fields['email'].widget.attrs['readonly'] = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        # Check uniqueness among other users
        user_pk = getattr(self.instance.user, 'pk', None)
        if User.objects.filter(email=email).exclude(pk=user_pk).exists():
            raise forms.ValidationError("This email is already used by another user.")
        return email

    def save(self, commit=True):
        app_user = super().save(commit=False)
        if not app_user.user:
            raise forms.ValidationError("Linked User is missing. Cannot save profile.")
        
        # Update linked User fields
        user = app_user.user
        user.first_name = self.cleaned_data.get('first_name', user.first_name)
        user.last_name = self.cleaned_data.get('last_name', user.last_name)
        user.email = self.cleaned_data.get('email', user.email)
        user.save()

        # Sync is_staff if superuser
        if user.is_superuser:
            app_user.is_staff = True

        if commit:
            app_user.save()
        return app_user
