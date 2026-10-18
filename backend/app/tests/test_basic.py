def test_token_protector_basic():
    from app.services.translation.token_protector import TokenProtector
    tp = TokenProtector()
    s = 'Hello ivan@example.com 2026-10-18'
    p, m = tp.protect(s)
    r, ok = tp.restore(p, m)
    assert ok and r == s


def test_text_pipeline():
    from app.services.text_input.pipeline import TextPipeline
    tp = TextPipeline()
    segs = tp.process('Привет\n\nHello')
    assert len(segs) == 2
