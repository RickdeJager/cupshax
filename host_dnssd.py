from zeroconf import ServiceInfo, Zeroconf
import socket
import os
import time

def create_ipp_printer_service():
    # IPP over TCP (standard IPP service)
    service_type = "_ipp._tcp.local."
    service_name = "Acme Laser Pro._ipp._tcp.local."
    
    ip_address = socket.inet_aton("10.0.0.3")  # Your printer IP (or use 127.0.0.1 for local)
    port = 631  # Standard IPP port
    
    # TXT records with IPP and localization attributes
    txt_records = {
        "txtvers": "1",                     # TXT record version
        "qtotal": "1",                      # Number of print queues
        "rp": "printers/acme_laser_pro",    # Resource path for IPP (CUPS uses /printers/...)
        "ty-en": "Acme Laser Pro",          # Localized printer type (English)
        "note-en": "Office printer, Floor 3, Room 301",  # Location (English)
        "pdl": "application/postscript,application/pdf",  # Supported PDLs (PostScript, PDF)
        "adminurl": "http://10.0.0.3:631",  # Printer admin URL
        "UUID": "545253fb-1337-4d8d-98ed-ab6cd608cea9",  # Unique identifier
        "printer-type": "0x800683",  # IPP printer type (e.g., 0x800683 for color, duplex, etc.)
    }

    service_info = ServiceInfo(
        service_type,
        service_name,
        addresses=[ip_address],
        port=port,
        properties=txt_records,
        server="Acme-Laser-Pro.local.",  # The hostname of the printer
    )
    
    return service_info


def main():
    # Start Zeroconf for DNS-SD advertisement
    zeroconf = Zeroconf()
    service_info = create_ipp_printer_service()
    
    try:
        print("Registering IPP printer service...")
        zeroconf.register_service(service_info)
        print("IPP Printer service registered. Press Ctrl+C to exit.")

        input("Press any key")
        
    except KeyboardInterrupt:
        print("Unregistering service...")
        zeroconf.unregister_service(service_info)
        zeroconf.close()


if __name__ == "__main__":
    main()

