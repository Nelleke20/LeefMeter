"""Service layer for day template management."""

from __future__ import annotations

from datetime import date

from src.models.activity import Activity
from src.models.day_template import DayTemplate, DayTemplateEntry
from src.repositories.day_template_repository import DayTemplateRepository
from src.services.activity_service import ActivityService


class DayTemplateService:
    """Manages day templates: create, apply, and delete.

    Uses the Repository pattern for persistence and delegates activity
    creation to the ActivityService.
    """

    def __init__(self, repository: DayTemplateRepository) -> None:
        """Initialise with a day template repository.

        Args:
            repository: Storage backend for day templates.
        """
        self._repo = repository

    def get_by_id(self, template_id: str) -> DayTemplate | None:
        """Return a single day template by its UUID.

        Args:
            template_id: UUID to look up.

        Returns:
            Matching DayTemplate, or None.
        """
        return self._repo.get_by_id(template_id)

    def get_all(self) -> list[DayTemplate]:
        """Return all saved day templates.

        Returns:
            List of all DayTemplate objects.
        """
        return self._repo.get_all()

    def save(self, template: DayTemplate) -> None:
        """Persist a new day template.

        Args:
            template: The DayTemplate to save.
        """
        self._repo.save(template)

    def update(self, template: DayTemplate) -> None:
        """Persist changes to an existing day template.

        Args:
            template: The updated DayTemplate (matched by id).
        """
        self._repo.update(template)

    def delete(self, template_id: str) -> None:
        """Remove a day template by id.

        Args:
            template_id: UUID of the template to delete.
        """
        self._repo.delete(template_id)

    def create_from_day(
        self,
        name: str,
        day_date: date,
        activity_service: ActivityService,
    ) -> None:
        """Save a new day template based on activities for a given date.

        Only activities that have a start_time are included.

        Args:
            name: Human-readable name for the new template.
            day_date: The date whose activities become the template entries.
            activity_service: Service used to fetch the day's activities.
        """
        day = activity_service.get_activities_for_day(day_date)
        entries = [
            DayTemplateEntry(
                activity_name=a.name,
                category=a.category,
                start_time=a.start_time or "00:00",
                duration_minutes=a.duration_minutes,
            )
            for a in day.activities
            if a.start_time is not None
        ]
        self._repo.save(DayTemplate(name=name, entries=entries))

    def apply_to_day(
        self,
        template: DayTemplate,
        target_date: date,
        activity_service: ActivityService,
    ) -> None:
        """Add all template entries as activities on a target date.

        Args:
            template: The day template to apply.
            target_date: The date to receive the activities.
            activity_service: Service used to add each activity.
        """
        for entry in template.entries:
            activity_service.add_activity(
                Activity(
                    name=entry.activity_name,
                    category=entry.category,
                    duration_minutes=entry.duration_minutes,
                    date=target_date,
                    start_time=entry.start_time,
                )
            )
