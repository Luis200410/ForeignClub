from __future__ import annotations

from django import template

register = template.Library()


@register.simple_tag
def admin_stage_models(app_list, *object_names):
    """Return model dictionaries matching the given object names."""

    allowed = set(object_names)
    results = []
    for app in app_list:
        for model in app.get("models", []):
            if model.get("object_name") in allowed:
                results.append(model)
    return results


@register.simple_tag
def admin_filtered_app_list(app_list, *exclude_object_names):
    """Return app list with models excluding those in the provided names."""

    exclude = set(exclude_object_names)
    filtered_apps = []
    for app in app_list:
        models = [
            model
            for model in app.get("models", [])
            if model.get("object_name") not in exclude
        ]
        if models:
            filtered_apps.append({**app, "models": models})
    return filtered_apps
