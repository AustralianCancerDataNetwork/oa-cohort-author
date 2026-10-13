"""Per-report indicator labels in the authoring surface.

The authoring tool reads overrides but does not write them -- they are maintained directly
against the workbench database. Two things follow, and both are tested here: every
report-scoped view has to *show* the report's own wording, and no code path in the tool may
silently destroy an override, because nothing here can put one back.
"""

from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as so
from oa_cohorts.cli.config_import import import_config_directory
from oa_cohorts.core import RuleCombination
from oa_cohorts.query.indicator import Indicator
from oa_cohorts.query.measure import Measure, MeasureRelationship, MeasureTemporalWindow
from oa_cohorts.query.report import Report, ReportIndicatorMap

from oa_cohort_author import AuthoringService, EntityKind
from oa_cohort_author.models import ParentRef, RelationKind
from oa_cohort_author.mutations import DIRECT_MUTABLE_FIELDS
from tests.helpers import _build_config_dir

CANONICAL = "Test indicator"
LUNG_LABEL = "Presented at Lung MDT meeting"


def _shared_indicator_setup(tmp_path):
    """The fixture's one indicator, shared with a second report that restates it.

    Report 1 inherits; report 2 overrides every field. That way a view showing canonical
    text where it should show the override is visibly wrong rather than coincidentally
    right.
    """
    config_dir = _build_config_dir(tmp_path / "config")
    engine = sa.create_engine("sqlite://")
    session_factory = so.sessionmaker(bind=engine, future=True)

    with session_factory() as session:
        import_config_directory(config_dir, session)
        session.add(
            Report(
                report_id=2,
                report_name="Lung Cancer MDT",
                report_short_name="lung_mdt",
                report_description="d",
                report_author="Author",
            )
        )
        session.flush()
        session.add(
            ReportIndicatorMap(
                report_id=2,
                indicator_id=1,
                indicator_label_override=LUNG_LABEL,
                indicator_reference_override="LUCAP 3.1",
                benchmark_override=85,
                benchmark_unit_override="percent",
            )
        )
        session.commit()

    return session_factory


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------


def test_the_report_workspace_shows_each_report_its_own_label(tmp_path):
    """Two workspaces over one indicator must not read the same.

    If the authoring view showed canonical text while the dashboard showed the override,
    whoever noticed would correct the canonical row -- putting back exactly the wording the
    overrides exist to remove.
    """
    session_factory = _shared_indicator_setup(tmp_path)
    service = AuthoringService()

    with session_factory() as session:
        inheriting = service.get_report_workspace(session, 1)
        overriding = service.get_report_workspace(session, 2)

    assert [node.label for node in inheriting.indicators] == [CANONICAL]
    assert [node.label for node in overriding.indicators] == [LUNG_LABEL]
    assert [node.entity_id for node in overriding.indicators] == [1]


def test_the_indicator_detail_keeps_canonical_and_names_the_restatement(tmp_path):
    """This view spans reports, so it cannot resolve one label -- it lists them."""
    session_factory = _shared_indicator_setup(tmp_path)
    service = AuthoringService()

    with session_factory() as session:
        detail = service.get_entity_detail(session, EntityKind.indicator, 1)

    assert detail.detail_view is not None
    summary = {row.label: row.value for row in detail.detail_view.summary_sections[0].rows}
    assert summary["Description"] == CANONICAL

    reports_section = detail.detail_view.secondary_sections[-1]
    assert reports_section.title == "Reports"
    by_report = {row.label: row.value for row in reports_section.rows}

    assert LUNG_LABEL in by_report["Lung Cancer MDT"]
    assert "restates label, reference, benchmark, benchmark unit" in by_report["Lung Cancer MDT"]
    # The inheriting report has nothing to restate, so it is not spelled out.
    assert "restates" not in by_report["Test report"]


# --------------------------------------------------------------------------
# Not destroying anything
# --------------------------------------------------------------------------


def test_cloning_an_indicator_for_edit_carries_the_overrides_across(tmp_path):
    """The link is repointed, not replaced.

    A delete-and-reinsert would drop the override columns, and nothing in this tool can
    re-enter them -- they are typed by hand against the workbench.
    """
    session_factory = _shared_indicator_setup(tmp_path)
    service = AuthoringService()

    with session_factory() as session:
        result = service.clone_for_edit(
            session,
            EntityKind.indicator,
            1,
            ParentRef(relation=RelationKind.report_indicator, parent_id=2),
        )
        assert result.ok, result.errors
        clone_id = result.entity_id

    assert clone_id != 1

    with session_factory() as session:
        # Report 2 now points at the clone, with its wording intact.
        moved = session.get(ReportIndicatorMap, (2, clone_id))
        assert moved is not None
        assert moved.indicator_label_override == LUNG_LABEL
        assert moved.indicator_reference_override == "LUCAP 3.1"
        assert moved.benchmark_override == 85
        assert moved.benchmark_unit_override == "percent"

        # The old link is gone, and report 1 is untouched.
        assert session.get(ReportIndicatorMap, (2, 1)) is None
        assert session.get(ReportIndicatorMap, (1, 1)) is not None

        clone = session.get(Indicator, clone_id)
        assert clone.indicator_description == CANONICAL
        assert clone.numerator_measure_id == 2
        assert clone.denominator_measure_id == 1


