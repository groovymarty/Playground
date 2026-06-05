from pathlib import Path
import dropbox

def get_dropbox():
    token = (Path.home() / ".dropbox-access-token").read_text().strip()
    return dropbox.Dropbox(token)