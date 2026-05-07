from __future__ import annotations

import csv
from pathlib import Path


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_config_dir(config_dir: Path) -> Path:
    config_dir.mkdir(parents=True, exist_ok=True)

    _write_csv(
        config_dir / "phenotype.csv",
        ["phenotype_id", "phenotype_name", "description"],
        [
            {"phenotype_id": 1, "phenotype_name": "nsclc", "description": ""},
        ],
    )
    _write_csv(
        config_dir / "phenotype_definition.csv",
        ["phenotype_id", "query_concept_id"],
        [
            {"phenotype_id": 1, "query_concept_id": 36561408},
            {"phenotype_id": 1, "query_concept_id": 44500480},
        ],
    )
    _write_csv(
        config_dir / "query_rule.csv",
        [
            "query_rule_id",
            "matcher",
            "concept_id",
            "notes",
            "scalar_threshold",
            "threshold_direction",
            "threshold_comparator",
            "phenotype_id",
        ],
        [
            {
                "query_rule_id": 1,
                "matcher": "exact",
                "concept_id": 36561408,
                "notes": "",
                "scalar_threshold": "",
                "threshold_direction": "",
                "threshold_comparator": "",
                "phenotype_id": "",
            },
            {
                "query_rule_id": 2,
                "matcher": "phenotype",
                "concept_id": "",
                "notes": "",
                "scalar_threshold": "",
                "threshold_direction": "",
                "threshold_comparator": "",
                "phenotype_id": 1,
            },
        ],
    )
    _write_csv(
        config_dir / "subquery.csv",
        ["subquery_id", "target", "temporality", "name", "short_name"],
        [
            {
                "subquery_id": 1,
                "target": "dx_primary",
                "temporality": "dt_current_start",
                "name": "Primary diagnosis",
                "short_name": "primary_dx",
            },
            {
                "subquery_id": 2,
                "target": "dx_primary",
                "temporality": "dt_current_start",
                "name": "Phenotype diagnosis",
                "short_name": "phen_dx",
            },
        ],
    )
    _write_csv(
        config_dir / "subquery_rule_map.csv",
        ["subquery_id", "query_rule_id"],
        [
            {"subquery_id": 1, "query_rule_id": 1},
            {"subquery_id": 1, "query_rule_id": 1},
            {"subquery_id": 2, "query_rule_id": 2},
        ],
    )
    _write_csv(
        config_dir / "measure.csv",
        ["measure_id", "name", "combination", "subquery_id", "person_ep_override"],
        [
            {
                "measure_id": 1,
                "name": "Diagnosis",
                "combination": "or",
                "subquery_id": 1,
                "person_ep_override": False,
            },
            {
                "measure_id": 2,
                "name": "Phenotype measure",
                "combination": "or",
                "subquery_id": 2,
                "person_ep_override": False,
            },
            {
                "measure_id": 3,
                "name": "Composite",
                "combination": "and",
                "subquery_id": "",
                "person_ep_override": False,
            },
        ],
    )
    _write_csv(
        config_dir / "measure_relationship.csv",
        ["parent_measure_id", "child_measure_id"],
        [
            {"parent_measure_id": 3, "child_measure_id": 1},
            {"parent_measure_id": 3, "child_measure_id": 2},
            {"parent_measure_id": 3, "child_measure_id": 2},
        ],
    )
    _write_csv(
        config_dir / "dash_cohort_def.csv",
        ["dash_cohort_def_id", "dash_cohort_def_name", "dash_cohort_def_short_name", "measure_id"],
        [
            {
                "dash_cohort_def_id": 1,
                "dash_cohort_def_name": "Base cohort",
                "dash_cohort_def_short_name": "base",
                "measure_id": 3,
            },
        ],
    )
    _write_csv(
        config_dir / "dash_cohort.csv",
        ["dash_cohort_id", "dash_cohort_name"],
        [
            {"dash_cohort_id": 1, "dash_cohort_name": "Test cohort"},
        ],
    )
    _write_csv(
        config_dir / "dash_cohort_def_map.csv",
        ["dash_cohort_def_id", "dash_cohort_id"],
        [
            {"dash_cohort_def_id": 1, "dash_cohort_id": 1},
            {"dash_cohort_def_id": 1, "dash_cohort_id": 1},
        ],
    )
    _write_csv(
        config_dir / "indicator.csv",
        [
            "indicator_id",
            "indicator_description",
            "indicator_reference",
            "numerator_measure_id",
            "numerator_label",
            "denominator_measure_id",
            "denominator_label",
            "temporal_early",
            "temporal_late",
            "temporal_min",
            "temporal_min_units",
            "temporal_max",
            "temporal_max_units",
            "benchmark",
            "benchmark_unit",
        ],
        [
            {
                "indicator_id": 1,
                "indicator_description": "Test indicator",
                "indicator_reference": "",
                "numerator_measure_id": 2,
                "numerator_label": "Numerator",
                "denominator_measure_id": 1,
                "denominator_label": "Denominator",
                "temporal_early": "dt_current_start",
                "temporal_late": "dt_numerator",
                "temporal_min": "",
                "temporal_min_units": "",
                "temporal_max": "",
                "temporal_max_units": "",
                "benchmark": "",
                "benchmark_unit": "days",
            },
        ],
    )
    _write_csv(
        config_dir / "report.csv",
        [
            "report_id",
            "report_name",
            "report_short_name",
            "report_description",
            "report_create_date",
            "report_edit_date",
            "report_author",
            "report_owner",
        ],
        [
            {
                "report_id": 1,
                "report_name": "Test report",
                "report_short_name": "test",
                "report_description": "Initial description",
                "report_create_date": "2024-05-15",
                "report_edit_date": "2024-05-15",
                "report_author": "Author",
                "report_owner": "",
            },
        ],
    )
    _write_csv(
        config_dir / "report_cohort_map.csv",
        ["report_cohort_map_id", "report_id", "dash_cohort_id", "primary_cohort"],
        [
            {
                "report_cohort_map_id": 1,
                "report_id": 1,
                "dash_cohort_id": 1,
                "primary_cohort": True,
            },
        ],
    )
    _write_csv(
        config_dir / "report_indicator_map.csv",
        ["report_id", "indicator_id"],
        [
            {"report_id": 1, "indicator_id": 1},
            {"report_id": 1, "indicator_id": 1},
        ],
    )
    return config_dir
