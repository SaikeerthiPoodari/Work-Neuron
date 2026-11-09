"""Paste into the PythonAnywhere web app's WSGI configuration file.

Replace ``your_pythonanywhere_username`` with the separate WorkNeuron account
username. Keep secrets in backend/.env (not in Git) or in the host environment.
"""

import os
import sys
from pathlib import Path

project_dir = Path("/home/your_pythonanywhere_username/Work-Neuron/backend")
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_production")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

