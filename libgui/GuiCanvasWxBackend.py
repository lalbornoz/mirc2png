#!/usr/bin/env python3
#
# GuiCanvasWxBackend.py
# Copyright (c) 2018, 2019 Lucio Andrés Illanes Albornoz <lucio@lucioillanes.de>
#

from ctypes import *
from GuiCanvasColours import Colours
import math, os, platform, wx

class GuiBufferedDC(wx.MemoryDC):
    # {{{ __del__(self)
    def __del__(self):
        self.dc.Blit(0, 0, *self.viewSize, self, 0, 0)
        self.SelectObject(wx.NullBitmap)
    # }}}
    # {{{ __init__(self, backend, buffer, clientSize, dc, viewRect)
    def __init__(self, backend, buffer, clientSize, dc, viewRect):
        super().__init__()
        canvasSize = [a - b for a, b in zip(backend.canvasSize, viewRect)]
        clientSize = [math.ceil(m / n) for m, n in zip(clientSize, backend.cellSize)]
        viewRect = [m * n for m, n in zip(backend.cellSize, viewRect)]
        viewSize = [min(m, n) for m, n in zip(canvasSize, clientSize)]
        viewSize = [m * n for m, n in zip(backend.cellSize, viewSize)]
        self.SelectObject(buffer); self.SetDeviceOrigin(*viewRect);
        self.dc, self.viewRect, self.viewSize = dc, viewRect, viewSize
    # }}}

