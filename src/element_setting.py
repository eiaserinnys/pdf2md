from src.pdf_viewer_toolbar_item import PdfViewerToolbarItem

SETTING_TABLE = {
    PdfViewerToolbarItem.SafeArea: {
        True: {
            'visible': {'outline': 'black', 'fill': 'black', 'dash': None, 'width': 1},
            'invisible': {'outline': 'gray40', 'fill': 'gray40', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    PdfViewerToolbarItem.Visibility: {
        True: {
            'visible': {'outline': 'green', 'fill': 'green', 'dash': None, 'width': 2},
            'invisible': {'outline': 'red', 'fill': 'red', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    'default': {
        True: {
            'visible': {'outline': 'green', 'fill': 'green', 'dash': None, 'width': 2},
            'invisible': {'outline': 'black', 'fill': 'black', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    }
}

def get_setting(mode, safe, visible):
    settings = SETTING_TABLE.get(mode, SETTING_TABLE['default'])
    if isinstance(settings[safe], dict):
        settings = settings[safe].get('visible' if visible else 'invisible', settings[safe])
    else:
        settings = settings[safe]
    return settings
