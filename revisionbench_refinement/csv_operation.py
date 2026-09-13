"""Bounded deterministic CSV transformation; no evaluation or arbitrary expressions."""
import csv
import io


def filter_csv(text,column,exclude_value):
    if len(text.encode())>65536:
        raise ValueError('CSV exceeds 64 KiB')
    reader=csv.reader(io.StringIO(text,newline=''))
    rows=list(reader)
    if not rows or len(rows[0])!=len(set(rows[0])) or column not in rows[0]:
        raise ValueError('Missing or duplicate CSV header')
    header=rows[0]
    if len(rows)>2049 or any(len(row)!=len(header) for row in rows[1:]):
        raise ValueError('CSV row shape or count invalid')
    index=header.index(column)
    kept=[row for row in rows[1:] if row[index]!=exclude_value]
    output=io.StringIO(newline='');writer=csv.writer(output,lineterminator='\n')
    writer.writerow(header);writer.writerows(kept)
    result=output.getvalue()
    if len(result.encode())>65536:raise ValueError('Transformed CSV exceeds limit')
    return result,{'rows_before':len(rows)-1,'rows_after':len(kept),'rows_removed':len(rows)-1-len(kept)}
