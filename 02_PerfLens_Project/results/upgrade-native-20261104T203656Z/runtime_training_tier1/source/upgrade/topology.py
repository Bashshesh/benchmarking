"""Read-only native Windows CPU-set topology and portable diagnostic probes."""
import ctypes
from ctypes import wintypes
import os
import struct
import psutil

def cpu_sets():
    if os.name!='nt':
        return dict(status='unavailable',reason='Windows CPU-set API not applicable')
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    call=api.GetSystemCpuSetInformation
    call.argtypes=[ctypes.c_void_p,wintypes.ULONG,ctypes.POINTER(wintypes.ULONG),wintypes.HANDLE,wintypes.ULONG]
    call.restype=wintypes.BOOL
    needed=wintypes.ULONG()
    call(None,0,ctypes.byref(needed),None,0)
    if not needed.value:
        return dict(status='unavailable',error=ctypes.get_last_error())
    buf=ctypes.create_string_buffer(needed.value)
    if not call(buf,needed.value,ctypes.byref(needed),None,0):
        return dict(status='unavailable',error=ctypes.get_last_error())
    rows=[]
    offset=0
    while offset<needed.value:
        size,kind=struct.unpack_from('<II',buf,offset)
        if size<8 or offset+size>needed.value:
            raise ValueError('Invalid CPU-set API record length')
        if kind==0 and size>=32:
            ident,group,logical,core,cache,numa,efficiency,flags=struct.unpack_from('<IHBBBBBB',buf,offset+8)
            rows.append(dict(id=ident,group=group,logical=logical,core=core,llc=cache,numa=numa,
                             efficiency_class=efficiency,flags=flags))
        offset+=size
    return dict(status='observed',cpu_sets=rows,source='Windows GetSystemCpuSetInformation',
                interpretation='higher efficiency_class means faster/less power-efficient; index is not frequency')

def diagnostic_probe():
    try:
        freq=psutil.cpu_freq(percpu=True)
        frequency=[v._asdict() for v in freq]
    except (AttributeError,NotImplementedError,OSError):
        frequency=None
    return dict(cpu_frequency_mhz=frequency,system_cpu_times=psutil.cpu_times()._asdict(),
                system_context_switches=psutil.cpu_stats().ctx_switches,
                limitation='system-wide/coarse observations; cannot attribute all scheduling or frequency changes to workload',
                thermal_sensor='not collected',hardware_counters='not available in this native collector')
