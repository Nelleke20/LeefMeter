"""Template management service."""

from __future__ import annotations

from datetime import date

from src.models.activity import Activity
from src.models.template import Template
from src.repositories.template_repository import TemplateRepository
from src.services.activity_service import ActivityService


class TemplateService:
    """Manages reusable activity templates.

    Templates store default name, intensity, and duration. Applying a
    template to a date creates a scored Activity via the ActivityService.
    """

    def __init__(self, repository: TemplateRepository) -> None:
        """Initialise with a template repository.

        Args:
            repository: Storage backend for templates.
        """
        self._repository = repository

    def add_template(self, template: Template) -> Template:
        """Persist a new template.

        Args:
            template: The template to save.

        Returns:
            The saved template.
        """
        self._repository.save(template)
        return template

    def get_all_templates(self) -> list[Template]:
        """Return all stored templates.

        Returns:
            All templates in storage order.
        """
        return self._repository.get_all()

    def update_template(self, template: Template) -> None:
        """Update an existing template (name and/or category).

        Args:
            template: Template with updated fields, matched by id.
        """
        self._repository.update(template)

    def delete_template(self, template_id: str) -> None:
        """Remove a template from storage.

        Args:
            template_id: The UUID of the template to delete.
        """
        self._repository.delete(template_id)

    def apply_template(
        self,
        template: Template,
        day: date,
        activity_service: ActivityService,
    ) -> Activity:
        """Create and score an Activity from a template for a given date.

        Args:
            template: The template to apply.
            day: The date to attach the new activity to.
            activity_service: Service used to score and persist the activity.

        Returns:
            The newly created and scored Activity.
        """
        activity = Activity(
            name=template.name,
            category=template.category,
            duration_minutes=template.duration_minutes,
            date=day,
        )
        return activity_service.add_activity(activity)
