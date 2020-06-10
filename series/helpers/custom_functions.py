import inspect
import os
from typing import Callable, Container, Iterable, Optional, Union

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.base import ModelBase
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


MEDIA_ROOT_FULL_PATH = os.path.join(settings.BASE_DIR, settings.MEDIA_ROOT)


def remove_files(path: Optional[str] = MEDIA_ROOT_FULL_PATH) -> None:
    """
    Removes files and sub-folders in chosen folder. Also cleans ImageModel from entries
    that leads to non-existent files.
    """

    assert os.path.exists(path) and os.path.isdir(path), error_codes.WRONG_PATH.message

    media_root_files = set()
    #  All files im MEDIA ROOT.
    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            file_path = os.path.normpath(file_path)
            media_root_files.add(file_path)

    db_files = set()
    #  All alive file path in ImageModel.
    images_in_db = archives.models.ImageModel.objects.all().only('image')
    for image in images_in_db:
        image_path = image.image.path
        #  If image file path is dead -delete image entry.
        if not os.path.exists(image_path):
            image.delete()
        else:
            image_path = os.path.normpath(image_path)
            db_files.add(image_path)
    #  Files in MEDIA_ROOT that are not present in ImageModel and should be deleted.
    files_to_delete = media_root_files - db_files

    assert len(media_root_files) == (len(db_files) + len(files_to_delete)),\
        'Something went really wrong!'

    for file in files_to_delete:
        os.remove(file)

    counter = 0
    #  Delete all empty folders.
    for (dirpath, dirnames, filenames) in os.walk(path):
        for folder in dirnames:
            folder_path = os.path.join(dirpath, folder)
            if os.path.isdir(folder_path) and not os.listdir(folder_path):
                os.rmdir(folder_path)
                counter += 1

    print(
        f'Total - {len(media_root_files)}',
        f'Files in DB - {len(db_files)}',
        f'Deleted - {len(files_to_delete)}',
        f'Deleted  - {counter} empty folders.',
        sep='\n'
    )