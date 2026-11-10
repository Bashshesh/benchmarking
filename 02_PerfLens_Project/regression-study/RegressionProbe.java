import java.nio.file.Path;
import jdk.jfr.Recording;

public class RegressionProbe {
    private static volatile long sink;

    public static void main(String[] args) throws Exception {
        boolean optimized = args[0].equals("optimized");
        int size = Integer.parseInt(args[1]);
        int queryCount = Integer.parseInt(args[2]);
        int warmups = Integer.parseInt(args[3]);
        int rounds = Integer.parseInt(args[4]);
        int[] values = new int[size];
        int[] queries = new int[queryCount];
        int expected = 0;
        for (int i = 0; i < size; i++) values[i] = 2 * i;
        for (int i = 0; i < queryCount; i++) {
            queries[i] = (int)((long)i * 7919 % (2L * size));
            if (queries[i] % 2 == 0) expected++;
        }
        run(values, queries, optimized, warmups, expected);
        if (args.length == 6) {
            try (Recording recording = new Recording()) {
                recording.enable("jdk.ExecutionSample")
                         .withPeriod(java.time.Duration.ofMillis(10)).withStackTrace();
                recording.start();
                System.out.println(run(values, queries, optimized, rounds, expected));
                recording.stop();
                recording.dump(Path.of(args[5]));
            }
        } else {
            System.out.println(run(values, queries, optimized, rounds, expected));
        }
    }

    private static double run(int[] values, int[] queries, boolean optimized,
                              int rounds, int expected) {
        long start = System.nanoTime();
        for (int i = 0; i < rounds; i++) {
            sink = SearchBench.search(values, queries, optimized);
            if (sink != expected) throw new AssertionError("Incorrect checksum");
        }
        return (System.nanoTime() - start) / 1e9 / rounds;
    }
}
