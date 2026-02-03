# judges/__init__.py

# Import the new professional classes from the new files
from .pattern_model import PatternModel
from .anomaly_model import AnomalyModel
from .network_model import NetworkModel

# This allows you to do: from judges import PatternModel
__all__ = ["PatternModel", "AnomalyModel", "NetworkModel"]