from src.toolbar.pdf_viewer_toolbar_item import PdfViewerToolbarItem

SETTING_TABLE = {
    PdfViewerToolbarItem.SafeArea: {
        True: {
            True:   {'outline': 'black', 'fill': 'black', 'dash': None, 'width': 1},
            False:  {'outline': 'gray40', 'fill': 'gray40', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'red', 'fill': 'red', 'dash': (5, 3), 'width': 1}
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
                True:   {'outline': 'OliveDrab4', 'fill': 'OliveDrab4', 'dash': None, 'width': 2},
                False:  {'outline': 'coral', 'fill': 'coral', 'dash': (3, 2), 'width': 1},
            },
            False:  {'outline': 'black', 'fill': 'black', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    PdfViewerToolbarItem.JoinAndSplit: {
        True: {
            True: {
                True:   {'outline': 'RoyalBlue3', 'fill': 'RoyalBlue3', 'dash': None, 'width': 2},
                False:  {'outline': 'RosyBrown3', 'fill': 'RosyBrown3', 'dash': (3, 2), 'width': 1},
            },
            False:  {'outline': 'black', 'fill': 'black', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    PdfViewerToolbarItem.Order: {
        True: {
            True: {
                True:   {'outline': 'DarkOrchid4', 'fill': 'DarkOrchid4', 'dash': None, 'width': 2},
                False:  {'outline': 'SkyBlue4', 'fill': 'SkyBlue4', 'dash': (3, 2), 'width': 1},
            },
            False:  {'outline': 'gray40', 'fill': 'gray40', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    PdfViewerToolbarItem.Body: {
        True: {
            True: {
                True:   {'outline': 'SlateBlue4', 'fill': 'SlateBlue4', 'dash': None, 'width': 2},
                False:  {'outline': 'bisque4', 'fill': 'bisque4', 'dash': (3, 2), 'width': 1},
            },
            False:  {'outline': 'black', 'fill': 'black', 'dash': (5, 3), 'width': 1}
        },
        False: {'outline': 'gray80', 'fill': 'gray80', 'dash': (5, 3), 'width': 1}
    },
    PdfViewerToolbarItem.Concat: {
        True: {
            True: {
                0:  {'outline': 'bisque3', 'fill': 'bisque3', 'dash': (5, 3), 'width': 1},
                1:   {'outline': 'DeepPink2', 'fill': 'DeepPink2', 'dash': None, 'width': 2},
                2:   {'outline': 'purple4', 'fill': 'purple4', 'dash': None, 'width': 2},
                3:   {'outline': 'DeepPink2', 'fill': 'DeepPink2', 'dash': (3, 2), 'width': 1},
                4:   {'outline': 'purple4', 'fill': 'purple4', 'dash': (3, 2), 'width': 1},
            },
            False:  {'outline': 'gray40', 'fill': 'gray40', 'dash': (5, 3), 'width': 1}
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

def get_setting(mode, safe, visible, option):
    settings = SETTING_TABLE.get(mode, SETTING_TABLE['default'])
    if isinstance(settings[safe], dict):
        settings = settings[safe].get(visible, settings[safe])
        if isinstance(settings, dict):
            settings = settings.get(option, settings)
    else:
        settings = settings[safe]
    return settings