def test_cloning_an_indicator_no_longer_raises_on_absent_fields(tmp_path):
    """Regression: the clone path passed eight names Indicator does not have.

    ``numerator_label`` and ``denominator_label`` are read-only properties over the measure
    names, and the ``temporal_*`` fields were removed from the model, so construction failed
    with ``AttributeError: property 'numerator_label' ... has no setter`` before any SQL ran.
    The path had therefore never worked.
    """
    session_factory = _shared_indicator_setup(tmp_path)
    service = AuthoringService()

    with session_factory() as session:
        result = service.clone_for_edit(
            session,
            EntityKind.indicator,
            1,
            ParentRef(relation=RelationKind.report_indicator, parent_id=1),
        )

    assert result.ok, result.errors
    assert result.detail is not None


def test_the_indicator_mutable_fields_are_all_real_columns():
    """The whitelist should not advertise an editable field that cannot be set."""
    columns = {column.name for column in Indicator.__table__.columns}

    assert DIRECT_MUTABLE_FIELDS[EntityKind.indicator] <= columns


def test_patient_grain_survives_clone_read_and_edit(tmp_path):
    session_factory = _shared_indicator_setup(tmp_path)
    service = AuthoringService()
    with session_factory() as session:
        source = session.get(Indicator, 1)
        source.grain = "patient"
        source.opportunity_selection = "first"
        source.numerator_reference = "denominator"
        source.period_date_source = "completion"
        source.undated_numerator_policy = "presence"
        session.commit()
        result = service.clone_for_edit(session, EntityKind.indicator, 1,
                                        ParentRef(relation=RelationKind.report_indicator, parent_id=2))
        assert result.ok, result.errors
        assert result.entity_id is not None
        clone = session.get(Indicator, result.entity_id)
        assert clone.grain == "patient"
        assert clone.opportunity_selection == "first"
        assert clone.numerator_reference == "denominator"
        assert clone.period_date_source == "completion"
        assert clone.undated_numerator_policy == "presence"
        fields = service.get_entity_detail(session, EntityKind.indicator, result.entity_id).fields
        assert fields["grain"] == "patient"
        assert fields["opportunity_selection"] == "first"
        assert fields["numerator_reference"] == "denominator"
        assert fields["period_date_source"] == "completion"
        assert fields["undated_numerator_policy"] == "presence"
        updated = service.update_entity(
            session,
            EntityKind.indicator,
            result.entity_id,
            {
                "grain": "episode",
                "opportunity_selection": "any",
                "numerator_reference": "cohort",
                "period_date_source": "numerator",
                "undated_numerator_policy": "exclude",
                "numerator_measure_id": 2,
                "denominator_measure_id": 1,
            },
        )
        assert updated.ok, updated.errors
        assert session.get(Indicator, result.entity_id).grain == "episode"
        assert session.get(Indicator, result.entity_id).period_date_source == "numerator"
        assert session.get(Indicator, 1).grain == "patient"


def test_measure_window_policy_survives_clone_and_detail(tmp_path):
    session_factory = _shared_indicator_setup(tmp_path)
    service = AuthoringService()
    with session_factory() as session:
        parent = session.scalar(sa.select(Measure).order_by(Measure.measure_id))
        assert parent is not None
        window = Measure(name="window", combination=RuleCombination.rule_and, matching_scope="treatment")
        session.add(window)
        session.flush()
        session.add(
            MeasureTemporalWindow(
                measure_id=window.measure_id,
                anchor_measure_id=parent.measure_id,
                candidate_measure_id=parent.measure_id,
                window_min_days=0,
                window_max_days=14,
                anchor_selection="latest",
                anchor_order_date_role="end",
                anchor_date_role="start",
                candidate_date_role="completion",
            )
        )
        session.add(
            MeasureRelationship(
                parent_measure_id=parent.measure_id,
                child_measure_id=window.measure_id,
            )
        )
        session.commit()

        result = service.clone_for_edit(
            session,
            EntityKind.measure,
            window.measure_id,
            ParentRef(relation=RelationKind.measure_child, parent_id=parent.measure_id),
        )

        assert result.ok, result.errors
        assert result.entity_id is not None
        clone = session.get(Measure, result.entity_id)
        assert clone is not None
        assert clone.window_config is not None
        assert clone.matching_scope == "treatment"
        assert clone.window_config.anchor_selection == "latest"
        assert clone.window_config.anchor_order_date_role == "end"
        assert clone.window_config.anchor_date_role == "start"
        assert clone.window_config.candidate_date_role == "completion"
        fields = service.get_entity_detail(session, EntityKind.measure, result.entity_id).fields
        assert fields["matching_scope"] == "treatment"
        assert fields["anchor_selection"] == "latest"
        assert fields["anchor_order_date_role"] == "end"
        assert fields["anchor_date_role"] == "start"
        assert fields["candidate_date_role"] == "completion"
