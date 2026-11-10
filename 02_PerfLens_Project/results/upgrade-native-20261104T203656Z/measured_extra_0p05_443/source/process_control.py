"""Windows job ownership for benchmark trees, including orphaned descendants."""
import ctypes
from ctypes import wintypes
from time import monotonic, sleep


class BasicAccounting(ctypes.Structure):
    _fields_ = [(name,ctypes.c_longlong) for name in ['user','kernel','period_user','period_kernel']] + [
        (name,wintypes.DWORD) for name in ['page_faults','total_processes','active_processes','terminated_processes']]


class BasicLimits(ctypes.Structure):
    _fields_ = [('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),
                ('flags',wintypes.DWORD),('min_working_set',ctypes.c_size_t),
                ('max_working_set',ctypes.c_size_t),('active_processes',wintypes.DWORD),
                ('affinity',ctypes.c_size_t),('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]


class IoCounters(ctypes.Structure):
    _fields_ = [(name,ctypes.c_ulonglong) for name in ['read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes']]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic',BasicLimits),('io',IoCounters),('process_memory',ctypes.c_size_t),
                ('job_memory',ctypes.c_size_t),('peak_process_memory',ctypes.c_size_t),('peak_job_memory',ctypes.c_size_t)]


class WindowsJob:
    def __init__(self):
        self.api=ctypes.WinDLL('kernel32',use_last_error=True)
        self.api.CreateJobObjectW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype=wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
        self.api.SetInformationJobObject.restype=wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes=[wintypes.HANDLE,wintypes.HANDLE]
        self.api.AssignProcessToJobObject.restype=wintypes.BOOL
        self.api.TerminateJobObject.argtypes=[wintypes.HANDLE,wintypes.UINT]
        self.api.TerminateJobObject.restype=wintypes.BOOL
        self.api.QueryInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD,ctypes.c_void_p]
        self.api.QueryInformationJobObject.restype=wintypes.BOOL
        self.api.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        self.api.OpenProcess.restype=wintypes.HANDLE
        self.api.CloseHandle.argtypes=[wintypes.HANDLE]
        self.api.CloseHandle.restype=wintypes.BOOL
        self.handle=self.api.CreateJobObjectW(None,None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits=ExtendedLimits()
        limits.basic.flags=0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            error=ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def assign(self,pid):
        process=self.api.OpenProcess(0x0100|0x0001,False,pid)  # SET_QUOTA | TERMINATE
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.api.AssignProcessToJobObject(self.handle,process):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.api.CloseHandle(process)

    def terminate(self):
        if self.handle:
            if not self.api.TerminateJobObject(self.handle,1):
                raise ctypes.WinError(ctypes.get_last_error())
            deadline=monotonic()+5
            while True:
                state=BasicAccounting()
                if not self.api.QueryInformationJobObject(self.handle,1,ctypes.byref(state),ctypes.sizeof(state),None):
                    raise ctypes.WinError(ctypes.get_last_error())
                if state.active_processes==0:
                    break
                if monotonic()>=deadline:
                    raise TimeoutError('Windows job still has active processes after termination')
                sleep(.005)

    def close(self):
        if self.handle:
            try:
                self.terminate()
            finally:
                self.api.CloseHandle(self.handle)
                self.handle=None
