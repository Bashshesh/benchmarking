# Graph-query diagnosis

cProfile runs are separate from the timing suite. Profiling overhead means these durations are diagnostic, not optimization effect estimates. Each variant performs ten operations over sixteen same-source targets on the same immutable 35x35 grid.

## baseline

```text
         784702 function calls (784697 primitive calls) in 0.221 seconds

   Ordered by: cumulative time
   List reduced from 65 to 18 due to restriction <18>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
       10    0.000    0.000    0.221    0.022 graph_queries.py:15(query)
      160    0.000    0.000    0.221    0.001 <class 'networkx.utils.decorators.argmap'> compilation 24:1(argmap_single_source_shortest_path_length_21)
      160    0.000    0.000    0.221    0.001 backends.py:541(_call_if_no_backends_installed)
      160    0.028    0.000    0.220    0.001 unweighted.py:21(single_source_shortest_path_length)
   196160    0.137    0.000    0.193    0.000 unweighted.py:83(_single_shortest_path_length)
   195842    0.022    0.000    0.022    0.000 {method 'add' of 'set' objects}
   196014    0.019    0.000    0.019    0.000 {method 'append' of 'list' objects}
   195841    0.015    0.000    0.015    0.000 {built-in method builtins.len}
        1    0.000    0.000    0.002    0.002 decorators.py:784(func)
        1    0.000    0.000    0.000    0.000 decorators.py:715(_lazy_compile)
        1    0.000    0.000    0.000    0.000 decorators.py:873(compile)
        1    0.000    0.000    0.000    0.000 decorators.py:921(assemble)
        1    0.000    0.000    0.000    0.000 decorators.py:1063(signature)
      2/1    0.000    0.000    0.000    0.000 inspect.py:3346(signature)
      2/1    0.000    0.000    0.000    0.000 inspect.py:3081(from_callable)
      2/1    0.000    0.000    0.000    0.000 inspect.py:2501(_signature_from_callable)
        1    0.000    0.000    0.000    0.000 backends.py:503(__signature__)
        1    0.000    0.000    0.000    0.000 {built-in method builtins.compile}



```

## optimized

```text
         49031 function calls in 0.014 seconds

   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
       10    0.000    0.000    0.014    0.001 graph_queries.py:15(query)
       10    0.000    0.000    0.014    0.001 <class 'networkx.utils.decorators.argmap'> compilation 24:1(argmap_single_source_shortest_path_length_21)
       10    0.000    0.000    0.014    0.001 backends.py:541(_call_if_no_backends_installed)
       10    0.002    0.000    0.014    0.001 unweighted.py:21(single_source_shortest_path_length)
    12260    0.009    0.000    0.012    0.000 unweighted.py:83(_single_shortest_path_length)
    12240    0.001    0.000    0.001    0.000 {method 'add' of 'set' objects}
    12240    0.001    0.000    0.001    0.000 {method 'append' of 'list' objects}
    12240    0.001    0.000    0.001    0.000 {built-in method builtins.len}
        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
       10    0.000    0.000    0.000    0.000 graph.py:472(__contains__)



```

## Diagnosis and justified change

The baseline recomputes all reachable distances for every target even though the source and graph stay unchanged. The optimized function computes one distance map per operation and looks up all sixteen targets. There is no cache across operations, and correctness is checked against Manhattan distances. Expected BFS call count falls from 160 to 10 in the ten-operation profile. The controlled timing suite, not these profiler durations, tests whether this diagnosis translates into improvement.

This is workload-level reuse, not a modification of NetworkX internals. It is justified when multiple queries share the source and the graph does not change. A mutable graph or isolated single-target queries require a different design. The optimized operation retains one distance map and the output list; peak memory was not measured.
