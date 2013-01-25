#Boa:Dialog:AboutVP

import wx

def create(parent):
    return AboutVP(parent)

[wxID_ABOUTVP, wxID_ABOUTVPABOUTTITLE, 
] = [wx.NewId() for _init_ctrls in range(2)]

class AboutVP(wx.Dialog):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wxID_ABOUTVP, name='AboutVP', parent=prnt,
              pos=wx.Point(608, 316), size=wx.Size(400, 250),
              style=wx.DEFAULT_DIALOG_STYLE, title='About wxVP')
        self.SetClientSize(wx.Size(384, 212))
        self.SetToolTipString('')
        self.SetWindowVariant(wx.WINDOW_VARIANT_NORMAL)

        self.AboutTitle = wx.StaticText(id=wxID_ABOUTVPABOUTTITLE,
              label='wxVP version 1.0', name='AboutTitle', parent=self,
              pos=wx.Point(110, 38), size=wx.Size(163, 24), style=0)
        self.AboutTitle.Center(wx.HORIZONTAL)
        self.AboutTitle.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL,
              False, 'Arial'))
        self.AboutTitle.SetToolTipString('')

    def __init__(self, parent):
        self._init_ctrls(parent)
