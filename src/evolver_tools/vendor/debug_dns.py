#!/usr/bin/env python3
"""Debug DNS response for www.github.com CNAME."""
import socket, struct

def _encode_domain(domain):
    labels = []
    for part in domain.rstrip('.').split('.'):
        labels.append(bytes([len(part)]) + part.encode('ascii'))
    labels.append(b'\x00')
    return b''.join(labels)

def _decode_name(data, offset):
    labels = []
    jumped = False
    orig_offset = offset
    while True:
        if offset >= len(data):
            break
        length = data[offset]
        if length & 0xC0:
            if not jumped:
                orig_offset = offset + 2
                jumped = True
            ptr = struct.unpack_from('!H', data, offset)[0] & 0x3FFF
            offset = ptr
            continue
        offset += 1
        if length == 0:
            break
        if offset + length > len(data):
            break
        labels.append(data[offset:offset+length].decode('ascii', errors='replace'))
        offset += length
    name = '.'.join(labels)
    end_offset = orig_offset if jumped else offset
    return name, end_offset

def debug_dns_lookup(domain='www.github.com'):
    """Perform a raw DNS CNAME query and print results."""
    qname = _encode_domain(domain)
    header = struct.pack('!HHHHHH', 0x1234, 0x0100, 1, 0, 0, 0)
    question = qname + struct.pack('!HH', 5, 1)
    packet = header + question

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.sendto(packet, ('8.8.8.8', 53))
    data, _ = sock.recvfrom(65535)
    sock.close()

    tid, flags, qdcount, ancount, nscount, arcount = struct.unpack_from('!HHHHHH', data, 0)
    print(f'ancount={ancount} nscount={nscount} arcount={arcount}')
    offset = 12

    for _ in range(qdcount):
        name, offset = _decode_name(data, offset)
        offset += 4

    for i in range(ancount):
        name, offset = _decode_name(data, offset)
        print(f'Answer {i}: name="{name}" offset={offset}')
        if offset + 10 > len(data):
            break
        rtype, rclass, ttl, rdlength = struct.unpack_from('!HHIH', data, offset)
        offset += 10
        rdata = data[offset:offset+rdlength]
        offset += rdlength
        print(f'  type={rtype} class={rclass} ttl={ttl} rdlen={rdlength}')
        print(f'  rdata hex: {rdata.hex()}')
        cname, end = _decode_name(rdata, 0)
        print(f'  cname="{cname}" end={end}')

if __name__ == '__main__':
    debug_dns_lookup()
