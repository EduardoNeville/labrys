#!/usr/bin/env python3
"""
Network/Graph Analysis of Sign Co-occurrence Patterns in Linear A.

Builds weighted undirected graphs (co-occurrence within same text) and
directed graphs (sequential adjacency), computes centrality metrics,
detects communities via label propagation, and outputs CSV summaries.

For site-specific analysis, builds separate graphs for:
  - Hagia Triada (incl. sub-areas)
  - Khania
  - Knossos
  - Zakros

Usage:
    python3 pipeline/network_analysis.py [--db DATA/lineara_full.db] [--out DATA/analysis/network/]
"""

import sqlite3
import csv
import os
import sys
import argparse
from collections import defaultdict, Counter, deque
import math
import random


# ── 1. Data Loading ──────────────────────────────────────────────────────────

def load_signs(db_path):
    """Load all signs with their inscription_id, sequence, and identifier.

    Returns list of dicts with keys:
        inscription_id, sequence, sign_id, bennett_id, character, sign_type
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT s.inscription_id, s.sequence,
               s.bennett_id, s.character, s.sign_type,
               i.findspot_id
        FROM signs s
        JOIN inscriptions i ON s.inscription_id = i.id
        ORDER BY s.inscription_id, s.sequence
    """)

    rows = []
    for row in cur:
        sign_id = row['bennett_id'] if row['bennett_id'] and row['bennett_id'].strip() else (
            row['character'] if row['character'] and row['character'].strip() else f"X_{row['inscription_id']}_{row['sequence']}"
        )
        rows.append({
            'inscription_id': row['inscription_id'],
            'sequence': row['sequence'],
            'sign_id': sign_id,
            'bennett_id': row['bennett_id'],
            'character': row['character'],
            'sign_type': row['sign_type'],
            'findspot_id': row['findspot_id'],
        })

    conn.close()
    return rows


