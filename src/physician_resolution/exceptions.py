class EntityResolutionError(Exception):
    """Base exception for entity resolution pipeline."""

    pass


class DataQualityError(EntityResolutionError):
    """Raised when input data fails validation."""

    pass


class NameParseError(EntityResolutionError):
    """Raised when a name cannot be parsed."""

    def __init__(self, raw_name: str, reason: str = ""):
        self.raw_name = raw_name
        self.reason = reason
        msg = f"Could not parse name: '{raw_name}'"
        if reason:
            msg += f" - {reason}"
        super().__init__(msg)


class NPIConflictError(EntityResolutionError):
    """Raised when NPI conflict cannot be resolved."""

    def __init__(self, cluster_id: str, npis: list[str]):
        self.cluster_id = cluster_id
        self.npis = npis
        super().__init__(f"Cluster {cluster_id} has conflicting NPIs: {npis}")


class DatabaseError(EntityResolutionError):
    """Raised when database operations fail."""

    pass
