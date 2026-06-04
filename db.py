from os import path
import sqlite3
from typing import Any, List, Optional
from collections import deque


def run_query(dbfile: str, query: str, parameters: List[Any]) -> list[Any]:
    conn = None
    try:
        ROOT = path.dirname(path.realpath(__file__))
        conn = sqlite3.connect(path.join(ROOT, dbfile))
        db = conn.cursor()
        db.execute(query, parameters)
        results = db.fetchall()
        conn.commit()
        return results
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_connections(actor_name: str, max_depth: int = 6, db_file: str = "movies.db") -> List[List[str]]:
    """Find connection chains from Kevin Bacon to `actor_name` up to `max_depth` degrees.

    Uses a memory-efficient BFS by querying the database for neighbors at each step.
    Optimized to find all shortest paths while minimizing memory footprint.
    """
    if not actor_name or actor_name == "Kevin Bacon":
        return []

    # helper to get person id by name
    def _person_id_by_name(name: str) -> Optional[int]:
        q = "SELECT id FROM people WHERE name = ?"
        rows = run_query(db_file, q, [name])
        return rows[0][0] if rows else None

    bacon_id = _person_id_by_name("Kevin Bacon")
    target_id = _person_id_by_name(actor_name)
    if bacon_id is None or target_id is None:
        return []

    # BFS: queue stores paths of (person_id, movie_title, person_name)
    q = deque([[(bacon_id, None, "Kevin Bacon")]])
    
    # Pruning: track min depth seen for each person to avoid cycles and redundant paths
    seen_people = {bacon_id: 0}
    results = []
    found_at_depth = None
    
    ROOT = path.dirname(path.realpath(__file__))
    conn = sqlite3.connect(path.join(ROOT, db_file))
    conn.row_factory = sqlite3.Row
    
    try:
        while q:
            path_list = q.popleft()
            last_person_id, _, _ = path_list[-1]
            current_depth = len(path_list) - 1
            
            # If we found shortest paths at a shallower depth, stop searching deeper
            if found_at_depth is not None and current_depth >= found_at_depth:
                break
                
            if current_depth >= max_depth:
                continue

            # Query neighbors using the indexes on the stars table
            cursor = conn.execute("""
                SELECT s2.person_id, m.title, p.name
                FROM stars s1
                JOIN stars s2 ON s1.movie_id = s2.movie_id
                JOIN movies m ON s1.movie_id = m.id
                JOIN people p ON s2.person_id = p.id
                WHERE s1.person_id = ? AND s2.person_id != ?
            """, (last_person_id, last_person_id))
            
            for row in cursor:
                next_person_id = row['person_id']
                movie_title = row['title']
                next_person_name = row['name']
                
                new_depth = current_depth + 1
                
                # Only explore this person if we haven't seen them at a shallower depth
                if next_person_id in seen_people and seen_people[next_person_id] < new_depth:
                    continue
                
                seen_people[next_person_id] = new_depth
                
                new_path = path_list + [(next_person_id, movie_title, next_person_name)]
                
                if next_person_id == target_id:
                    # Found a connection! Format for frontend
                    formatted = [path_list[0][2]] 
                    for i in range(1, len(new_path)):
                        _, m_title, p_name = new_path[i]
                        formatted.extend(["was in", m_title, "with", p_name])
                    results.append(formatted)
                    found_at_depth = new_depth
                elif new_depth < max_depth and (found_at_depth is None or new_depth < found_at_depth):
                    q.append(new_path)
                
    finally:
        conn.close()

    return results


def get_direct_connections(actor_name: str) -> List[Any]:
    # Default search limited to 2 degrees for "direct connections"
    return get_connections(actor_name, max_depth=2)