def load_findspots(db_path):
    """Load findspot id → site name mapping."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, site FROM findspots")
    mapping = {row['id']: row['site'] for row in cur}
    conn.close()
    return mapping


def get_site_inscription_ids(rows, findspots, site_names):
    """Return set of inscription_ids belonging to sites whose name contains any of site_names."""
    site_ids = set()
    for fid, name in findspots.items():
        if any(sn.lower() in name.lower() for sn in site_names):
            site_ids.add(fid)

    ins_ids = set()
    for r in rows:
        if r['findspot_id'] in site_ids:
            ins_ids.add(r['inscription_id'])
    return ins_ids


# ── 2. Graph Construction ────────────────────────────────────────────────────

def build_cooccurrence_graph(rows, ins_ids=None):
    """Build weighted undirected graph: nodes = signs, edges = co-occurrence in same text.

    Returns adjacency dict: {node: {neighbor: weight}}
    """
    # Group signs by inscription
    ins_signs = defaultdict(set)
    for r in rows:
        if ins_ids is not None and r['inscription_id'] not in ins_ids:
            continue
        ins_signs[r['inscription_id']].add(r['sign_id'])

    adj = defaultdict(lambda: defaultdict(int))

    for ins_id, signs in ins_signs.items():
        sign_list = list(signs)
        for i in range(len(sign_list)):
            for j in range(i + 1, len(sign_list)):
                a, b = sign_list[i], sign_list[j]
                if a != b:
                    adj[a][b] += 1
                    adj[b][a] += 1

    return dict(adj)


def build_sequential_graph(rows, ins_ids=None):
    """Build directed weighted graph: edge A→B when A precedes B in sequence.

    Only consecutive signs within the same inscription.
    Returns adjacency dict: {node: {neighbor: weight}}
    """
    # Group signs by inscription, sorted by sequence
    ins_signs = defaultdict(list)
    for r in rows:
        if ins_ids is not None and r['inscription_id'] not in ins_ids:
            continue
        ins_signs[r['inscription_id']].append((r['sequence'], r['sign_id']))

    adj = defaultdict(lambda: defaultdict(int))

    for ins_id, seq_signs in ins_signs.items():
        seq_signs.sort(key=lambda x: x[0])
        for i in range(len(seq_signs) - 1):
            a = seq_signs[i][1]
            b = seq_signs[i + 1][1]
            if a != b:
                adj[a][b] += 1

    return dict(adj)


# ── 3. Graph Metrics ─────────────────────────────────────────────────────────

def get_nodes(adj):
    """Get set of all nodes from adjacency dict (handles both directed and undirected)."""
    nodes = set()
    for u, neighbors in adj.items():
        nodes.add(u)
        for v in neighbors:
            nodes.add(v)
    return nodes


def degree_centrality(adj, directed=False):
    """Compute degree centrality for each node."""
    nodes = get_nodes(adj)
    n = len(nodes)
    if n <= 2:
        return {node: 0.0 for node in nodes}

    cent = {}
    if directed:
        out_deg = {u: len(nbrs) for u, nbrs in adj.items()}
        in_deg = defaultdict(int)
        for u, nbrs in adj.items():
            for v in nbrs:
                in_deg[v] += 1
        for node in nodes:
            cent[node] = (out_deg.get(node, 0) + in_deg.get(node, 0)) / (2 * (n - 1))
    else:
        for node in nodes:
            deg = len(adj.get(node, {}))
            cent[node] = deg / (n - 1)
    return cent


def betweenness_centrality(adj, directed=False, sample_size=None):
    """Compute betweenness centrality using Brandes' algorithm.

    For large graphs, optional sample_size limits the number of source nodes.
    """
    nodes = sorted(get_nodes(adj))
    n = len(nodes)
    if n <= 2:
        return {node: 0.0 for node in nodes}

    # Convert to adjacency list form for faster access
    adj_list = {u: list(nbrs.keys()) for u, nbrs in adj.items()}
    for v in nodes:
        if v not in adj_list:
            adj_list[v] = []

    cent = defaultdict(float)

    sources = nodes
    if sample_size and sample_size < n:
        sources = random.sample(nodes, sample_size)

    for s in sources:
        # BFS stack
        stack = []
        pred = {v: [] for v in nodes}
        sigma = {v: 0 for v in nodes}
        dist = {v: -1 for v in nodes}
        sigma[s] = 1
        dist[s] = 0
        q = deque([s])

        while q:
            v = q.popleft()
            stack.append(v)
            for w in adj_list[v]:
                # w found for the first time?
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    q.append(w)
                # shortest path to w via v?
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)

        # Accumulation
        delta = {v: 0 for v in nodes}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                cent[w] += delta[w]

    # Normalize
    if not directed:
        factor = 2.0 / ((n - 1) * (n - 2)) if n > 2 else 0
    else:
        factor = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 0

    # If sampling, scale up
    if sample_size and sample_size < n:
        factor *= (n / sample_size)

    cent = {node: val * factor for node, val in cent.items()}
    for node in nodes:
        if node not in cent:
            cent[node] = 0.0
    return cent


def pagerank(adj, alpha=0.85, max_iter=100, tol=1e-6):
    """Compute PageRank for directed graph.

    Falls back to undirected interpretation if graph is undirected.
    """
    nodes = sorted(get_nodes(adj))
    n = len(nodes)
    if n == 0:
        return {}

    # Build out-degree
    out_deg = {u: len(nbrs) for u, nbrs in adj.items()}
    # Dangling nodes (no outgoing edges)
    dangling_nodes = [v for v in nodes if out_deg.get(v, 0) == 0]

    # Map node → index
    idx = {v: i for i, v in enumerate(nodes)}

    # Initialize
    rank = {v: 1.0 / n for v in nodes}

    for iteration in range(max_iter):
        new_rank = defaultdict(float)
        dangling_sum = sum(rank.get(v, 0) for v in dangling_nodes)

        teleport = (1 - alpha) / n

        for v in nodes:
            # Teleportation + dangling redistribution
            new_rank[v] = teleport + alpha * dangling_sum / n

        # Distribute from non-dangling nodes
        for u in nodes:
            if out_deg.get(u, 0) > 0:
                contrib = alpha * rank.get(u, 0) / out_deg[u]
                for w in adj[u]:
                    new_rank[w] += contrib

        # Check convergence
        diff = sum(abs(new_rank.get(v, 0) - rank.get(v, 0)) for v in nodes)
        rank = dict(new_rank)
        if diff < tol:
            break

    return rank


def clustering_coefficient(adj):
    """Compute local clustering coefficient for each node."""
    nodes = get_nodes(adj)
    coeffs = {}

    for v in nodes:
        neighbors = list(adj.get(v, {}).keys())
        k = len(neighbors)
        if k < 2:
            coeffs[v] = 0.0
        else:
            # Count edges among neighbors
            edges = 0
            for i in range(k):
                for j in range(i + 1, k):
                    a, b = neighbors[i], neighbors[j]
                    if b in adj.get(a, {}):
                        edges += 1
            coeffs[v] = (2.0 * edges) / (k * (k - 1))
    return coeffs


def label_propagation_communities(adj, max_iter=100):
    """Detect communities using Label Propagation Algorithm.

    Returns dict: {node: community_id}
    """
    nodes = sorted(get_nodes(adj))
    # Initialize each node with unique label
    labels = {v: i for i, v in enumerate(nodes)}
    n = len(nodes)

    for iteration in range(max_iter):
        changed = False
        # Shuffle node order for stochasticity
        order = list(nodes)
        random.shuffle(order)

        for v in order:
            neighbors = list(adj.get(v, {}).keys())
            if not neighbors:
                continue

            # Count label frequencies among neighbors (weighted by edge weight)
            label_counts = defaultdict(int)
            for w in neighbors:
                wt = adj[v].get(w, 1)
                label_counts[labels[w]] += wt

            # Find max frequency label(s)
            max_count = max(label_counts.values())
            best_labels = [lab for lab, cnt in label_counts.items() if cnt == max_count]

            # Choose the smallest label (deterministic tie-breaking)
            new_label = min(best_labels)
            if new_label != labels[v]:
                labels[v] = new_label
                changed = True

        if not changed:
            break

    # Renumber communities compactly
    unique_labels = {}
    next_id = 0
    community_of = {}
    for v in nodes:
        lab = labels[v]
        if lab not in unique_labels:
            unique_labels[lab] = next_id
            next_id += 1
        community_of[v] = unique_labels[lab]

    return community_of


def connected_components(adj):
    """Find connected components of the graph.

    Returns list of sets of nodes.
    """
    nodes = get_nodes(adj)
    visited = set()
    components = []

    for start in nodes:
        if start in visited:
            continue
        # BFS
        comp = set()
        q = deque([start])
        while q:
            v = q.popleft()
            if v in visited:
                continue
            visited.add(v)
            comp.add(v)
            for w in adj.get(v, {}):
                if w not in visited:
                    q.append(w)
        components.append(comp)

    return components


# ── 4. Output ────────────────────────────────────────────────────────────────

def write_centrality_csv(rows, degree_cent, between_cent, pagerank_vals, cluster_coeffs, output_dir, label="sign_centrality"):
    """Write centrality metrics CSV."""
    all_nodes = sorted(set(
        list(degree_cent.keys()) + list(between_cent.keys()) +
        list(pagerank_vals.keys()) + list(cluster_coeffs.keys())
    ))

    path = os.path.join(output_dir, f"{label}.csv")
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sign_id', 'degree_centrality', 'betweenness_centrality',
                        'pagerank', 'clustering_coefficient'])
        for node in all_nodes:
            writer.writerow([
                node,
                f"{degree_cent.get(node, 0):.6f}",
                f"{between_cent.get(node, 0):.6f}",
                f"{pagerank_vals.get(node, 0):.6f}",
                f"{cluster_coeffs.get(node, 0):.6f}",
            ])
    print(f"  ✏️  {path}")
    return path


def write_communities_csv(communities, output_dir, label="communities"):
    """Write community membership CSV."""
    path = os.path.join(output_dir, f"{label}.csv")
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sign_id', 'community_id'])
        for node in sorted(communities.keys()):
            writer.writerow([node, communities[node]])
    print(f"  ✏️  {path}")
    return path


def write_top_bridges_csv(between_cent, output_dir, top_n=30, label="top_bridges"):
    """Write signs with highest betweenness centrality."""
    sorted_nodes = sorted(between_cent.items(), key=lambda x: -x[1])
    path = os.path.join(output_dir, f"{label}.csv")
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['rank', 'sign_id', 'betweenness_centrality'])
        for rank, (node, val) in enumerate(sorted_nodes[:top_n], 1):
            writer.writerow([rank, node, f"{val:.6f}"])
    print(f"  ✏️  {path}")
    return path


def write_component_summary_csv(components, output_dir, label="component_summary"):
    """Write connected component summary."""
    comp_sizes = [(i, len(comp)) for i, comp in enumerate(components)]
    comp_sizes.sort(key=lambda x: -x[1])

    path = os.path.join(output_dir, f"{label}.csv")
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['component_id', 'size', 'node_count', 'signs'])
        for cid, size in comp_sizes:
            comp_nodes = components[cid]
            sample = sorted(comp_nodes)[:10]
            writer.writerow([cid, size, len(comp_nodes), '; '.join(sample)])
    print(f"  ✏️  {path}")
    return path


def write_sign_type_summary(rows, communities, output_dir, label="community_sign_types"):
    """Write summary of sign types per community."""
    # Build sign_id → sign_type mapping
    sign_types = {}
    for r in rows:
        sid = r['sign_id']
        if sid not in sign_types:
            sign_types[sid] = r['sign_type']

    # Community → sign_type counts
    comm_types = defaultdict(lambda: Counter())
    for sign_id, cid in communities.items():
        st = sign_types.get(sign_id, 'unknown')
        comm_types[cid][st] += 1

    path = os.path.join(output_dir, f"{label}.csv")
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['community_id', 'total_signs', 'sign_type_breakdown'])
        for cid in sorted(comm_types.keys()):
            breakdown = dict(comm_types[cid])
            total = sum(breakdown.values())
            breakdown_str = '; '.join(f"{st}:{cnt}" for st, cnt in sorted(breakdown.items()))
            writer.writerow([cid, total, breakdown_str])
    print(f"  ✏️  {path}")
    return path


def write_network_summary(adj_undirected, adj_directed, output_dir, label="network_summary"):
    """Write a summary of the network."""
    undirected_nodes = len(get_nodes(adj_undirected))
    directed_nodes = len(get_nodes(adj_directed))

    undirected_edges = sum(len(nbrs) for nbrs in adj_undirected.values()) // 2
    directed_edges = sum(len(nbrs) for nbrs in adj_directed.values())

    path = os.path.join(output_dir, f"{label}.csv")
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['undirected_nodes', undirected_nodes])
        writer.writerow(['undirected_edges', undirected_edges])
        writer.writerow(['directed_nodes', directed_nodes])
        writer.writerow(['directed_edges', directed_edges])
    print(f"  ✏️  {path}")
    return path


# ── 5. Main Pipeline ─────────────────────────────────────────────────────────

def analyze_graph(rows, name, output_dir, findspots=None, ins_ids=None):
    """Run full graph analysis on a subset of inscriptions."""
    print(f"\n{'='*60}")
    print(f"  Graph Analysis: {name}")
    print(f"{'='*60}")

    # Build graphs
    print("  Building co-occurrence graph...")
    adj_undirected = build_cooccurrence_graph(rows, ins_ids)
    print(f"    Nodes: {len(get_nodes(adj_undirected))}")
    print(f"    Edges (undirected): {sum(len(nbrs) for nbrs in adj_undirected.values()) // 2}")

    print("  Building sequential adjacency graph...")
    adj_directed = build_sequential_graph(rows, ins_ids)
    print(f"    Nodes: {len(get_nodes(adj_directed))}")
    print(f"    Edges (directed): {sum(len(nbrs) for nbrs in adj_directed.values())}")

    # Create subdirectory
    subdir = os.path.join(output_dir, name.replace(' ', '_').lower())
    os.makedirs(subdir, exist_ok=True)

    # Network summary
    print("  Writing network summary...")
    write_network_summary(adj_undirected, adj_directed, subdir, "network_summary")

    # Connected components
    print("  Computing connected components...")
    components = connected_components(adj_undirected)
    print(f"    Found {len(components)} components")
    write_component_summary_csv(components, subdir)

    # Degree centrality
    print("  Computing degree centrality...")
    degree_cent = degree_centrality(adj_undirected)

    # Betweenness centrality (with sampling for large graphs)
    n_nodes = len(get_nodes(adj_undirected))
    sample = min(200, n_nodes) if n_nodes > 500 else None
    print(f"  Computing betweenness centrality (sample={sample or 'all'})...")
    between_cent = betweenness_centrality(adj_undirected, sample_size=sample)

    # PageRank (on directed sequential graph)
    print("  Computing PageRank...")
    pagerank_vals = pagerank(adj_directed)

    # Clustering coefficient
    print("  Computing clustering coefficient...")
    cluster_coeffs = clustering_coefficient(adj_undirected)

    # Write centrality CSV
    write_centrality_csv(rows, degree_cent, between_cent, pagerank_vals, cluster_coeffs, subdir)

    # Top bridges
    write_top_bridges_csv(between_cent, subdir)

    # Community detection
    print("  Running label propagation community detection...")
    communities = label_propagation_communities(adj_undirected)
    num_communities = len(set(communities.values()))
    print(f"    Found {num_communities} communities")

    # Per-community sign type breakdown
    write_sign_type_summary(rows, communities, subdir)

    # Write communities
    write_communities_csv(communities, subdir)

    # Print top central signs
    print(f"\n  Top 10 signs by degree centrality:")
    top_deg = sorted(degree_cent.items(), key=lambda x: -x[1])[:10]
    for node, val in top_deg:
        print(f"    {node:>12s}  {val:.4f}")

    print(f"\n  Top 10 bridging signs (betweenness):")
    top_bet = sorted(between_cent.items(), key=lambda x: -x[1])[:10]
    for node, val in top_bet:
        print(f"    {node:>12s}  {val:.6f}")

    print(f"\n  Top 10 signs by PageRank:")
    top_pr = sorted(pagerank_vals.items(), key=lambda x: -x[1])[:10]
    for node, val in top_pr:
        print(f"    {node:>12s}  {val:.6f}")

    print(f"\n  Communities (size ≥ 5):")
    comm_sizes = Counter(communities.values())
    for cid, size in sorted(comm_sizes.items(), key=lambda x: -x[1]):
        if size >= 5:
            members = [n for n, c in communities.items() if c == cid]
            print(f"    Community {cid:>3d}: {size:>4d} members — {', '.join(sorted(members[:8]))}{'...' if size > 8 else ''}")

    return adj_undirected, adj_directed, communities


def main():
    parser = argparse.ArgumentParser(description="Linear A sign network analysis")
    parser.add_argument("--db", default="/home/eduardoneville/projects/labrys/data/database/lineara_full.db",
                        help="Path to SQLite database")
    parser.add_argument("--out", default="/home/eduardoneville/projects/labrys/data/analysis/network",
                        help="Output directory for analysis files")
    args = parser.parse_args()

    db_path = args.db
    output_dir = args.out

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # ── Load data ──
    print("Loading signs...")
    rows = load_signs(db_path)
    print(f"  Loaded {len(rows)} sign occurrences")

    findspots = load_findspots(db_path)
    print(f"  Loaded {len(findspots)} findspots")

    # ── Global analysis ──
    analyze_graph(rows, "global", output_dir, findspots)

    # ── Site-specific analysis ──
    # Hagia Triada: findspot entries containing "Haghia Triada"
    sites = {
        "hagia_triada": ["Haghia Triada"],
        "khania": ["Khania"],
        "knossos": ["Knossos"],
        "zakros": ["Zakros"],
    }

    for site_label, site_names in sites.items():
        ins_ids = get_site_inscription_ids(rows, findspots, site_names)
        n_ins = len(ins_ids)
        n_signs = sum(1 for r in rows if r['inscription_id'] in ins_ids)
        if n_ins == 0:
            print(f"\n  ⚠️  No inscriptions found for {site_label}, skipping.")
            continue
        print(f"\n  {site_label}: {n_ins} inscriptions, {n_signs} sign occurrences")
        analyze_graph(rows, site_label, output_dir, findspots, ins_ids)

    print(f"\n{'='*60}")
    print("  ✅ All analyses complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
