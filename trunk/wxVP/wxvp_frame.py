#Boa:Frame:wxVP

import wx
import wxvp_about_dialog

def create(parent):
    return wxVP(parent)

[wxID_WXVP, wxID_WXVPSTATUSBAR1, 
] = [wx.NewId() for _init_ctrls in range(2)]

[wxID_WXVPMENU1WXID_OPEN, wxID_WXVPMENU1WXID_SAVE, 
] = [wx.NewId() for _init_coll_menu1_Items in range(2)]

[wxID_WXVPFILEMENUID_EXIT, wxID_WXVPFILEMENUID_OPEN, 
 wxID_WXVPFILEMENUID_SAVEAS, 
] = [wx.NewId() for _init_coll_FileMenu_Items in range(3)]

[wxID_WXVPEDITMENUEDIT_ADD_FILE, wxID_WXVPEDITMENUITEM_ADD_DIR, 
 wxID_WXVPEDITMENUITEM_EXTRACT_DIR, wxID_WXVPEDITMENUITEM_EXTRACT_FILE, 
 wxID_WXVPEDITMENUITEM_REMOVE_DIR, wxID_WXVPEDITMENUITEM_REMOVE_FILE, 
] = [wx.NewId() for _init_coll_EditMenu_Items in range(6)]

[wxID_WXVPHELPMENUID_ABOUT] = [wx.NewId() for _init_coll_HelpMenu_Items in range(1)]

class wxVP(wx.Frame):
    def _init_coll_EditMenu_Items(self, parent):
        # generated method, don't edit

        parent.Append(help='', id=wxID_WXVPEDITMENUEDIT_ADD_FILE,
              kind=wx.ITEM_NORMAL, text='Add file(s)...')
        parent.Append(help='', id=wxID_WXVPEDITMENUITEM_ADD_DIR,
              kind=wx.ITEM_NORMAL, text='Add directory...')
        parent.AppendSeparator()
        parent.Append(help='', id=wxID_WXVPEDITMENUITEM_REMOVE_FILE,
              kind=wx.ITEM_NORMAL, text='Remove file(s)')
        parent.Append(help='', id=wxID_WXVPEDITMENUITEM_REMOVE_DIR,
              kind=wx.ITEM_NORMAL, text='Remove directory')
        parent.AppendSeparator()
        parent.Append(help='', id=wxID_WXVPEDITMENUITEM_EXTRACT_FILE,
              kind=wx.ITEM_NORMAL, text='Extract file(s)...')
        parent.Append(help='', id=wxID_WXVPEDITMENUITEM_EXTRACT_DIR,
              kind=wx.ITEM_NORMAL, text='Extract directory...')

    def _init_coll_menuBar1_Menus(self, parent):
        # generated method, don't edit

        parent.Append(menu=self.FileMenu, title='File')
        parent.Append(menu=self.EditMenu, title='Edit')
        parent.Append(menu=self.HelpMenu, title='Help')

    def _init_coll_HelpMenu_Items(self, parent):
        # generated method, don't edit

        parent.Append(help='', id=wxID_WXVPHELPMENUID_ABOUT,
              kind=wx.ITEM_NORMAL, text='About wxVP')
        self.Bind(wx.EVT_MENU, self.OnHelpAbout, id=wxID_WXVPHELPMENUID_ABOUT)

    def _init_coll_FileMenu_Items(self, parent):
        # generated method, don't edit

        parent.Append(help='', id=wxID_WXVPFILEMENUID_OPEN, kind=wx.ITEM_NORMAL,
              text='Load VP...')
        parent.Append(help='', id=wxID_WXVPFILEMENUID_SAVEAS,
              kind=wx.ITEM_NORMAL, text='Save VP...')
        parent.AppendSeparator()
        parent.Append(help='', id=wxID_WXVPFILEMENUID_EXIT, kind=wx.ITEM_NORMAL,
              text='Exit')
        self.Bind(wx.EVT_MENU, self.OnFileOpen, id=wxID_WXVPFILEMENUID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnFileSave, id=wxID_WXVPFILEMENUID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnFileExit, id=wxID_WXVPFILEMENUID_EXIT)

    def _init_utils(self):
        # generated method, don't edit
        self.menuBar1 = wx.MenuBar()

        self.FileMenu = wx.Menu(title='')

        self.EditMenu = wx.Menu(title='')

        self.HelpMenu = wx.Menu(title='')

        self._init_coll_menuBar1_Menus(self.menuBar1)
        self._init_coll_FileMenu_Items(self.FileMenu)
        self._init_coll_EditMenu_Items(self.EditMenu)
        self._init_coll_HelpMenu_Items(self.HelpMenu)

    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Frame.__init__(self, id=wxID_WXVP, name='wxVP', parent=prnt,
              pos=wx.Point(513, 253), size=wx.Size(924, 611),
              style=wx.DEFAULT_FRAME_STYLE, title='wxVP')
        self._init_utils()
        self.SetClientSize(wx.Size(908, 573))
        self.SetToolTipString('"wxVP"')
        self.SetMenuBar(self.menuBar1)

        self.statusBar1 = wx.StatusBar(id=wxID_WXVPSTATUSBAR1,
              name='statusBar1', parent=self, style=0)
        self.statusBar1.SetAutoLayout(True)
        self.statusBar1.SetToolTipString('wxVP')
        self.statusBar1.SetStatusText('')
        self.statusBar1.Center(wx.HORIZONTAL)
        self.SetStatusBar(self.statusBar1)

    def __init__(self, parent):
        self._init_ctrls(parent)

    def OnFileSave(self, event):
        event.Skip()

    def OnFileOpen(self, event):
        event.Skip()

    def OnHelpAbout(self, event):
        dlg = wxvp_about_dialog.AboutVP(self)
        try:
            dlg.ShowModal()
        finally:
            dlg.Destroy()

    def OnFileExit(self, event):
        self.Close()
