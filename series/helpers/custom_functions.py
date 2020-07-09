import datetime
import functools
import inspect
import os
from typing import Callable, Container, Iterable, Optional, Tuple, Union

import more_itertools
import numpy
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.base import ModelBase
from psycopg2.extras import DateRange
from rest_framework.response import Response

import archives.models
from series import error_codes


def check_code_inside(func: Callable, code: [Container, Iterable]) -> bool:
    """
    Check whether or not coed snippets(methods, names, etc) inside a callable.
    Use-case: Check if method is overridden.
    """
    source_code = inspect.getsource(func)
    contains_or_not = [snippet for snippet in code if snippet in source_code]
    return bool(contains_or_not)


def response_to_dict(response: Response, /, key_field: str) -> dict:
    """
    Converts DRF response of list view to a nested dictionary  where keys of inner dictionaries
    would be fields specified in key_field
    {
    key_field: {inner nested dict with response.data},
    key_field: {inner nested dict with response.data},
    ...
    }
    """
    return_dict = {}

    # In order to be able to work with paginated and non-paginated responses.
    try:
        data = response.data['results']
    except TypeError:
        data = response.data

    for obj in data:
        try:
            inner_dict = {obj[key_field]: obj}
            return_dict.update(inner_dict)
        except KeyError as err:
            raise KeyError(f'There is no field with name{key_field} in response.data objects') from err

    return return_dict


def key_field_to_field_dict(response: Response, key_field: str, other_field: str) -> dict:
    """
    Returns mapping of {key_field: other_field} based on response.data.
    """
    response_dict = response_to_dict(response, key_field)

    try:
        return_dict = {
            key_field: nested_dict[other_field] for key_field, nested_dict in response_dict.items()
        }
    except KeyError as err:
        raise KeyError(f'There is no field with name{other_field} in response.data objects') from err

    return return_dict


def dict_from_names(*variable_names: str, namespace: Callable = globals) -> dict:
    """
    Returns a dict constructed from variables and their values.
    a = 1
    b = 2
    c = 3
    dict_from_names('a', 'b', 'c') -> {'a': 1, 'b': 2, 'c': 3}
    """
    namespace = namespace()
    return {name: namespace[name] for name in variable_names}


def get_model_fields_subset(
        model: Union[ModelBase, str],
        fields_to_remove: Iterable[str] = (),
        prefix: Optional[str] = None,
) -> set:
    """
       Function builds set of model field's names without certain specified fields in 'fields_to_remove',
        possibly prepended with an optional prefix.
       :param model: Model instance or model name in format app name.model name (users.user).
       :param fields_to_remove: Field names to be removed from final set of fields.
       :param prefix: Prefix to prepend each field name in resulted set. Optional.
       :return: Set of model's field names.
    """

    if isinstance(model, str):
        app_label, model = model.lower().split('.')
        try:
            model = ContentType.objects.get(app_label=app_label, model=model).model_class()
        except ContentType.DoesNotExist as err:
            raise NameError(f'Model with name "{model}" not found in app "{app_label}".') from err

    fields = set(
        f'{prefix}{field.name}' if prefix is not None else field.name
        for field in model._meta.local_fields
        if field.name not in fields_to_remove
    )

    return fields


def clean_garbage_in_folder(path: str = settings.MEDIA_ROOT_FULL_PATH) -> None:
    """
    Removes files and sub-folders in chosen folder. Also cleans ImageModel from entries
    that leads to non-existent files.
    """
    assert path == settings.MEDIA_ROOT_FULL_PATH, 'Temporary assertion.'
    assert os.path.exists(path) and os.path.isdir(path), error_codes.WRONG_PATH.message
    assert not settings.IM_IN_TEST_MODE, error_codes.NOT_IN_TESTS.message

    #  Full path to MEDIA_ROOT.
    media_root_partial = functools.partial(os.path.join, settings.BASE_DIR, settings.MEDIA_ROOT)

    #  Container with all files in MEDIA ROOT.
    media_root_files = set()

    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            file_path = os.path.join(dirpath, file)  # full path here
            file_path = os.path.normpath(file_path)
            media_root_files.add(file_path)

    db_files = set()
    images_to_delete = []

    #  All alive file path in ImageModel.
    images_in_db = archives.models.ImageModel.objects.all().values_list('image', flat=True)
    for image in images_in_db:
        image_path = media_root_partial(image)
        image_path = os.path.normpath(image_path)

        #  If image file path is dead -delete image entry.
        if not os.path.exists(image_path):
            images_to_delete.append(image)
        else:
            db_files.add(image_path)

    deleted_model_instances_count, _ = archives.models.ImageModel.objects.filter(
        image__in=images_to_delete).delete()

    #  Files in MEDIA_ROOT that are not present in ImageModel and should be deleted.
    files_to_delete = media_root_files - db_files

    assert len(media_root_files) == (len(db_files) + len(files_to_delete)),\
        'Something went really wrong!'

    errors_in_delete = []

    for file in files_to_delete:
        try:
            os.remove(file)
        except (PermissionError, OSError):
            errors_in_delete.append(file)

    folders_counter = 0

    #  Delete all empty folders.
    for (dirpath, dirnames, filenames) in os.walk(path):
        for folder in dirnames:
            folder_path = os.path.join(dirpath, folder)
            if os.path.isdir(folder_path) and not os.listdir(folder_path):
                os.rmdir(folder_path)
                folders_counter += 1

    print(
        f'Total files - {len(media_root_files)}',
        f'Files in DB - {len(db_files)}',
        f'Deleted - {len(files_to_delete)} files',
        f'Deleted - {folders_counter} empty folders.',
        f'Deleted - {deleted_model_instances_count} empty model instances.',
        f'{len(errors_in_delete)} errors happened during file deletion process.'
        f' Filenames are --{errors_in_delete}',
        sep='\n'
    )


def available_range(
        outer_range: DateRange,
        *inner_ranges: DateRange,
        delta: int = 1,
) -> Tuple[DateRange]:
    """
    Returns outer range minus all inner ranges .
    ooooooooooooooooooooooooooooo   outer range
      xxxx   xxxxxxxxxx     xx      inner ranges
    yy    yy           yyyyy   yy   result (4 individual ranges)
    """
    #  Construct outer range sequence.
    overall_range = set(
        numpy.arange(
            outer_range.lower,
            outer_range.upper,
            dtype='datetime64[D]')
    )
    #  Construct inner sequences and deduct each from outer range sequence.
    for date_range in inner_ranges:
        overall_range.difference_update(
            set(
                numpy.arange(
                    date_range.lower,
                    date_range.upper,
                    dtype='datetime64[D]'
                )))
    #  Split final dates sequence into individual sequences.
    available_dates_list = more_itertools.split_when(
        sorted(overall_range),
        lambda x, y: abs(x - y) > numpy.timedelta64(delta, 'D')
    )
    #  Convert final date sequences to DateRanges.
    available_ranges = tuple(
        DateRange(
            min(sequence).astype(datetime.date),
            max(sequence).astype(datetime.date),
            '(]') for sequence in available_dates_list
    )
    return available_ranges
