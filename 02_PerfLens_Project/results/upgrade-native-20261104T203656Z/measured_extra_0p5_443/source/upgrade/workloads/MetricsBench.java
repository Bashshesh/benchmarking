import java.lang.management.ManagementFactory;
import java.util.Arrays;

/** Project-owned extension to SearchBench; no third-party repository code. */
public class MetricsBench {
  static volatile long sink;
  public static void main(String[] args) {
    String variant=args.length>0?args[0]:"optimized";
    int loops=args.length>1?Integer.parseInt(args[1]):2000;
    int warmups=args.length>2?Integer.parseInt(args[2]):100;
    boolean trace=args.length>3 && args[3].equals("latency");
    if (!(variant.equals("baseline")||variant.equals("optimized"))||loops<1||warmups<0) throw new IllegalArgumentException();
    int[] values=new int[20000], queries=new int[2000];
    for(int i=0;i<values.length;i++)values[i]=i*2;
    long expected=0;
    for(int i=0;i<queries.length;i++){queries[i]=(int)(((long)i*7919)%(values.length*2));if((queries[i]&1)==0)expected++;}
    long answer=SearchBench.search(values,queries,variant.equals("optimized"));
    if(answer!=expected)throw new AssertionError("Independent membership oracle failed");
    for(int i=0;i<warmups;i++)sink=SearchBench.search(values,queries,variant.equals("optimized"));
    com.sun.management.OperatingSystemMXBean os=(com.sun.management.OperatingSystemMXBean)ManagementFactory.getOperatingSystemMXBean();
    java.lang.management.ThreadMXBean raw=ManagementFactory.getThreadMXBean();
    com.sun.management.ThreadMXBean thread=raw instanceof com.sun.management.ThreadMXBean?(com.sun.management.ThreadMXBean)raw:null;
    if(thread!=null && thread.isThreadAllocatedMemorySupported() && !thread.isThreadAllocatedMemoryEnabled())thread.setThreadAllocatedMemoryEnabled(true);
    long tid=Thread.currentThread().threadId();
    long[] latencies=trace?new long[loops]:null;
    long cpu0=os.getProcessCpuTime();
    long alloc0=thread!=null && thread.isThreadAllocatedMemorySupported()?thread.getThreadAllocatedBytes(tid):-1;
    long start=System.nanoTime();
    for(int i=0;i<loops;i++){
      long t=trace?System.nanoTime():0;
      // Change one known-present query deterministically to avoid an invariant operation.
      // Its membership remains true, so the independent expected count is unchanged.
      queries[0]=(i%values.length)*2;
      sink=SearchBench.search(values,queries,variant.equals("optimized"));
      if(trace)latencies[i]=System.nanoTime()-t;
    }
    long elapsed=System.nanoTime()-start;
    long alloc1=alloc0>=0?thread.getThreadAllocatedBytes(tid):-1;
    long cpu1=os.getProcessCpuTime();
    if(sink!=expected)throw new AssertionError("Incorrect timed membership result");
    String tails="null";
    String rawLatency=trace?Arrays.toString(latencies):"null";
    if(trace){Arrays.sort(latencies);tails="{\"median_seconds\":"+latencies[(loops-1)/2]/1e9+",\"p95_seconds\":"+latencies[(int)Math.ceil(.95*loops)-1]/1e9+",\"p99_seconds\":"+latencies[(int)Math.ceil(.99*loops)-1]/1e9+"}";}
    String cpu=cpu0>=0 && cpu1>=cpu0?Double.toString((cpu1-cpu0)/1e9/loops):"null";
    String allocation=alloc0>=0 && alloc1>=alloc0?Double.toString((double)(alloc1-alloc0)/loops):"null";
    System.out.println("{\"seconds\":"+(elapsed/1e9/loops)+",\"checksum\":"+sink+",\"valid\":true,\"process_cpu_seconds_per_operation\":"+cpu+",\"thread_allocated_bytes_per_operation\":"+allocation+",\"throughput_ops_per_second\":"+(loops/(elapsed/1e9))+",\"loops\":"+loops+",\"warmups\":"+warmups+",\"latency_diagnostic\":"+trace+",\"latencies\":"+tails+",\"latency_nanoseconds\":"+rawLatency+"}");
  }
}
