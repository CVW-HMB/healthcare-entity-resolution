"""Evaluation metrics against ground truth."""

from collections import defaultdict

import pandas as pd

from ..logging import get_logger

logger = get_logger("analysis.evaluation")


def load_ground_truth(filepath: str) -> dict[str, str]:
    """
    Load ground truth mapping.

    Returns: source_id -> true_physician_id
    """
    df = pd.read_csv(filepath, dtype=str)

    # The ground truth maps true_physician_id to attributes
    # We need to invert this based on what identifiers we have
    mapping = {}

    for _, row in df.iterrows():
        true_id = row.get("true_physician_id")
        npi = row.get("npi")

        if true_id and npi:
            mapping[npi] = true_id

    logger.info(f"Loaded ground truth with {len(mapping)} entries")

    return mapping


def evaluate_clustering(
    predicted_clusters: list[set[str]],
    source_to_true: dict[str, str],
) -> dict:
    """
    Evaluate clustering against ground truth.

    Metrics:
    - Precision: What % of predicted matches are correct?
    - Recall: What % of true matches did we find?
    - F1: Harmonic mean
    - Adjusted Rand Index: Cluster similarity metric

    Args:
        predicted_clusters: List of sets of source_ids
        source_to_true: Mapping from source_id to true_physician_id

    Returns:
        Dict of evaluation metrics
    """
    # Build predicted pairs
    predicted_pairs = set()
    for cluster in predicted_clusters:
        cluster_list = list(cluster)
        for i, id1 in enumerate(cluster_list):
            for id2 in cluster_list[i + 1 :]:
                pair = tuple(sorted([id1, id2]))
                predicted_pairs.add(pair)

    # Build true pairs
    true_clusters: dict[str, set[str]] = defaultdict(set)
    for source_id, true_id in source_to_true.items():
        true_clusters[true_id].add(source_id)

    true_pairs = set()
    for true_id, cluster in true_clusters.items():
        cluster_list = list(cluster)
        for i, id1 in enumerate(cluster_list):
            for id2 in cluster_list[i + 1 :]:
                pair = tuple(sorted([id1, id2]))
                true_pairs.add(pair)

    # Calculate metrics
    true_positives = len(predicted_pairs & true_pairs)
    false_positives = len(predicted_pairs - true_pairs)
    false_negatives = len(true_pairs - predicted_pairs)

    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0
    )
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "predicted_pairs": len(predicted_pairs),
        "true_pairs": len(true_pairs),
    }


def evaluate_with_ground_truth_df(
    predicted_clusters: list[set[str]],
    records_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
    source_id_col: str = "source_id",
    true_id_col: str = "true_physician_id",
) -> dict:
    """
    Evaluate using DataFrames with true_physician_id columns.

    This handles the case where ground truth is embedded in source data.
    """
    # Build mapping from source records
    source_to_true = {}

    for _, row in records_df.iterrows():
        source_id = row.get(source_id_col)
        true_id = row.get(true_id_col)
        if source_id and true_id:
            source_to_true[source_id] = true_id

    return evaluate_clustering(predicted_clusters, source_to_true)


def analyze_errors(
    predicted_clusters: list[set[str]],
    source_to_true: dict[str, str],
    limit: int = 10,
) -> dict:
    """
    Analyze false positives and false negatives.

    Returns examples of each error type for debugging.
    """
    # Build cluster lookup
    node_to_cluster: dict[str, int] = {}
    for idx, cluster in enumerate(predicted_clusters):
        for node in cluster:
            node_to_cluster[node] = idx

    # Find false positives (predicted same, actually different)
    false_positives = []
    for idx, cluster in enumerate(predicted_clusters):
        cluster_list = list(cluster)
        true_ids = set()
        for node in cluster_list:
            true_id = source_to_true.get(node)
            if true_id:
                true_ids.add(true_id)

        if len(true_ids) > 1:
            false_positives.append(
                {
                    "cluster_idx": idx,
                    "cluster_size": len(cluster),
                    "true_ids_found": list(true_ids),
                    "sample_nodes": cluster_list[:5],
                }
            )

    # Find false negatives (should be same, predicted different)
    true_clusters: dict[str, set[str]] = defaultdict(set)
    for source_id, true_id in source_to_true.items():
        true_clusters[true_id].add(source_id)

    false_negatives = []
    for true_id, true_cluster in true_clusters.items():
        predicted_cluster_ids = set()
        for node in true_cluster:
            if node in node_to_cluster:
                predicted_cluster_ids.add(node_to_cluster[node])

        if len(predicted_cluster_ids) > 1:
            false_negatives.append(
                {
                    "true_id": true_id,
                    "true_cluster_size": len(true_cluster),
                    "split_into_n_clusters": len(predicted_cluster_ids),
                    "sample_nodes": list(true_cluster)[:5],
                }
            )

    return {
        "false_positive_clusters": false_positives[:limit],
        "false_negative_splits": false_negatives[:limit],
        "total_fp_clusters": len(false_positives),
        "total_fn_splits": len(false_negatives),
    }


def generate_evaluation_report(
    predicted_clusters: list[set[str]],
    source_to_true: dict[str, str],
) -> dict:
    """Generate comprehensive evaluation report."""
    report = {
        "metrics": evaluate_clustering(predicted_clusters, source_to_true),
        "error_analysis": analyze_errors(predicted_clusters, source_to_true),
    }

    logger.info(
        f"Evaluation: P={report['metrics']['precision']:.3f}, "
        f"R={report['metrics']['recall']:.3f}, "
        f"F1={report['metrics']['f1_score']:.3f}"
    )

    return report
