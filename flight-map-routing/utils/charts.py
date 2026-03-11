import time
import pandas as pd
import plotly.graph_objects as go

try:
    from src.algorithms.astar import astar_shortest_path
    ASTAR_AVAILABLE = True
except ImportError:
    ASTAR_AVAILABLE = False


def create_route_analysis(graph, path):
    segments = []

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        for edge in graph.neighbors(u):
            if edge.dst == v:
                segments.append({
                    'segment': f"{u} → {v}",
                    'distance': edge.km,
                    'time': edge.minutes,
                    'price': edge.price
                })
                break

    if not segments:
        return go.Figure()

    df = pd.DataFrame(segments)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Distance (km)',
        x=df['segment'],
        y=df['distance'],
        marker_color='#667eea',
        text=df['distance'].round(),
        textposition='auto',
    ))

    fig.add_trace(go.Bar(
        name='Time (min)',
        x=df['segment'],
        y=df['time'],
        marker_color='#28a745',
        text=df['time'],
        textposition='auto',
        yaxis='y2'
    ))

    fig.update_layout(
        title='Route Segment Analysis',
        xaxis_title='Flight Segments',
        yaxis=dict(title='Distance (km)', title_font=dict(color='#667eea')),
        yaxis2=dict(title='Time (minutes)', overlaying='y', side='right',
                    title_font=dict(color='#28a745')),
        barmode='group',
        height=500,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    return fig


def create_performance_comparison(graph, src, dst, mode):
    algorithms = []

    from src.algorithms.bfs import bfs_least_hops
    algorithms.append(('BFS', lambda: bfs_least_hops(graph, src, dst)))

    from src.algorithms.dijkstra import dijkstra
    if mode == 'distance':
        weight = lambda e: e.km
    elif mode == 'time':
        weight = lambda e: e.minutes
    elif mode == 'price':
        weight = lambda e: e.price
    else:
        weight = lambda e: 1

    algorithms.append(('Dijkstra', lambda: dijkstra(graph, src, dst, weight)))

    if ASTAR_AVAILABLE:
        try:
            from src.algorithms.astar import astar_shortest_path
            algorithms.append(('A*', lambda: astar_shortest_path(graph, src, dst, weight)))
        except Exception:
            pass

    results = []
    for name, algo_func in algorithms:
        start = time.time()
        try:
            path = algo_func()
            elapsed = (time.time() - start) * 1000

            results.append({
                'Algorithm': name,
                'Time (ms)': round(elapsed, 2),
                'Path Length': len(path) if path else 0,
                'Found': '✓' if path else '✗'
            })
        except Exception:
            results.append({
                'Algorithm': name,
                'Time (ms)': 0,
                'Path Length': 0,
                'Found': '✗'
            })

    if not results:
        return go.Figure()

    df = pd.DataFrame(results)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['Algorithm'],
        y=df['Time (ms)'],
        marker_color=['#667eea', '#28a745', '#ffc107', '#dc3545'][:len(df)],
        text=df['Time (ms)'],
        textposition='auto',
    ))

    fig.update_layout(
        title='Algorithm Performance Comparison',
        xaxis_title='Algorithm',
        yaxis_title='Time (milliseconds)',
        height=500,
        showlegend=False,
        annotations=[
            dict(
                x=row['Algorithm'],
                y=row['Time (ms)'] + (max(df['Time (ms)']) * 0.05 if max(df['Time (ms)']) > 0 else 5),
                text=f"Found: {row['Found']} | Nodes: {row['Path Length']}",
                showarrow=False,
                font=dict(size=10)
            ) for _, row in df.iterrows()
        ] if not df.empty else []
    )

    return fig
