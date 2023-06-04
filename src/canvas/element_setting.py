from src.toolbar.pdf_viewer_toolbar_item import PdfViewerToolbarItem

SETTING_TABLE = {
    PdfViewerToolbarItem.SafeArea: {
        True: {
            True:   {'outline': 'black', 'fill': 'black', 'dash': None, 'width': 1},
            False:  {'outline': 'gray40', 'fill': 'gray40', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    PdfViewerToolbarItem.Visibility: {
        True: {
            True:   {'outline': 'green', 'fill': 'green', 'dash': None, 'width': 2},
            False:  {'outline': 'red', 'fill': 'red', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    PdfViewerToolbarItem.MergeAndSplit: {
        True: {
            True: {
                True:   {'outline': 'green', 'fill': 'green', 'dash': None, 'width': 2},
                False:  {'outline': 'coral', 'fill': 'coral', 'dash': (3, 2), 'width': 1},
            },
            False:  {'outline': 'black', 'fill': 'black', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    'default': {
        True: {
            True:   {'outline': 'green', 'fill': 'green', 'dash': None, 'width': 2},
            False:  {'outline': 'black', 'fill': 'black', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    }
}

def get_setting(mode, safe, visible, can_be_split):
    settings = SETTING_TABLE.get(mode, SETTING_TABLE['default'])
    if isinstance(settings[safe], dict):
        settings = settings[safe].get(visible, settings[safe])
        if isinstance(settings, dict):
            settings = settings.get(can_be_split, settings)
    else:
        settings = settings[safe]
    return settings
