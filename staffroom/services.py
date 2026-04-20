from .models import StaffWallet


def get_user_wallet(user):
    wallet, _ = StaffWallet.objects.get_or_create(user=user)
    return wallet
