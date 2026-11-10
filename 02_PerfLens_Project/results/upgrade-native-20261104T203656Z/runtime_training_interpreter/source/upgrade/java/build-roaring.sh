#!/bin/sh
set -eu
java -version
javac -version
sha256sum /opt/jmh/*.jar
# Only run inside the restricted container documented in REPRODUCE.md.
mkdir -p /out/library /out/harness /out/generated
if [ -d /src/roaringbitmap/src/main/java ]; then
  find /src/roaringbitmap/src/main/java -name '*.java' ! -name module-info.java > /out/library-sources.txt
elif [ -d /src/RoaringBitmap/src/main/java ]; then
  find /src/RoaringBitmap/src/main/java -name '*.java' ! -name module-info.java > /out/library-sources.txt
else
  echo 'Expected pinned RoaringBitmap source layout not found' >&2; exit 2
fi
if [ -d /src/shims/src/main/java ]; then find /src/shims/src/main/java -name '*.java' >> /out/library-sources.txt; fi
javac -proc:none --release 8 -d /out/library @/out/library-sources.txt
jmhcp=$(find /opt/jmh -name '*.jar' | paste -sd: -)
find /harness/src -name '*.java' > /out/harness-sources.txt
javac -cp "/out/library:$jmhcp" -processorpath "$jmhcp" -processor org.openjdk.jmh.generators.BenchmarkProcessor -s /out/generated -d /out/harness @/out/harness-sources.txt
java -cp "/out/library:/out/harness:$jmhcp" perflens.external.CorrectnessMain
java -cp "/out/library:/out/harness:$jmhcp" org.openjdk.jmh.Main -l
printf '%s\n' "/out/library:/out/harness:$jmhcp" > /out/classpath.txt
