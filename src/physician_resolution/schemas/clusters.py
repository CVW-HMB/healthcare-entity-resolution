from dataclasses import dataclass, field


@dataclass
class ClusterQuality:
    """Quality metrics for a resolved cluster."""

    cluster_id: str
    size: int
    avg_edge_weight: float
    min_edge_weight: float
    density: float  # edges / possible_edges
    npi_count: int  # distinct NPIs in cluster
    npi_conflict: bool  # True if multiple NPIs
    state_count: int  # distinct states
    specialty_count: int  # distinct specialties
    quality_score: float  # overall quality metric
    warnings: list[str] = field(default_factory=list)

    def has_issues(self) -> bool:
        """Return True if cluster has quality issues."""
        return self.npi_conflict or len(self.warnings) > 0