class GuiCanvasWxBackend():
    # {{{ _CellState(): Cell state
    class _CellState():
        CS_NONE             = 0x00
        CS_BOLD             = 0x01
        CS_ITALIC           = 0x02
        CS_UNDERLINE        = 0x04
    # }}}

    # {{{ _drawBrushPatch(self, eventDc, patch, point)
    def _drawBrushPatch(self, eventDc, patch, point):
        absPoint = self._xlatePoint(point)
        brushBg, brushFg, pen = self._getBrushPatchColours(patch)
        self._setBrushDc(brushBg, brushFg, eventDc, pen)
        eventDc.DrawRectangle(*absPoint, *self.cellSize)
    # }}}
    # {{{ _drawCharPatch(self, eventDc, patch, point)
    def _drawCharPatch(self, eventDc, patch, point):
        absPoint, fontBitmap = self._xlatePoint(point), wx.Bitmap(*self.cellSize)
        brushBg, brushFg, pen = self._getCharPatchColours(patch)
        fontDc = wx.MemoryDC(); fontDc.SelectObject(fontBitmap); fontDc.SetFont(self._font);
        fontDc.SetBackground(brushBg); fontDc.SetBrush(brushFg); fontDc.SetPen(pen);
        fontDc.SetTextForeground(wx.Colour(Colours[patch[0]][:4]))
        fontDc.SetTextBackground(wx.Colour(Colours[patch[1]][:4]))
        fontDc.DrawRectangle(0, 0, *self.cellSize)
        fontDc.SetPen(self._pens[patch[0]])
        if (patch[2] & self._CellState.CS_UNDERLINE)    \
        or (patch[3] == "_"):
            fontDc.DrawLine(0, self.cellSize[1] - 1, self.cellSize[0], self.cellSize[1] - 1)
        if patch[3] != "_":
            fontDc.DrawText(patch[3], 0, 0)
        eventDc.Blit(*absPoint, *self.cellSize, fontDc, 0, 0)
    # }}}
    # {{{ _finiBrushesAndPens(self)
    def _finiBrushesAndPens(self):
        [brush.Destroy() for brush in self._brushes or []]
        [pen.Destroy() for pen in self._pens or []]
        self._brushes, self._lastBrushBg, self._lastBrushFg, self._lastPen, self._pens = None, None, None, None, None
    # }}}
    # {{{ _getBrushPatchColours(self, patch)
    def _getBrushPatchColours(self, patch):
        if (patch[0] != -1) and (patch[1] != -1):
            brushBg, brushFg, pen = self._brushes[patch[1]], self._brushes[patch[1]], self._pens[patch[1]]
        elif (patch[0] == -1) and (patch[1] == -1):
            brushBg, brushFg, pen = self._brushAlpha, self._brushAlpha, self._penAlpha
        elif patch[0] == -1:
            brushBg, brushFg, pen = self._brushes[patch[1]], self._brushes[patch[1]], self._pens[patch[1]]
        elif patch[1] == -1:
            brushBg, brushFg, pen = self._brushAlpha, self._brushAlpha, self._penAlpha
        return (brushBg, brushFg, pen)
    # }}}
    # {{{ _getCharPatchColours(self, patch)
    def _getCharPatchColours(self, patch):
        if (patch[0] != -1) and (patch[1] != -1):
            brushBg, brushFg, pen = self._brushes[patch[1]], self._brushes[patch[1]], self._pens[patch[1]]
        elif (patch[0] == -1) and (patch[1] == -1):
            brushBg, brushFg, pen = self._brushAlpha, self._brushAlpha, self._penAlpha
        elif patch[0] == -1:
            brushBg, brushFg, pen = self._brushes[patch[1]], self._brushes[patch[1]], self._pens[patch[1]]
        elif patch[1] == -1:
            brushBg, brushFg, pen = self._brushAlpha, self._brushAlpha, self._penAlpha
        return (brushBg, brushFg, pen)
    # }}}
    # {{{ _initBrushesAndPens(self)
    def _initBrushesAndPens(self):
        self._brushes, self._pens = [None for x in range(len(Colours))], [None for x in range(len(Colours))]
        for mircColour in range(len(Colours)):
            self._brushes[mircColour] = wx.Brush(wx.Colour(Colours[mircColour][:4]), wx.BRUSHSTYLE_SOLID)
            self._pens[mircColour] = wx.Pen(wx.Colour(Colours[mircColour][:4]), 1)
        self._brushAlpha = wx.Brush(wx.Colour(Colours[14][:4]), wx.BRUSHSTYLE_SOLID)
        self._penAlpha = wx.Pen(wx.Colour(Colours[14][:4]), 1)
        self._lastBrushBg, self._lastBrushFg, self._lastPen = None, None, None
    # }}}
    # {{{ _setBrushDc(self, brushBg, brushFg, dc, pen)
    def _setBrushDc(self, brushBg, brushFg, dc, pen):
        if self._lastBrushBg != brushBg:
            dc.SetBackground(brushBg); self._lastBrushBg = brushBg;
        if self._lastBrushFg != brushFg:
            dc.SetBrush(brushFg); self._lastBrushFg = brushFg;
        if self._lastPen != pen:
            dc.SetPen(pen); self._lastPen = pen;
    # }}}
    # {{{ _xlatePoint(self, point)
    def _xlatePoint(self, point):
        return [a * b for a, b in zip(point, self.cellSize)]
    # }}}

    # {{{ drawCursorMaskWithJournal(self, canvasJournal, eventDc, viewRect)
    def drawCursorMaskWithJournal(self, canvasJournal, eventDc, viewRect):
        [self.drawPatch(eventDc, patch, viewRect) for patch in canvasJournal.popCursor()]
    # }}}
    # {{{ drawPatch(self, eventDc, patch, viewRect)
    def drawPatch(self, eventDc, patch, viewRect):
        point = [m - n for m, n in zip(patch[:2], viewRect)]
        if [(c >= 0) and (c < s) for c, s in zip(point, self.canvasSize)] == [True, True]:
            if patch[5] == " ":
                if patch[3] == -1:
                    self._drawCharPatch(eventDc, [*patch[2:-1], "░"], point)
                elif patch[4] & self._CellState.CS_UNDERLINE:
                    self._drawCharPatch(eventDc, patch[2:], point)
                else:
                    self._drawBrushPatch(eventDc, patch[2:], point)
            else:
                self._drawCharPatch(eventDc, patch[2:], point)
            return True
        else:
            return False
    # }}}
    # {{{ getDeviceContext(self, clientSize, parentWindow, viewRect)
    def getDeviceContext(self, clientSize, parentWindow, viewRect):
        if viewRect == (0, 0):
            eventDc = wx.BufferedDC(wx.ClientDC(parentWindow), self.canvasBitmap)
        else:
            eventDc = GuiBufferedDC(self, self.canvasBitmap, clientSize, wx.ClientDC(parentWindow), viewRect)
        self._lastBrushBg, self._lastBrushFg, self._lastPen = None, None, None
        return eventDc
    # }}}
    # {{{ onPaint(self, clientSize, panelWindow, viewRect)
    def onPaint(self, clientSize, panelWindow, viewRect):
        if self.canvasBitmap != None:
            if viewRect == (0, 0):
                eventDc = wx.BufferedPaintDC(panelWindow, self.canvasBitmap)
            else:
                eventDc = GuiBufferedDC(self, self.canvasBitmap, clientSize, wx.PaintDC(panelWindow), viewRect)
    # }}}
    # {{{ resize(self, canvasSize, cellSize):
    def resize(self, canvasSize, cellSize):
        winSize = [a * b for a, b in zip(canvasSize, cellSize)]
        if self.canvasBitmap == None:
            self.canvasBitmap = wx.Bitmap(winSize)
        else:
            oldDc = wx.MemoryDC(); oldDc.SelectObject(self.canvasBitmap);
            newDc = wx.MemoryDC(); newBitmap = wx.Bitmap(winSize); newDc.SelectObject(newBitmap);
            newDc.Blit(0, 0, *self.canvasBitmap.GetSize(), oldDc, 0, 0)
            oldDc.SelectObject(wx.NullBitmap)
            self.canvasBitmap.Destroy(); self.canvasBitmap = newBitmap;
        self.canvasSize, self.cellSize = canvasSize, cellSize
        if platform.system() == "Windows":
            self._font = wx.TheFontList.FindOrCreateFont(cellSize[0] + 1, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, self.fontName)
        else:
            self._font = wx.Font(cellSize[0] + 1, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    # }}}
    # {{{ xlateEventPoint(self, event, eventDc, viewRect)
    def xlateEventPoint(self, event, eventDc, viewRect):
        eventPoint = event.GetLogicalPosition(eventDc)
        rectX, rectY = eventPoint.x - (eventPoint.x % self.cellSize[0]), eventPoint.y - (eventPoint.y % self.cellSize[1])
        mapX, mapY = int(rectX / self.cellSize[0] if rectX else 0), int(rectY / self.cellSize[1] if rectY else 0)
        return [m + n for m, n in zip((mapX, mapY), viewRect)]
    # }}}

    # {{{ __del__(self): destructor method
    def __del__(self):
        if self.canvasBitmap != None:
            self.canvasBitmap.Destroy(); self.canvasBitmap = None;
        self._finiBrushesAndPens()
    # }}}

    #
    # __init__(self, canvasSize, cellSize, fontName="Dejavu Sans Mono", fontPathName=os.path.join("assets", "fonts", "DejaVuSansMono.ttf")): initialisation method
    def __init__(self, canvasSize, cellSize, fontName="Dejavu Sans Mono", fontPathName=os.path.join("assets", "fonts", "DejaVuSansMono.ttf")):
        self._brushes, self._font, self._lastBrush, self._lastPen, self._pens = None, None, None, None, None
        self.canvasBitmap, self.cellSize, self.fontName, self.fontPathName = None, None, fontName, fontPathName
        if platform.system() == "Windows":
            WinDLL("gdi32.dll").AddFontResourceW(self.fontPathName.encode("utf16"))
        self._initBrushesAndPens(); self.resize(canvasSize, cellSize);

# vim:expandtab foldmethod=marker sw=4 ts=4 tw=120
