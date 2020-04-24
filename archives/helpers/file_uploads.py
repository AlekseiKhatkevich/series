from .. import models


def save_image_path(instance: object, filename: str) -> str:
    """
        Custom path for saving images depend on a series name or season number.
        """
    if isinstance(instance.content_object, models.TvSeriesModel):
        path = f'{instance.content_object.name}/{filename}'
    elif isinstance(instance.content_object, models.SeasonModel):
        path = f'{instance.content_object.series.name}/' \
               f'{instance.content_object.season_number}/' \
               f'{filename}'
    else:
        path = f'uploads/images/{filename}'
    return path
