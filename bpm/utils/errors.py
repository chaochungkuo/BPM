class BpmError(Exception):
    """Base BPM error."""


class YamlError(BpmError):
    """YAML load/dump error."""


class ValidationError(BpmError):
    """Descriptor or model validation error."""