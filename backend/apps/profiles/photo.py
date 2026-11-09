def profile_photo_url(user, request=None):
    """Return the authenticated user's current profile photo URL, if any."""
    profile = getattr(user, "worker_profile", None) or getattr(user, "client_profile", None)
    if not profile:
        return ""
    photo = getattr(profile, "profile_photo", None)
    if photo:
        url = photo.url
        return request.build_absolute_uri(url) if request else url
    # Keep compatibility with older worker records that used a URL field.
    return getattr(profile, "profile_photo_url", "") or ""
