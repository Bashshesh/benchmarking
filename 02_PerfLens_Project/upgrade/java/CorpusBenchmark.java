package perflens.external;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;
import org.roaringbitmap.RoaringBitmap;

/** Real source-text byte-offset index; identical Apache-licensed input in both arms. */
@BenchmarkMode(Mode.AverageTime) @OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Thread) @Threads(1)
public class CorpusBenchmark {
  RoaringBitmap index;
  int[] blocks;
  int position;
  @Setup(Level.Trial) public void setup() throws Exception {
    byte[] bytes=Files.readAllBytes(Paths.get("/out/corpus.bin"));
    index=new RoaringBitmap();
    // Index non-whitespace source bytes, an input-derived text-filter proxy.
    for(int i=0;i<bytes.length;i++) if((bytes[i]&255)>32) index.add(i);
    blocks=new int[(bytes.length+65535)/65536];
    for(int b=0;b<blocks.length;b++) {
      blocks[b]=b;
      long lo=((long)b)<<16, hi=((long)b+1)<<16;
      long expected=0;
      for(long i=lo;i<Math.min(hi,bytes.length);i++)if((bytes[(int)i]&255)>32)expected++;
      if(index.rangeCardinality(lo,hi)!=expected)throw new AssertionError("corpus oracle");
    }
    if(blocks.length==0)throw new AssertionError("empty corpus");
  }
  @Benchmark public long fullBlock(){
    int b=blocks[position++%blocks.length];
    if(position==Integer.MAX_VALUE)position=0;
    return index.rangeCardinality(((long)b)<<16,((long)b+1)<<16);
  }
  @Benchmark public long nearBoundary(){
    int b=blocks[position++%blocks.length];
    if(position==Integer.MAX_VALUE)position=0;
    return index.rangeCardinality(((long)b)<<16,(((long)b+1)<<16)-1);
  }
}
