from urllib.parse import urlparse

class Recipient:
    def __init__(self, server, username, ssl=True, type="User"):
        self.server = server
        self.username = username
        self.type = type
        if ssl:
            self.base_url = f"https://{server}"
        else:
            self.base_url = f"http://{server}"
        #self.recipient_url = f"{base_url}/users/{username}"
        #self.recipient_inbox = f"{recipient_url}/inbox"
        #recipient_parsed = urlparse(recipient_inbox)
        #recipient_host = recipient_parsed.netloc
        #recipient_path = recipient_parsed.path

    @property
    def url(self):
        u = f"{self.base_url}/users/{self.username}"
        if (self.type == "Group"):
            u = f"{self.base_url}"
        return u

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
