# Used to guarantee to use at least Wx2.8
import wxversion

wxversion.ensureMinimal('2.8')

import wx
import wx.aui
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as Toolbar
from matplotlib.figure import Figure
from srim import process
import os, sys


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

        self.list = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT, size=(140, -1))
        self.list.InsertColumn(0, 'Layers', width=140)
        self.data = panel.data

        for i in range(len(self.data)):
            l = self.data[i]
            index = self.list.InsertStringItem(sys.maxint, 'Layer-%d (%s)' % (l['layer'], l['atom']))
            self.list.SetItemData(index, i)

        self.panel.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick, self.list)

        self.fig = Figure()
        self.canvas = Canvas(self.panel, -1, self.fig)
        self.toolbar = Toolbar(self.canvas) #matplotlib toolbar
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        # This way of adding to sizer allows resizing
        sizer.Add(self.canvas, 1, wx.LEFT|wx.TOP|wx.GROW)
        # Best to allow the toolbar to resize!
        sizer.Add(self.toolbar, 0, wx.GROW)

        hbox.Add(self.list, 0, wx.EXPAND)
        hbox.Add(sizer, 1, wx.EXPAND)

        self.panel.SetSizer(hbox)
        hbox.Layout()
        self.panel.Layout()
        self.panel.GetParent().Layout()

    def OnClick(self, event):
        i = event.GetData()
        l = self.data[i]
        self.fig.clf()
        a = self.fig.add_subplot(111)
        n, bins, patches = a.hist(l['energy'], 50, normed=1, alpha=0.75)
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
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename = dlg.GetFilename()
            self.dirname = dlg.GetDirectory()
            fname = os.path.join(self.dirname, self.filename)
            self.SetStatusText('Processing: %s' % fname)
            self.data = process(fname)
            self.SetStatusText('Done. %d records read' % len(self.data))
            self.layersPanel = LayerList(self)
        dlg.Destroy()

def main():
    app = wx.PySimpleApp()
    frame = MainFrame(None, 'SRIM postprocessing')
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()
