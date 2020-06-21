from rest_framework import renderers


class BaseBinaryRenderer(renderers.BaseRenderer):
    """
    Base class for binary renderers.
    """
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class JPEGRenderer(BaseBinaryRenderer):
    """
    JPG image binary renderer.
    """
    media_type = 'image/jpeg'
    format = 'jpg'


class GIFRenderer(BaseBinaryRenderer):
    """
    GIF image binary renderer.
    """
    media_type = 'image/gif'
    format = 'gif'

