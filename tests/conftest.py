from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_SRC = REPO_ROOT / "src"
PUBLIC_ROOT = REPO_ROOT.parent / "OA_cohorts-1"
PUBLIC_SRC = PUBLIC_ROOT / "src"
if str(PRIVATE_SRC) not in sys.path:
    sys.path.insert(0, str(PRIVATE_SRC))
if str(PUBLIC_SRC) not in sys.path:
    sys.path.insert(0, str(PUBLIC_SRC))
if str(PUBLIC_ROOT) not in sys.path:
    sys.path.insert(0, str(PUBLIC_ROOT))


import sqlalchemy as sa
import pytest
from oa_cohorts.core import RuleTarget
from oa_cohorts.measurables.measurable_base import MeasurableBase, MeasurableSpec, MeasurableDomain


test_events = sa.table(
    "test_events",
    sa.column("person_id"),
    sa.column("episode_id"),
    sa.column("event_date"),
    sa.column("concept_id"),
    sa.column("value_number"),
)


class ExecutableMeasurable(MeasurableBase):
    __measurable__ = MeasurableSpec(
        domain=MeasurableDomain.dx,
        label="Executable",
        person_id_attr="person_id",
        episode_id_attr="episode_id",
        event_date_attr="event_date",
        value_concept_attr="concept_id",
        value_numeric_attr="value_number",
    )

    person_id = test_events.c.person_id
    episode_id = test_events.c.episode_id
    event_date = test_events.c.event_date
    concept_id = test_events.c.concept_id
    value_number = test_events.c.value_number


class NoNumericMeasurable(MeasurableBase):
    __measurable__ = MeasurableSpec(
        domain=MeasurableDomain.dx,
        label="No numeric",
        person_id_attr="person_id",
        episode_id_attr="episode_id",
        event_date_attr="event_date",
        value_concept_attr="concept_id",
    )

    person_id = test_events.c.person_id
    episode_id = test_events.c.episode_id
    event_date = test_events.c.event_date
    concept_id = test_events.c.concept_id


@pytest.fixture
def patch_measurable_registry(monkeypatch):
    registry = {
        RuleTarget.dx_any: ExecutableMeasurable,
        RuleTarget.meas_concept: NoNumericMeasurable,
    }
    monkeypatch.setattr("oa_cohorts.query.subquery.get_measurable_registry", lambda: registry)
    monkeypatch.setattr("oa_cohorts.query.query_rule.get_measurable_registry", lambda: registry)
    return registry
