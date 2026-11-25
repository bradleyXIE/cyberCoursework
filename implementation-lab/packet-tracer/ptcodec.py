import ctypes, sys, zlib, struct
g = ctypes.CDLL('/opt/homebrew/opt/libgcrypt/lib/libgcrypt.dylib')
g.gcry_check_version.restype = ctypes.c_char_p
g.gcry_check_version(None)
TWOFISH, EAX = 10, 14
def eax(data, enc):
    h = ctypes.c_void_p()
    assert g.gcry_cipher_open(ctypes.byref(h), TWOFISH, EAX, 0) == 0
    key = bytes([0x89])*16; iv = bytes([0x10])*16
    assert g.gcry_cipher_setkey(h, key, 16) == 0
    assert g.gcry_cipher_setiv(h, iv, 16) == 0
    buf = ctypes.create_string_buffer(bytes(data), len(data))
    f = g.gcry_cipher_encrypt if enc else g.gcry_cipher_decrypt
    rc = f(h, buf, len(data), None, 0); assert rc == 0, rc
    tag = ctypes.create_string_buffer(16)
    if enc: g.gcry_cipher_gettag(h, tag, 16)
    g.gcry_cipher_close(h)
    return buf.raw, tag.raw
def decode(raw):
    L = len(raw)
    s1 = bytes(raw[L-1-i] ^ ((L - i*L) & 0xff) for i in range(L))
    ct = s1[:-16]  # last 16 = tag
    pt, _ = eax(ct, False)
    n = len(pt)
    s3 = bytes(pt[i] ^ ((n - i) & 0xff) for i in range(n))
    size = struct.unpack('>I', s3[:4])[0]
    out = zlib.decompress(s3[4:]); assert len(out) == size
    return out
def encode(xml):
    comp = struct.pack('>I', len(xml)) + zlib.compress(xml)
    n = len(comp)
    s3 = bytes(comp[i] ^ ((n - i) & 0xff) for i in range(n))
    ct, tag = eax(s3, True)
    s1 = ct + tag; L = len(s1)
    out = bytearray(L)
    for i in range(L):
        out[L-1-i] = s1[i] ^ ((L - i*L) & 0xff)
    return bytes(out)
if __name__ == '__main__':
    mode, src, dst = sys.argv[1:4]
    data = open(src,'rb').read()
    open(dst,'wb').write(decode(data) if mode=='d' else encode(data))
