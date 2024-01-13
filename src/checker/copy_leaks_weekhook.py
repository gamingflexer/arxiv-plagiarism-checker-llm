from flask import Flask, request, jsonify
from copyleaks.models.export import Export, ExportCrawledVersion, ExportResult
from copyleaks.copyleaks import Copyleaks
from copyleaks.exceptions.command_error import CommandError
from copyleaks.models.submit.document import FileDocument
from copyleaks.models.submit.properties.scan_properties import ScanProperties
from copyleaks.models.submit.properties.pdf import Pdf
from copy_leaks_login import CopyleaksClient
from config import COPY_LEAKS_EMAIL_ADDRESS, COPY_LEAKS_KEY, WEBHOOK_SECRET

app = Flask(__name__)

# Copyleaks configuration
copyleaks_client = Copyleaks()
copyleaks_client.login(COPY_LEAKS_EMAIL_ADDRESS, COPY_LEAKS_KEY)

@app.route('/webhook/completion?event=<status>', methods=['GET'])
def handle_completion_webhook(status):
    data = request.json
    print(f'Completion webhook received. Status: {status}')
    
    if status == 'completed':
        scan_id = data.get('scanId')
        export_results(scan_id)
        generate_pdf_report(scan_id)

    return 'Webhook received'

def export_results(scan_id):
    try:
        export = Export()
        export.set_completion_webhook(f'{request.url_root}webhook/export/completion')
        
        # Set up export options (crawled version and results)
        crawled = ExportCrawledVersion()
        crawled.set_endpoint(f'{request.url_root}webhook/export/crawled')
        crawled.set_verb('POST')
        crawled.set_headers([['key', 'value'], ['key2', 'value2']])
        export.set_crawled_version(crawled)

        results = ExportResult()
        results.set_id(scan_id)
        results.set_endpoint(f'{request.url_root}webhook/export/result/{scan_id}')
        results.set_verb('POST')
        results.set_headers([['key', 'value'], ['key2', 'value2']])
        export.set_results([results])

        Copyleaks.export(copyleaks_client.auth_token, scan_id, f'export-{scan_id}', export)
    except CommandError as ce:
        response = ce.get_response()
        print(f"Export error (HTTP status code {response.status_code}):")
        print(response.content)

def generate_pdf_report(scan_id):
    try:
        pdf = Pdf()
        pdf.set_create(True)
        Copyleaks.generate_pdf_report(copyleaks_client.auth_token, scan_id, pdf)
    except CommandError as ce:
        response = ce.get_response()
        print(f"PDF generation error (HTTP status code {response.status_code}):")
        print(response.content)

if __name__ == '__main__':
    app.run(port=8001, host='0.0.0.0')