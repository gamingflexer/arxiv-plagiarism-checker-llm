import base64
import random
from copyleaks.copyleaks import Copyleaks
from copyleaks.exceptions.command_error import CommandError
from copyleaks.models.submit.document import FileDocument
from copyleaks.models.submit.properties.scan_properties import ScanProperties

class CopyleaksClient:
    def __init__(self, email_address, key):
        self.email_address = email_address
        self.key = key
        self.auth_token = None

    def login(self):
        try:
            self.auth_token = Copyleaks.login(self.email_address, self.key)
        except CommandError as ce:
            response = ce.get_response()
            print(f"An error occurred (HTTP status code {response.status_code}):")
            print(response.content)
            exit(1)

        print("Logged successfully!\nToken:")
        print(self.auth_token)

    def submit_file(self, file_content, filename, webhook_url):
        scan_id = random.randint(100, 100000)
        BASE64_FILE_CONTENT = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
        file_submission = FileDocument(BASE64_FILE_CONTENT, filename)

        scan_properties = ScanProperties(webhook_url)
        scan_properties.set_sandbox(True)
        file_submission.set_properties(scan_properties)

        Copyleaks.submit_file(self.auth_token, scan_id, file_submission)
        print("Sent to scanning")
        print("You will be notified using your webhook once the scan is completed.")