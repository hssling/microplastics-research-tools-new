from enum import IntFlag

import comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0 as __wrapper_module__
from comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0 import (
    IDispatch, StdFont, FONTSIZE, Color, typelib_path, FONTUNDERSCORE,
    Font, GUID, VgaColor, FONTSTRIKETHROUGH, IFontDisp,
    OLE_XSIZE_PIXELS, OLE_ENABLEDEFAULTBOOL, IEnumVARIANT,
    DISPPROPERTY, CoClass, OLE_OPTEXCLUSIVE, _lcid, IPictureDisp,
    Checked, OLE_XSIZE_HIMETRIC, Unchecked, OLE_YPOS_PIXELS, Default,
    OLE_XPOS_HIMETRIC, Picture, FONTNAME, OLE_XPOS_PIXELS, DISPPARAMS,
    OLE_CANCELBOOL, OLE_COLOR, OLE_YPOS_CONTAINER, COMMETHOD,
    OLE_HANDLE, OLE_YSIZE_HIMETRIC, FontEvents, Gray,
    OLE_XSIZE_CONTAINER, BSTR, IFontEventsDisp, EXCEPINFO, Library,
    VARIANT_BOOL, OLE_YPOS_HIMETRIC, OLE_XPOS_CONTAINER, HRESULT,
    _check_version, DISPMETHOD, FONTITALIC, FONTBOLD, IPicture,
    StdPicture, IUnknown, OLE_YSIZE_CONTAINER, dispid,
    OLE_YSIZE_PIXELS, Monochrome, IFont
)


class OLE_TRISTATE(IntFlag):
    Unchecked = 0
    Checked = 1
    Gray = 2


class LoadPictureConstants(IntFlag):
    Default = 0
    Monochrome = 1
    VgaColor = 2
    Color = 4


__all__ = [
    'Picture', 'StdFont', 'FONTNAME', 'OLE_XPOS_PIXELS', 'FONTSIZE',
    'Color', 'typelib_path', 'LoadPictureConstants', 'FONTUNDERSCORE',
    'Font', 'VgaColor', 'OLE_COLOR', 'OLE_CANCELBOOL',
    'FONTSTRIKETHROUGH', 'OLE_YPOS_CONTAINER', 'IFontDisp',
    'OLE_HANDLE', 'OLE_YSIZE_HIMETRIC', 'OLE_XSIZE_PIXELS',
    'OLE_ENABLEDEFAULTBOOL', 'FontEvents', 'Gray',
    'OLE_XSIZE_CONTAINER', 'IFontEventsDisp', 'Library',
    'OLE_OPTEXCLUSIVE', 'OLE_YPOS_HIMETRIC', 'OLE_XPOS_CONTAINER',
    'OLE_TRISTATE', 'IPictureDisp', 'OLE_YPOS_PIXELS', 'FONTITALIC',
    'FONTBOLD', 'Checked', 'IPicture', 'StdPicture',
    'OLE_YSIZE_CONTAINER', 'OLE_YSIZE_PIXELS', 'OLE_XSIZE_HIMETRIC',
    'Monochrome', 'Unchecked', 'IFont', 'Default', 'OLE_XPOS_HIMETRIC'
]

