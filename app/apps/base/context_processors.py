from .models import SiteSettings


def site_settings(request):
    settings = SiteSettings.load()
    return {
        'site_name': settings.site_name,
        'site_organization': settings.organization,
        'site_address': settings.address,
        'site_phone': settings.phone,
        'site_logo': settings.logo.url if settings.logo else None,
    }

