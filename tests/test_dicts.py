from dynagefw.utils import flatten_dict, nest_dict


def test_nest_flatten():
    flat = flatten_dict({"age": 11, "cog": {"ps": 1, "mem": 3}})
    assert flat == flatten_dict(nest_dict(flat))

