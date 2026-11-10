package perflens.finalstudy;

import java.util.Random;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;
import org.roaringbitmap.BitmapContainer;

@BenchmarkMode(Mode.SingleShotTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Threads(1)
@State(Scope.Thread)
public class LazyRank {
    static final int SIZE = 256;
    static final char MAX = Character.MAX_VALUE;

    @Param({"cached", "first", "repeat"}) public String scenario;
    @Param({"false"}) public boolean repairs;
    private final long[][] words = new long[16][1024];
    private final int[] expected = new int[16];
    private final BitmapContainer[] batch = new BitmapContainer[SIZE];

    @Setup(Level.Trial)
    public void initialize() {
        Random random = new Random(8452026L);
        for (int i = 0; i < words.length; i++) {
            for (int bit = 0; bit < 65536; bit++) {
                if (random.nextBoolean()) {
                    words[i][bit >>> 6] |= 1L << (bit & 63);
                    expected[i]++;
                }
            }
            BitmapContainer probe = new BitmapContainer(words[i], -1);
            for (int call = 0; call < 2; call++) {
                if (probe.rank(MAX) != expected[i] ||
                    probe.getCardinality() != (repairs ? expected[i] : -1)) {
                    throw new AssertionError("Incorrect lazy rank semantics");
                }
            }
        }
        // Single-shot iterations alone invoke the batch driver only 50 times.
        // Exercise it with the exact scenario before JMH starts timing shots.
        int total = 0;
        for (int cardinality : expected) total += cardinality;
        int expectedSum = total * (SIZE / words.length);
        for (int call = 0; call < 16000; call++) {
            prepare();
            if (rankBatch() != expectedSum) throw new AssertionError("Incorrect warmup checksum");
        }
    }

    @Setup(Level.Iteration)
    public void prepare() {
        for (int i = 0; i < SIZE; i++) {
            int fixture = i % words.length;
            int cardinality = expected[fixture];
            BitmapContainer bitmap = new BitmapContainer(words[fixture],
                    scenario.equals("cached") ? cardinality : -1);
            if (scenario.equals("repeat") && bitmap.rank(MAX) != cardinality) {
                throw new AssertionError("Incorrect priming result");
            }
            int initial = scenario.equals("cached") || (scenario.equals("repeat") && repairs)
                    ? cardinality : -1;
            if (bitmap.getCardinality() != initial) {
                throw new AssertionError("Incorrect state before timing");
            }
            batch[i] = bitmap;
        }
    }

    @Benchmark
    @OperationsPerInvocation(SIZE)
    public int rankBatch() {
        int sum = 0;
        for (BitmapContainer bitmap : batch) {
            sum += bitmap.rank(MAX);
        }
        return sum;
    }

    @TearDown(Level.Iteration)
    public void verify() {
        for (int i = 0; i < SIZE; i++) {
            int cardinality = expected[i % words.length];
            if (batch[i].getCardinality() != (scenario.equals("cached") || repairs ? cardinality : -1)) {
                throw new AssertionError("Incorrect post-shot cardinality");
            }
        }
    }

    public static void main(String[] args) {
        LazyRank fixture = new LazyRank();
        fixture.repairs = Boolean.parseBoolean(args[0]);
        fixture.scenario = "first";
        fixture.initialize();
        int total = 0;
        for (int cardinality : fixture.expected) total += cardinality;
        for (String scenario : new String[]{"cached", "first", "repeat"}) {
            fixture.scenario = scenario;
            fixture.prepare();
            if (fixture.rankBatch() != total * (SIZE / fixture.words.length)) {
                throw new AssertionError("Incorrect batch checksum");
            }
            fixture.verify();
        }
        System.out.println("valid: 16 independent membership counts, 3 batch checks, repairs="
                + fixture.repairs + ", checksum=" + total * (SIZE / fixture.words.length));
    }
}
