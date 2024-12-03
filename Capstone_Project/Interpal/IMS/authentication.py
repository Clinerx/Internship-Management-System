# authentication.py

from django.contrib.auth.backends import ModelBackend
from .models import AccountApproval

class ApprovalBasedAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Standard authentication using the default ModelBackend
        user = super().authenticate(request, username=username, password=password, **kwargs)

        # If the user is authenticated, check if their account is approved
        if user:
            try:
                # Check the approval status of the user
                approval = AccountApproval.objects.get(user=user)

                if not approval.is_approved:
                    # If the account is not approved, return None (login fails)
                    return None
            except AccountApproval.DoesNotExist:
                # If there is no AccountApproval entry, also return None (login fails)
                return None

        return user  # If approved, return the user object for successful authentication
