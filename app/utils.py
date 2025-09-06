import os
import secrets
from datetime import datetime
from .models import Sequence

def generate_policy_number():
    year = datetime.utcnow().strftime("%Y")
    seq = Sequence.next_val(f"policy_{year}")
    return f"POL-{year}-{seq:06d}"

def env_admin_password():
    return os.getenv("ADMIN_PASSWORD", "admin123")
