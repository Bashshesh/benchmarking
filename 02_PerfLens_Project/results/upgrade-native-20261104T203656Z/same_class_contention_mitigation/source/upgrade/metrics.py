"""Metric adapters and conservative configuration decisions; no new classifier."""
import math

JVM_CONFIGURATIONS = {'default': [], 'tier1': ['-XX:TieredStopAtLevel=1'], 'interpreter': ['-Xint']}

def jmh_single_fork(record):
    """A JMH invocation must contain exactly one benchmark and one independent fork."""
    if len(record)!=1:
        raise ValueError('One benchmark/parameter combination per invocation is required')
    value=record[0]
    metric=value['primaryMetric']
    raw=metric.get('rawData',[])
    if value.get('forks')!=1 or len(raw)!=1 or not raw[0]:
        raise ValueError('One independent JMH fork required; never flatten correlated iterations')
    if value.get('mode')!='avgt':
        raise ValueError('Adapter currently requires average operation time')
    units={'ns/op':1e-9,'us/op':1e-6,'ms/op':1e-3,'s/op':1.0}
    if metric['scoreUnit'] not in units:
        raise ValueError('Unsupported JMH score unit')
    seconds=metric['score']*units[metric['scoreUnit']]
    if not math.isfinite(seconds) or seconds<=0:
        raise ValueError('Invalid JMH timing')
    return dict(seconds=seconds,within_fork_iterations=raw[0],unit=metric['scoreUnit'],sampling_unit='one JVM fork')

def permitted_jvm(name):
    if name not in JVM_CONFIGURATIONS:
        raise ValueError('Configuration is not in the permitted JVM allowlist')
    return JVM_CONFIGURATIONS[name].copy()

def recommend(reference, candidate, comparison, correctness, cpu_ratio=None):
    """A fixed relative performance goal, with a descriptive resource guard."""
    if not correctness:
        return dict(selected=reference,reason='correctness not established')
    if comparison['decision']!='improvement' or comparison['ci95_percent'][1]>=-5:
        return dict(selected=reference,reason='no confirmed practically relevant improvement')
    if cpu_ratio is None or not math.isfinite(cpu_ratio) or cpu_ratio<0:
        return dict(selected=reference,reason='resource evidence is missing or invalid')
    if cpu_ratio is not None and cpu_ratio>1.10:
        return dict(selected=reference,reason='observed CPU mean exceeds the preselected 10% resource allowance')
    return dict(selected=candidate,reason='held-out interval supports >5% faster internal time; CPU guard passed',
                limitation='conditional recommendation; resource mean is not a confidence guarantee')

def dependence(values):
    """Descriptive lag-one correlation and first/second-half drift; no independence proof."""
    n=len(values)
    if n<4:
        raise ValueError('At least four ordered observations required')
    mean=sum(values)/n
    denom=sum((v-mean)**2 for v in values)
    lag=None if denom==0 else sum((values[i]-mean)*(values[i-1]-mean) for i in range(1,n))/denom
    first=sum(values[:n//2])/(n//2)
    second=sum(values[n//2:])/(n-n//2)
    return dict(lag_one_descriptive=lag,second_half_change_percent=100*(second/first-1),n=n)
