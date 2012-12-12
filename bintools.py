class RawData:
    """Creates an object that can be read like a file.  Takes any sequence of data as an argument.  May typically be used to pass only a part of a file to a function so that the part of the file can still be read like a file.
    
    Methods:
        read(length = 0) -- Returns a slice of data from the current address to the current address plus length.  Increases current address by length.  If length is 0 or not provided, returns the entire data.
        seek(new_addr[, whence = 0]) -- Changes the current address.  If whence is 0, new_addr is bytes from beginning; if whence is 1, new_addr is bytes from current address; if whence is 2, new_addr is bytes from end."""
    def __init__(self, data):
        self.data = data
        self.addr = 0
        
    def __len__(self):
        return len(self.data)
        
    def read(self, length = 0):
        if length == 0:
            return self.data
        else:
            out = self.data[self.addr:self.addr + length]
            self.addr += length
            return out
            
    def seek(self, new_addr, whence = 0):
        if whence == 1:
            self.addr += new_addr
        elif whence == 2:
            self.addr = len(self.data) - new_addr
        else:
            self.addr = new_addr