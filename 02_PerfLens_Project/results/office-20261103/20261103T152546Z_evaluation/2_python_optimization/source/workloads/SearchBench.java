import java.util.Arrays;

/** Sorted membership queries: sequential scan versus binary search. */
public class SearchBench {
    private static volatile long sink;

    static long search(int[] values, int[] queries, boolean optimized) {
        long count = 0;
        for (int query : queries) {
            if (optimized) {
                if (Arrays.binarySearch(values, query) >= 0) count++;
            } else {
                for (int value : values) {
                    if (value == query) { count++; break; }
                }
            }
        }
        return count;
    }

    public static void main(String[] args) {
        String variant = args[0];
        int size = Integer.parseInt(args[1]);
        int queryCount = Integer.parseInt(args[2]);
        int loops = Integer.parseInt(args[3]);
        int warmups = Integer.parseInt(args[4]);
        if ((!variant.equals("baseline") && !variant.equals("optimized")) ||
                size < 2 || queryCount < 1 || loops < 1 || warmups < 0) {
            throw new IllegalArgumentException("Invalid workload configuration");
        }
        int[] values = new int[size];
        int[] queries = new int[queryCount];
        for (int i = 0; i < size; i++) values[i] = 2 * i;
        long expected = 0;
        for (int i = 0; i < queryCount; i++) {
            queries[i] = (int)(((long)i * 7919) % (2L * size));
            if (queries[i] % 2 == 0) expected++;
        }
        boolean optimized = variant.equals("optimized");
        StringBuilder trace = new StringBuilder("[");
        for (int i = 0; i < warmups; i++) {
            long t = System.nanoTime();
            sink = search(values, queries, optimized);
            if (i > 0) trace.append(',');
            trace.append((System.nanoTime() - t) / 1e9);
            if (sink != expected) throw new AssertionError("Warmup checksum");
        }
        trace.append(']');
        long start = System.nanoTime();
        for (int i = 0; i < loops; i++) sink = search(values, queries, optimized);
        double seconds = (System.nanoTime() - start) / 1e9 / loops;
        if (sink != expected) throw new AssertionError("Wrong membership count");
        System.out.println("{\"seconds\":" + seconds + ",\"checksum\":" + sink +
                ",\"valid\":true,\"warmup_seconds\":" + trace + "}");
    }
}
