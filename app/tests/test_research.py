from app.services import research as R


def _fake(calls):
    def f(q):
        calls.append(q)
        return {"results": [{"title": f"Co {len(calls)}", "url": f"https://x.test/{len(calls)}", "content": "c"},
                            {"title": "nourl", "url": "", "content": "c"}]}
    return f


def test_fixture_fallback_gives_three_items_marked_demo(tmp_path):
    items = R.research("gastos corporativos", data_dir=tmp_path)
    assert len(items) >= 3 and all(i.url and i.demo_data for i in items)


def test_live_results_are_cached_and_drop_missing_url(tmp_path):
    calls = []
    a = R.research("x", data_dir=tmp_path, search=_fake(calls))
    b = R.research("x", data_dir=tmp_path, search=_fake(calls))
    assert len(calls) == 1 and [i.url for i in a] == [i.url for i in b] == ["https://x.test/1"]
    assert not a[0].demo_data and a[0].fetched_at


def test_dev_mode_adds_stack_docs(tmp_path):
    calls = []
    R.research("x", "dev", data_dir=tmp_path, search=_fake(calls), stack=["Supabase Auth"])
    assert calls[-1] == "Supabase Auth current documentation" and len(calls) == 2


def test_credit_cap_falls_back_to_fixture(tmp_path):
    calls = []
    b = R.CreditBudget(1)
    items = R.research("x", "dev", data_dir=tmp_path, search=_fake(calls), stack=["A", "B"], budget=b)
    assert len(calls) == 1 and any(i.demo_data for i in items)


def test_search_error_falls_back(tmp_path):
    def boom(q):
        raise RuntimeError("down")
    assert all(i.demo_data for i in R.research("x", data_dir=tmp_path, search=boom))
