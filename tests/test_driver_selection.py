from driver import select_steps


def test_select_steps():
    pipeline=[("C1",object()),("C2",object()),("C3",object())]
    assert [name for name,_ in select_steps(pipeline,"C2","C3")]==["C2","C3"]
