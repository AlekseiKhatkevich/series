import os

from archives import models


def save_image_path(instance: 'models.ImageModel', filename: str) -> str:
    """
        Custom path for saving images depend on a series name or season number.
        """
    if isinstance(instance.content_object, models.TvSeriesModel):
        _path = os.path.join(
            instance.content_object.name,
            filename
        )
    elif isinstance(instance.content_object, models.SeasonModel):
        _path = os.path.join(
            instance.content_object.series.name,
            str(instance.content_object.season_number),
            filename
        )
    else:
        _path = os.path.join(
            'uploads/images/',
            filename
        )
    return os.path.normpath(_path)
