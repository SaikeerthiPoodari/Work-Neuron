"""Public, presentation-friendly name for the idempotent demo seeder."""

from .seed_demo import Command as SeedDemoCommand


class Command(SeedDemoCommand):
    help = "Populate the complete WorkNeuron demo ecosystem for presentations."
