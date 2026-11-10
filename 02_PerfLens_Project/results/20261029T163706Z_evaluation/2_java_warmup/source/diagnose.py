"""Profile graph-query work separately from the timing evaluation."""
import cProfile
import importlib.util
import io
from pathlib import Path
import pstats

from perflens import ROOT


def main():
    spec=importlib.util.spec_from_file_location('graph_queries',ROOT/'workloads/graph_queries.py')
    workload=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(workload)
    graph=workload.nx.grid_2d_graph(35,35)
    targets=[(i%35,(i*7+3)%35) for i in range(16)]
    expected=[x+y for x,y in targets]
    output=ROOT/'results/diagnosis'
    output.mkdir(exist_ok=True)
    lines=['# Graph-query diagnosis','',
        'cProfile runs are separate from the timing suite. Profiling overhead means these durations are diagnostic, not optimization effect estimates. Each variant performs ten operations over sixteen same-source targets on the same immutable 35x35 grid.','']
    for variant in ['baseline','optimized']:
        profiler=cProfile.Profile()
        profiler.enable()
        for _ in range(10):
            result=workload.query(graph,targets,variant)
        profiler.disable()
        if result!=expected:
            raise RuntimeError('Wrong distances during profiling')
        profiler.dump_stats(str(output/(variant+'.pstats')))
        buffer=io.StringIO()
        stats=pstats.Stats(profiler,stream=buffer).strip_dirs().sort_stats('cumulative')
        stats.print_stats(18)
        text=buffer.getvalue()
        (output/(variant+'.txt')).write_text(text,encoding='utf-8')
        lines += [f'## {variant}','', '```text',text,'```','']
    lines += ['## Diagnosis and justified change','',
        'The baseline recomputes all reachable distances for every target even though the source and graph stay unchanged. The optimized function computes one distance map per operation and looks up all sixteen targets. There is no cache across operations, and correctness is checked against Manhattan distances. Expected BFS call count falls from 160 to 10 in the ten-operation profile. The controlled timing suite, not these profiler durations, tests whether this diagnosis translates into improvement.',
        '', 'This is workload-level reuse, not a modification of NetworkX internals. It is justified when multiple queries share the source and the graph does not change. A mutable graph or isolated single-target queries require a different design. The optimized operation retains one distance map and the output list; peak memory was not measured.']
    (output/'DIAGNOSIS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(output/'DIAGNOSIS.md')


if __name__=='__main__':
    main()
