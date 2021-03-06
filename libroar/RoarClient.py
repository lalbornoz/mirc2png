#!/usr/bin/env python3
#
# RoarClient.py
# Copyright (c) 2018, 2019 Lucio Andrés Illanes Albornoz <lucio@lucioillanes.de>
#

from Canvas import Canvas
from GuiCanvasWxBackend import GuiCanvasWxBackend
from GuiFrame import GuiFrame, NID_TOOLBAR_HSEP
from RoarAssetsWindow import RoarAssetsWindow
from RoarCanvasCommands import RoarCanvasCommands
from RoarCanvasWindow import RoarCanvasWindow

from glob import glob
import os, random, sys, wx

class RoarClient(GuiFrame):
    def _getIconPathName(self):
        iconPathNames = glob(os.path.join("assets", "images", "logo*.bmp"))
        return iconPathNames[random.randint(0, len(iconPathNames) - 1)]

    def _initToolBitmaps(self, toolBars):
        basePathName = os.path.join(os.path.dirname(sys.argv[0]), "assets", "images")
        for toolBar in toolBars:
            for toolBarItem in [i for i in toolBar if i != NID_TOOLBAR_HSEP]:
                toolBarItem.attrDict["icon"] = self.loadBitmap(basePathName, toolBarItem.attrDict["icon"])

    def onChar(self, event):
        self.canvasPanel.onKeyboardInput(event)

    def onClose(self, event):
        if not self.canvasPanel.commands.exiting:
            closeFlag = self.canvasPanel.commands._promptSaveChanges()
        else:
            closeFlag = True
        if closeFlag:
            event.Skip();

    def onMouseWheel(self, event):
        self.canvasPanel.GetEventHandler().ProcessEvent(event)

    def onSize(self, event):
        pass

    def __init__(self, parent, defaultCanvasPos=(0, 75), defaultCanvasSize=(100, 30), size=(840, 640), title=""):
        super().__init__(self._getIconPathName(), size, parent, title)
        self.canvas = Canvas(defaultCanvasSize)
        self.canvasPanel = RoarCanvasWindow(GuiCanvasWxBackend, self.canvas, RoarCanvasCommands, self, defaultCanvasPos, defaultCanvasSize)
        self.loadAccels(self.canvasPanel.commands.accels, self.canvasPanel.commands.menus, self.canvasPanel.commands.toolBars)
        self.loadMenus(self.canvasPanel.commands.menus)
        self._initToolBitmaps(self.canvasPanel.commands.toolBars)
        self.loadToolBars(self.canvasPanel.commands.toolBars)

        self.canvasPanel.commands.update(brushSize=self.canvasPanel.brushSize, colours=self.canvasPanel.brushColours)
        self.addWindow(self.canvasPanel)
        self.assetsWindow = RoarAssetsWindow(GuiCanvasWxBackend, self)
        self.canvasPanel.commands.canvasAssetsWindowShow(None)

        self.canvasPanel.operatorsMenu = wx.Menu()
        for menuItem in self.canvasPanel.commands.menus[3][1:]:
            menuItemWindow = self.canvasPanel.operatorsMenu.Append(menuItem.attrDict["id"], menuItem.attrDict["label"], menuItem.attrDict["caption"])
            self.Bind(wx.EVT_MENU, self.onMenu, menuItemWindow)

        self.canvasPanel.commands.canvasClearRecent.attrDict["id"] = wx.NewId()
        self.canvasPanel.commands.canvasOpenRecent.attrDict["menu"].AppendSeparator()
        self.canvasPanel.commands.canvasRestore.attrDict["menu"].AppendSeparator()
        self.canvasPanel.commands.canvasRestoreFile.attrDict["id"] = wx.NewId()
        menuItemWindow = self.canvasPanel.commands.canvasOpenRecent.attrDict["menu"].Append(self.canvasPanel.commands.canvasClearRecent.attrDict["id"], self.canvasPanel.commands.canvasClearRecent.attrDict["label"], self.canvasPanel.commands.canvasClearRecent.attrDict["caption"])
        menuItemWindow = self.canvasPanel.commands.canvasRestore.attrDict["menu"].Append(self.canvasPanel.commands.canvasRestoreFile.attrDict["id"], self.canvasPanel.commands.canvasRestoreFile.attrDict["label"], self.canvasPanel.commands.canvasRestoreFile.attrDict["caption"])
        self.canvasPanel.commands.canvasOpenRecent.attrDict["menu"].Bind(wx.EVT_MENU, self.canvasPanel.commands.canvasClearRecent, menuItemWindow)
        self.canvasPanel.commands.canvasRestore.attrDict["menu"].Bind(wx.EVT_MENU, self.canvasPanel.commands.canvasRestoreFile, menuItemWindow)
        self.Bind(wx.EVT_CLOSE, self.onClose); self.Bind(wx.EVT_SIZE, self.onSize);
        self.toolBarPanes[0].BestSize(0, 0).Right(); self.toolBarPanes[1].BestSize(0, 0).Right(); self.auiManager.Update();

# vim:expandtab foldmethod=marker sw=4 ts=4 tw=120
