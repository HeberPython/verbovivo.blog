"""Fail closed before a generated reflection can become an approval draft."""
from html import unescape
import re


class EditorialTextError(RuntimeError):
    pass


def validate_reflection(source: str, body: str) -> None:
    paragraphs = re.findall(r'<p>(.*?)</p>', body, re.DOTALL)
    prose = [unescape(re.sub(r'<[^>]+>', '', part)).strip() for part in paragraphs]
    words = sum(len(part.split()) for part in prose)
    minimum = min(450, max(80, int(len(source.split()) * 0.45)))
    if words < minimum or len(prose) < 3:
        raise EditorialTextError(f'Incomplete reflection: {words} prose words; minimum {minimum}.')
    if '<h2>Para meditar</h2>' in body and 'Que esta palavra seja lida com calma' in body:
        raise EditorialTextError('Emergency placeholder is not a publishable reflection.')
    for part in prose:
        end = part.rstrip('"\'\u201d\u2019) ]')
        if not end or end[-1] not in '.!?\u2026:':
            raise EditorialTextError('Unfinished paragraph; approval draft blocked.')

