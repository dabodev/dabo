import wx

class App(wx.App):
    def OnInit(self):
        return True

if __name__ == "__main__":
    import form, textBox, commandButton
    app = App()
    frame = form.Form()
    panel = wx.Panel(frame, -1)
    textBox = textBox.TextBox(panel)
    textBox.SetPosition((10,5))
    textBox.SetSize((200, 24))
    commandButton = commandButton.CommandButton(panel)
    commandButton.SetPosition((50,50))
    frame.Show(1)
    app.MainLoop()

