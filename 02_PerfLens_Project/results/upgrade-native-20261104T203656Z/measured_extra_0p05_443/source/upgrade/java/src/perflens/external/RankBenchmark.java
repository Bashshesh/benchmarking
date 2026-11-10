package perflens.external;
import java.util.Random;
import java.util.concurrent.TimeUnit;
import org.openjdk.jmh.annotations.*;
import org.roaringbitmap.BitmapContainer;
import org.roaringbitmap.RoaringBitmap;

/** Frozen external source for BOTH actual library revisions, not copied optimization logic. */
@BenchmarkMode(Mode.AverageTime) @OutputTimeUnit(TimeUnit.NANOSECONDS)
@State(Scope.Thread) @Threads(1)
public class RankBenchmark {
  @Param({"65535","65534"}) public int limit;
  @Param({"16"}) public int containers;
  BitmapContainer[] bitmaps;
  RoaringBitmap global;
  int index;
  @Setup(Level.Trial) public void setup(){
    bitmaps=new BitmapContainer[containers]; global=new RoaringBitmap();
    Random rng=new Random(8452026L);
    for(int c=0;c<containers;c++){
      long[] words=new long[1024];int count=0;
      for(int x=0;x<65536;x++) if(rng.nextBoolean()){
        words[x>>>6]|=1L<<(x&63);count++;global.add((c<<16)|x);
      }
      bitmaps[c]=new BitmapContainer(words,count);
    }
  }
  @Benchmark public int rank(){
    int c=index++%containers;
    // Reset index before integer overflow without relying on benchmark duration.
    if(index==Integer.MAX_VALUE)index=0;
    return bitmaps[c].rank((char)limit);
  }
  @Benchmark public long fullContainerRange(){
    int c=index++%containers;
    if(index==Integer.MAX_VALUE)index=0;
    return global.rangeCardinality(((long)c)<<16,((long)c+1)<<16);
  }
}
