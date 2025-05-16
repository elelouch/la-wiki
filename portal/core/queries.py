from typing import List

# Entiendo que las queries son muy repetitivas, pero es mas legible esto que falopearla
# con una query completamente dinamica

section_children_archives_by_like_name = """
WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section s 
    WHERE s.id = %(root_id)s
    UNION ALL
    SELECT cs.*
    FROM core_section cs, ancestors a 
    WHERE cs.parent_id = a.id
) SELECT 
        arch.id,
        arch.fullname
FROM ancestors
INNER JOIN core_archive arch
ON ancestors.id = arch.section_id
WHERE arch.fullname LIKE %(like_name)s
"""

section_children_archives = """
WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section s 
    WHERE s.id = %(root_id)s
    UNION ALL
    SELECT cs.*
    FROM core_section cs, ancestors a 
    WHERE cs.parent_id = a.id
) SELECT 
        arch.id,
        arch.fullname
FROM ancestors
INNER JOIN core_archive arch
ON ancestors.id = arch.section_id
"""

section_children_archives_where_uuid_available = """
WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section s 
    WHERE s.id = %(root_id)s
    UNION ALL
    SELECT cs.*
    FROM core_section cs, ancestors a 
    WHERE cs.parent_id = a.id
) SELECT 
    arch.id,
    arch.fullname
FROM ancestors
INNER JOIN core_archive arch
ON ancestors.id = arch.section_id
WHERE arch.uuid IN %(uuid_tuple)s
"""

"""
COMO USAR ESTA QUERY
Primero, es requerido armar una string con los valores de la tabla
de expresion constante (CTE), esta tendra una forma tipo (arch_uuid, elasticsearch_score).
Ej: '("a03f", 1.234), ("b02e", 0.3456)'.
La CTE entonces, tendria dos registros con esos valores.
Utilizando .format(cte_values=values), se colocaran los valores dentro de la query.
"""
section_chidren_archives_orderby_cte = """
WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section s 
    WHERE s.id = %(root_id)s
    UNION ALL
    SELECT cs.*
    FROM core_section cs, ancestors a 
    WHERE cs.parent_id = a.id
),vals(uuid, elasticsearch_score) AS (VALUES {cte_values})
SELECT 
    arch.id,
    arch.fullname
FROM ancestors
INNER JOIN core_archive arch
ON ancestors.id = arch.section_id
INNER JOIN vals v
ON v.uuid = arch.uuid
ORDER BY elasticsearch_score
"""

section_children = """
WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section s 
    WHERE s.id = %s
    UNION ALL
    SELECT cs.*
    FROM core_section cs, ancestors a 
    WHERE cs.parent_id = a.id
) SELECT * FROM ancestors;
"""
