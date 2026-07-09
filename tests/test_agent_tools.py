from __future__ import annotations

from datetime import date
from typing import Any

from tongji.core.errors import UpstreamError
from tongji.tools.service import AgentTools


class FakeSdk:
    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call(self, name: str, params: dict[str, Any] | None = None) -> Any:
        self.calls.append((name, params or {}))
        value = self.responses[name]
        if isinstance(value, Exception):
            raise value
        return value


async def test_current_week_falls_back_to_calendar_calculation():
    sdk = FakeSdk(
        {
            "calendar_current_week": UpstreamError("bad binding"),
            "calendar_current_term": {
                "data": {
                    "schoolCalendar": {
                        "id": 123,
                        "beginDay": "2026-02-23",
                        "weekNum": 20,
                    }
                }
            },
        }
    )

    result = await AgentTools(sdk).current_week(today=date(2026, 3, 4))

    assert result.data == {"week": 2}
    assert result.meta["source"] == "calculated"


async def test_week_schedule_resolves_student_and_term_context():
    sdk = FakeSdk(
        {
            "students_me": {
                "data": {
                    "list": [
                        {
                            "studentId": "student-demo",
                            "campus": "3",
                            "campusI18n": "示例校区",
                        }
                    ]
                }
            },
            "calendar_current_term": {
                "data": {"schoolCalendar": {"id": 123, "beginDay": "2026-02-23"}}
            },
            "timetable_student": {
                "data": [
                    {
                        "courseCode": "DEMO101",
                        "courseName": "示例课程",
                        "weekDay": 1,
                        "weeks": "1-16",
                    }
                ]
            },
            "calendar_current_week": {"data": {"currentWeek": 2}},
        }
    )

    result = await AgentTools(sdk).schedule(today_only=False)

    assert result.data[0]["course_name"] == "示例课程"
    timetable_call = next(call for call in sdk.calls if call[0] == "timetable_student")
    assert timetable_call[1]["student_id"] == "student-demo"
    assert timetable_call[1]["calendar_id"] == 123


async def test_score_rank_resolves_student_and_reports_unavailable():
    sdk = FakeSdk(
        {
            "students_me": {"data": {"list": [{"studentId": "student-demo"}]}},
            "calendar_current_term": {"data": {"schoolCalendar": {"id": 123}}},
            "scores_rank": {"data": None},
        }
    )

    result = await AgentTools(sdk).score_rank()

    assert result.data is None
    assert result.meta["available"] is False
    assert ("scores_rank", {"student_id": "student-demo"}) in sdk.calls
