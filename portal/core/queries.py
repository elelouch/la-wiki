from typing import List


section_child_archives = """
WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section s 
    WHERE s.id = %s
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

sca_str = """
WITH RECURSIVE ancestors AS (
    SELECT *
    FROM core_section s 
    WHERE s.id = %s
    UNION ALL
    SELECT cs.*
    FROM core_section cs, ancestors a 
    WHERE cs.parent_id = a.id
) SELECT 
        {fields}
FROM ancestors
INNER JOIN core_archive arch
ON ancestors.id = arch.section_id
"""

def sca(*, fields: List[str]):
    assert fields
    fields_with_prefix = [ "arch." + f for f in fields ]
    fs = section_child_archives.format(
        '\n'.join(fields_with_prefix)
    )
    return sca_str.format(fields=fs)
