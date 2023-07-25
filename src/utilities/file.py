import os
import uuid

from django.conf import settings
from django.core.files.storage import get_storage_class


def save_image_with_path(image, photo_name):
    """Generate a random filename. Uses DEFAULT_FILE_STORAGE to validate filename"""
    ext = os.path.splitext(photo_name)[1]

    image_path = f'images/{uuid.uuid4()}{ext}'

    fs = get_storage_class()()
    # Generate a new name if exists
    image_path = fs.get_available_name(image_path)

    image.save(os.path.join(settings.MEDIA_ROOT, image_path))

    return image_path
