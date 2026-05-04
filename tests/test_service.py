from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as so

from oa_cohort_author import AuthoringService, EntityKind
from oa_cohorts.cli.config_import import import_config_directory
from tests.helpers import _build_config_dir


def test_list_reports_and_workspace(tmp_path):
    config_dir = _build_config_dir(tmp_path / "config")
    engine = sa.create_engine("sqlite://")
    session_factory = so.sessionmaker(bind=engine, future=True)
    service = AuthoringService()

    with session_factory() as session:
        import_config_directory(config_dir, session)

    with session_factory() as session:
        reports = service.list_reports(session)
        assert len(reports) == 1
        workspace = service.get_report_workspace(session, 1)
        by_short_name = service.get_report_workspace_by_short_name(session, "test")
        rule_detail = service.get_entity_detail(session, EntityKind.query_rule, 1)
        cohort_node = workspace.cohorts[0]
        assert workspace.report_name == "Test report"
        assert by_short_name.report_id == workspace.report_id
        assert workspace.primary_cohort_names == ("Test cohort",)
        assert len(workspace.cohorts) == 1
        assert len(workspace.indicators) == 1
        assert cohort_node.executability is not None
        assert rule_detail.rule_status is not None
        rule_node = workspace.cohorts[0].children[0].children[0].children[0].children[0].children[0]
        assert rule_node.kind is EntityKind.query_rule
        assert rule_node.status_label is not None


def test_entity_detail_reports_shared_measure_usage(tmp_path):
    config_dir = _build_config_dir(tmp_path / "config")
    engine = sa.create_engine("sqlite://")
    session_factory = so.sessionmaker(bind=engine, future=True)
    service = AuthoringService()

    with session_factory() as session:
        import_config_directory(config_dir, session)

    with session_factory() as session:
        detail = service.get_entity_detail(session, EntityKind.measure, 2)
        assert detail.shared is True
        assert detail.allowed_actions["can_clone"] is True
        assert detail.allowed_actions["can_edit"] is False


def test_tailored_detail_views_include_primary_links(tmp_path):
    config_dir = _build_config_dir(tmp_path / "config")
    engine = sa.create_engine("sqlite://")
    session_factory = so.sessionmaker(bind=engine, future=True)
    service = AuthoringService()

    with session_factory() as session:
        import_config_directory(config_dir, session)

    with session_factory() as session:
        indicator = service.get_entity_detail(session, EntityKind.indicator, 1)
        cohort_def = service.get_entity_detail(session, EntityKind.dash_cohort_def, 1)
        measure = service.get_entity_detail(session, EntityKind.measure, 1)
        assert indicator.detail_view is not None
        assert indicator.detail_view.secondary_sections[0].title == "Numerator"
        assert indicator.detail_view.secondary_sections[1].title == "Denominator"
        indicator_rows = indicator.detail_view.secondary_sections[0].rows
        assert indicator_rows[1].link is not None
        assert indicator_rows[1].link.kind is EntityKind.measure
        assert cohort_def.detail_view is not None
        summary_rows = cohort_def.detail_view.summary_sections[0].rows
        assert any(row.link is not None and row.link.kind is EntityKind.measure for row in summary_rows)
        assert cohort_def.detail_view.secondary_sections[0].title == "Measure context"
        assert measure.detail_view is not None
        assert any(section.title == "Definition" for section in measure.detail_view.secondary_sections)
