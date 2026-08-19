from ledgerline.api.router import Request, Router


def test_a_matching_route_is_dispatched():
    r = Router()
    r.add("GET", "/v1/ping", lambda req: (200, {"pong": True}))
    assert r.dispatch(Request("GET", "/v1/ping")).body == {"pong": True}


def test_path_parameters_reach_the_handler():
    r = Router()
    r.add("GET", "/v1/things/<thing_id>", lambda req, thing_id: (200, {"id": thing_id}))
    assert r.dispatch(Request("GET", "/v1/things/abc")).body == {"id": "abc"}


def test_an_unknown_path_is_404():
    assert Router().dispatch(Request("GET", "/nope")).status == 404


def test_the_method_has_to_match():
    r = Router()
    r.add("POST", "/v1/things", lambda req: (201, {}))
    assert r.dispatch(Request("GET", "/v1/things")).status == 404


def test_a_handler_that_raises_becomes_an_error_response():
    r = Router()

    def boom(req):
        raise ValueError("bad input")

    r.add("GET", "/v1/boom", boom)
    resp = r.dispatch(Request("GET", "/v1/boom"))
    assert resp.status == 400 and resp.body["error"]["code"] == "invalid_request"


def test_headers_are_read_case_insensitively():
    req = Request("POST", "/x", headers={"Idempotency-Key": "k"})
    assert req.header("idempotency-key") == "k"
    assert req.header("missing", "fallback") == "fallback"


def test_the_route_decorator_registers():
    r = Router()

    @r.route("GET", "/v1/decorated")
    def handler(req):
        return 200, {"ok": True}

    assert r.dispatch(Request("GET", "/v1/decorated")).status == 200
