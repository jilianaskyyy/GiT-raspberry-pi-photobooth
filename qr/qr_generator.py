import qrcode

GALLERY_URL = "https://spectacular-raindrop-7f6521.netlify.app" 

def make_qr(session_id, save_as="qr.png"):
    link = f"{GALLERY_URL}?session={session_id}"
    qrcode.make(link).save(save_as)
    return save_as