from os import path
import sqlite3
from typing import Any, Final, List, Dict, Optional
from collections import deque


def run_query(dbfile: str, query: str, parameters: List[str]) -> list[Any]:
    conn = None
    try:
        ROOT = path.dirname(path.realpath(__file__))
        conn = sqlite3.connect(path.join(ROOT, dbfile))
        db = conn.cursor()
        db.execute(query, parameters)
        conn.commit()
        return db.fetchall()
    except sqlite3.Error as e:
        if conn:
            conn.close()


def get_connections(actor_name: str, max_depth: int = 6, db_file: str = "movies.db") -> List[str]:
    """Find connection chains from Kevin Bacon to `actor_name` up to `max_depth` degrees.

    Returns a list of formatted connection strings. Depth counts person-to-person links
    (e.g. max_depth=2 finds Bacon -> X -> target).
    """
    if not actor_name:
        return []

    if actor_name == "Kevin Bacon":
        return []

    # helper to get person id by name
    def _person_id_by_name(name: str) -> Optional[int]:
        q = "SELECT id FROM people WHERE name = ?"
        rows = run_query(db_file, q, [name]) or []
        return rows[0][0] if rows else None

    bacon_id = _person_id_by_name("Kevin Bacon")
    target_id = _person_id_by_name(actor_name)
    if bacon_id is None or target_id is None:
        return []

    # load all star relations and movie titles
    q = (
        "SELECT s.person_id, p.name, s.movie_id, m.title "
        "FROM stars s "
        "JOIN people p ON s.person_id = p.id "
        "JOIN movies m ON s.movie_id = m.id"
    )
    rows = run_query(db_file, q, []) or []

    person_to_movies: Dict[int, List[int]] = {}
    movie_to_people: Dict[int, List[int]] = {}
    person_names: Dict[int, str] = {}
    movie_titles: Dict[int, str] = {}

    for person_id, person_name, movie_id, movie_title in rows:
        person_to_movies.setdefault(person_id, []).append(movie_id)
        movie_to_people.setdefault(movie_id, []).append(person_id)
        person_names[person_id] = person_name
        movie_titles[movie_id] = movie_title

    # BFS over alternating person/movie path: start [person]
    results: List[str] = []
    seen_paths = set()
    q: deque = deque()
    q.append([bacon_id])

    while q:
        path = q.popleft()
        # persons are at even indices: 0,2,4...
        last_person = path[-1]
        # count person-to-person links = number of persons -1
        person_steps = (len([x for i, x in enumerate(path) if i % 2 == 0]) - 1)
        if person_steps > max_depth:
            continue

        if last_person == target_id and person_steps >= 1:
            key = tuple(path)
            if key in seen_paths:
                continue
            seen_paths.add(key)
            # build list of components
            parts = ["Kevin Bacon"]
            # iterate movie/person pairs
            i = 1
            while i < len(path):
                movie_id = path[i]
                person_id = path[i + 1]
                parts.append("was in")
                parts.append(movie_titles.get(movie_id, "?"))
                parts.append("with")
                parts.append(person_names.get(person_id, "?"))
                i += 2
            results.append(parts)
            # don't expand this path further
            continue

        # expand: from last_person -> movies -> other persons
        for movie_id in person_to_movies.get(last_person, []):
            for other_person in movie_to_people.get(movie_id, []):
                # avoid cycles in persons
                if other_person in (p for idx, p in enumerate(path) if idx % 2 == 0):
                    continue
                new_path = path + [movie_id, other_person]
                # prune by person_steps limit
                new_person_steps = (len([x for i, x in enumerate(new_path) if i % 2 == 0]) - 1)
                if new_person_steps > max_depth:
                    continue
                q.append(new_path)

    return results


def get_direct_connections(actor_name: str) -> List[Any]:
    # kept for backwards compatibility: 2 degrees
    return get_connections(actor_name, max_depth=2)