package perflens.external;
import java.util.Random;
import org.roaringbitmap.BitmapContainer;
import org.roaringbitmap.RoaringBitmap;

/** Independent boolean membership/rank oracle, outside JMH measurement. */
public class CorrectnessMain {
  public static void main(String[] args){
    long checksum=0;
    for(int seed=0;seed<4;seed++){
      boolean[] membership=new boolean[65536];long[] words=new long[1024];int count=0;
      Random rng=new Random(8452026L+seed);
      RoaringBitmap global=new RoaringBitmap();
      for(int x=0;x<65536;x++){
        boolean included=seed==0?false:seed==1?true:rng.nextBoolean();
        membership[x]=included;
        if(included){words[x>>>6]|=1L<<(x&63);count++;global.add(x);}
      }
      BitmapContainer bitmap=new BitmapContainer(words,count);
      for(int limit:new int[]{0,1,32767,65534,65535}){
        int expected=0;for(int x=0;x<=limit;x++)if(membership[x])expected++;
        if(bitmap.rank((char)limit)!=expected)throw new AssertionError("rank mismatch seed="+seed+" limit="+limit);
        checksum+=expected;
      }
      if(global.rangeCardinality(0,65536L)!=count)throw new AssertionError("range mismatch");
      checksum+=count;
    }
    System.out.println("{\"valid\":true,\"checksum\":"+checksum+",\"cases\":24,\"oracle\":\"boolean membership\"}");
  }
}
