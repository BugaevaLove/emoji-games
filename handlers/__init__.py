from .start import start_handler, help_handler
from .games import games_conv
from .profile import profile_handler, top_handler, vip_callback
from .admin import admin_conv

handlers = [
    start_handler,
    help_handler,
    games_conv,
    profile_handler,
    top_handler,
    vip_callback,
    admin_conv
]