package perflens.external;
import java.lang.management.*;
import java.util.*;
import org.roaringbitmap.BitmapContainer;
/** Separate instrumented actual-library workload, never a clean timing replicate. */
public class RankDiagnostic {
 public static void main(String[] args) {
  int limit=Integer.parseInt(args[0]);
  BitmapContainer[] bitmap=new BitmapContainer[16];
  Random rng=new Random(8452026L);
  for(int c=0;c<16;c++){
   long[] words=new long[1024];int count=0;
   for(int i=0;i<1024;i++){words[i]=rng.nextLong();count+=Long.bitCount(words[i]);}
   bitmap[c]=new BitmapContainer(words,count);
  }
  long end=System.nanoTime()+3_000_000_000L, checksum=0, operations=0;
  while(System.nanoTime()<end){
   for(int c=0;c<16;c++)checksum+=bitmap[c].rank((char)limit);
   operations+=16;
  }
  System.out.println("{\"valid\":true,\"operations\":"+operations+",\"checksum\":"+checksum+"}");
 }
}
