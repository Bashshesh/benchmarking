package perflens.external;
import java.nio.file.*;
import org.roaringbitmap.RoaringBitmap;
/** Supplemental full/near boundary membership oracle for the retained real input. */
public class CorpusCorrectnessMain {
 public static void main(String[] args) throws Exception {
  byte[] input=Files.readAllBytes(Paths.get("/out/corpus.bin"));
  RoaringBitmap bitmap=new RoaringBitmap();
  for(int i=0;i<input.length;i++)if((input[i]&255)>32)bitmap.add(i);
  long checksum=0;int cases=0;
  for(long start=0;start<input.length;start+=65536){
   for(long end:new long[]{start+65536,start+65535}){
    long expected=0;
    for(long i=start;i<Math.min(end,input.length);i++)if((input[(int)i]&255)>32)expected++;
    long actual=bitmap.rangeCardinality(start,end);
    if(actual!=expected)throw new AssertionError("input range oracle");
    checksum+=actual;cases++;
   }
  }
  System.out.println("{\"valid\":true,\"cases\":"+cases+",\"checksum\":"+checksum+"}");
 }
}
