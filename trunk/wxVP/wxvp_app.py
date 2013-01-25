#!/usr/bin/env python
#Boa:App:BoaApp

import wx

import wxvp_frame

modules ={u'wxvp_frame': [1, 'Main frame of Application', u'wxvp_frame.py']}

class BoaApp(wx.App):
    def OnInit(self):
        self.main = wxvp_frame.create(None)
        self.main.Show()
        self.SetTopWindow(self.main)
        return True

def main():
    application = BoaApp(0)
    application.MainLoop()

if __name__ == '__main__':
    main()
