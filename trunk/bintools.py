def readint(bytes):
    """Takes a string of length four as an argument.  Interprets a binary/escaped hex string as an integer."""
    if len(bytes) != 4:
        raise ValueError
    n = ord(bytes[3]) << 24
    n += ord(bytes[2]) << 16
    n += ord(bytes[1]) << 8
    n += ord(bytes[0])
    return n

def readfloat(bytes):
    """Takes a string of length four as an argument.  Interprets a binary/escaped hex string as a float."""
    if len(bytes) != 4:
        raise ValueError
    binstr = bin(getInt(bytes))[2:]
    sign = binstr[0]
    e = binstr[1:9]
    frac = binstr[9:]
    n = 1.0
    for i in range(len(frac)):
        n += int(frac[i]) * 2 ** -(i + 1)
    n *= -1 ** int(sign)
    n *= 2 ** (int(e, 2) - 127)
	  return n
     
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