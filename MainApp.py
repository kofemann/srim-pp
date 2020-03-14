#!/usr/bin/env python

import wx
import wx.aui
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as Toolbar
from matplotlib.figure import Figure
from srim import process
import os
import sys
import io


class PlotPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        self.fig = Figure()
        self.canvas = Canvas(self, -1, self.fig)
        self.toolbar = Toolbar(self.canvas) #matplotlib toolbar
        self.toolbar.Realize()
        #self.toolbar.set_active([0,1])

        # Now put all into a sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        # This way of adding to sizer allows resizing
        sizer.Add(self.canvas, 1, wx.LEFT|wx.TOP|wx.GROW)
        # Best to allow the toolbar to resize!
        sizer.Add(self.toolbar, 0, wx.GROW)
        self.SetSizer(sizer)
        self.Fit()

class LayerList:
    def __init__(self, panel):

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.panel = panel.viewPanel
        self.parent = panel

        self.list = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT, size=(140, -1))
        self.list.InsertColumn(0, 'Layers', width=140)
        self.data = panel.data

        for i in range(len(self.data)):
            l = self.data[i]
            index = self.list.InsertItem(sys.maxsize, 'Layer-%d (%s)' % (l['layer'], l['atom']))
            self.list.SetItemData(index, i)

        self.panel.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnClick, self.list)

        self.text = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.fig = Figure()
        self.canvas = Canvas(self.panel, -1, self.fig)
        self.toolbar = Toolbar(self.canvas)
        self.toolbar.Realize()

        # Note that event is a MplEvent
        self.canvas.mpl_connect('motion_notify_event', self.UpdateStatusBar)
        self.canvas.Bind(wx.EVT_ENTER_WINDOW, self.ChangeCursor)

        sizer = wx.BoxSizer(wx.VERTICAL)
        # This way of adding to sizer allows resizing
        sizer.Add(self.canvas, 0, wx.LEFT|wx.TOP|wx.GROW)
        # Best to allow the toolbar to resize!
        sizer.Add(self.toolbar, 0, wx.GROW)
        sizer.Add(self.text, 1, wx.EXPAND)

        hbox.Add(self.list, 0, wx.EXPAND)
        hbox.Add(sizer, 1, wx.EXPAND)

        self.panel.SetSizer(hbox)
        hbox.Layout()
        self.panel.Layout()
        self.panel.GetParent().Layout()

    def ChangeCursor(self, event):
        self.canvas.SetCursor(wx.Cursor(wx.CURSOR_BULLSEYE))
        event.Skip()

    def UpdateStatusBar(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            self.parent.SetStatusText(("energy = %.3f, event count = %.3f" % (x, y)), 0)

    def OnClick(self, event):
        i = event.GetData()
        l = self.data[i]
        self.fig.clf()
        a = self.fig.add_subplot(111)
        n, bins, patches = a.hist(l['energy'], 50, density=0, alpha=0.75)
        a.set_xlabel('Energy, Mev')
        a.set_ylabel('Events')
        a.set_title('Layer : ' + str(l['layer']) + '[' + l['atom'] + ']')
        a.grid(True)

        textstr = 'Events=%d\navg=%.2f\nsigma=%.2f' % (len(l['energy']), l['avg'], l['sigma'])
        props = dict(boxstyle='round4', facecolor='wheat', alpha=0.5)
        x, xx, y = a.get_xlim()[0], a.get_xlim()[1] - a.get_xlim()[0], a.get_ylim()[1]
        a.text(x + xx/100, y - y/100, textstr,
               fontsize=14, verticalalignment='top', bbox=props)

        output = io.StringIO()
        p = zip(n, bins)
        for i in p:
            output.write("%.4f\t\t%d\n" % (i[1], int(i[0])))
        self.text.SetValue(output.getvalue())
        self.canvas.draw()


class MainFrame(wx.Frame):
    def __init__(self, parent, title, size=(1024, 840)):
        wx.Frame.__init__(self, parent, title=title, size=size)
      #  self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.CreateStatusBar() # A Status bar in the bottom of the window

        # Setting up the menu.
        filemenu = wx.Menu()

        # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open", " Open SRIM result")
        filemenu.AppendSeparator()
        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About", " Information about this program")
        filemenu.AppendSeparator()
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        self.viewPanel = wx.Panel(self, -1)
        self.SetStatusText('Ready...')

    def OnAbout(self, e):
        # A message dialog box with an OK button. wx.OK is a standard ID in wxWidgets.
        dlg = wx.MessageDialog(self,
                               "A simple program to analyze results produced by SRIM calculations",
                               "SRIM postprocessing", wx.OK)
        dlg.ShowModal() # Show it
        dlg.Destroy() # finally destroy it when finished.

    def OnExit(self, e):
        self.Close(True)  # Close the frame.

    def OnOpen(self, e):
        """ Open a file"""
        self.dirname = ''
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.path = dlg.GetPath()
            self.SetStatusText('Processing: %s' % self.path)
            wx.BeginBusyCursor()
            wx.SafeYield()
            self.data = process(self.path)
            wx.EndBusyCursor()
            self.SetStatusText('Done. %d records read' % len(self.data))
            self.layersPanel = LayerList(self)
        dlg.Destroy()

def main():
    app = wx.App()
    frame = MainFrame(None, 'SRIM postprocessing')
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()
