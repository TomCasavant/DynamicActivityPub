from urllib.parse import urlparse

class Recipient:
    def __init__(self, server, username):
        self.server = server
        self.username = username
        self.base_url = f"https://{server}"
        #self.recipient_url = f"{base_url}/users/{username}"
        #self.recipient_inbox = f"{recipient_url}/inbox"
        #recipient_parsed = urlparse(recipient_inbox)
        #recipient_host = recipient_parsed.netloc
        #recipient_path = recipient_parsed.path

    @property
    def url(self):
        return f"{self.base_url}/users/{self.username}"

    @property
    def inbox(self):
        return f"{self.url}/inbox"
        
    @property
    def parsed(self):
        return urlparse(self.inbox)

    @property
    def host(self):
        return self.parsed.netloc

    @property
    def path(self):
        return self.parsed.path
