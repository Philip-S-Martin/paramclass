from paramclass import ParamClass


def test_outer_name_function_call_still_defers_arguments():
    def combine(left, right):
        return f"{left}:{right}"

    class Demo(ParamClass):
        left = int(2)
        right = left + 3
        label = combine(left, right)

    assert Demo().label == "2:5"
    assert Demo(left=10).label == "10:13"


def test_outer_object_attribute_and_item_lookup_still_work():
    class Config:
        value = 4

    values = {"offset": 6}

    class Demo(ParamClass):
        base = Config.value
        total = base + values["offset"]

    assert Demo().total == 10
    assert Demo(base=20).total == 26


def test_inheritance_builds_base_parameters_first():
    class Base(ParamClass):
        x = 2
        y = x + 1

    class Child(Base):
        z = Base.y + 1

    assert Child().x == 2
    assert Child().y == 3
    assert Child().z == 4
    assert Child(x=10).y == 11
    assert Child(x=10).z == 12


def test_literal_dependencies_use_overrides():
    class Demo(ParamClass):
        x = 2
        y = x + 3

    assert Demo().x == 2
    assert Demo().y == 5
    assert Demo(x=10).x == 10
    assert Demo(x=10).y == 13


def test_literal_containers_resolve_nested_links():
    class Demo(ParamClass):
        x = 2
        values = [x, x + 1, (x + 2, {"next": x + 3})]

    assert Demo().values == [2, 3, (4, {"next": 5})]
    assert Demo(x=10).values == [10, 11, (12, {"next": 13})]


def test_nested_paramclass_instances_are_built_and_linkable():
    class Child(ParamClass):
        x = 2
        y = x + 1

    class Parent(ParamClass):
        child = Child()
        total = child.y + 10

    parent = Parent()
    overridden = Parent(child=Child(x=10))

    assert isinstance(parent.child, Child)
    assert parent.child.y == 3
    assert parent.total == 13
    assert overridden.child.y == 11
    assert overridden.total == 21


def test_collections_of_paramclasses_resolve_nested_links():
    class Child(ParamClass):
        x = 2
        y = x + 1

    class Parent(ParamClass):
        children = [Child(x=1), Child(x=2)]
        named = {"first": children[0], "second": children[1]}
        total = named["first"].y + named["second"].y

    parent = Parent()

    assert [child.y for child in parent.children] == [2, 3]
    assert parent.named["first"] is parent.children[0]
    assert parent.total == 5


def test_standalone_lambda_can_be_overridden():
    class Demo(ParamClass):
        transform = lambda value: value + 1
        result = transform(2)

    assert Demo().result == 3
    assert Demo(transform=lambda value: value * 10).result == 20


def test_language_constants_are_parameters():
    class Demo(ParamClass):
        enabled = True
        missing = None
        disabled = False
        enabled_check = enabled == True
        missing_check = missing == None
        disabled_check = disabled == False

    assert Demo().enabled is True
    assert Demo().missing is None
    assert Demo().disabled is False
    assert Demo().enabled_check is True
    assert Demo().missing_check is True
    assert Demo().disabled_check is True
    assert Demo(enabled=False).enabled_check is False


def test_methods_and_descriptors_are_not_parameters():
    class Demo(ParamClass):
        x = 2

        def method(self):
            return self.x + 1

        @property
        def doubled(self):
            return self.x * 2

        @staticmethod
        def identity(value):
            return value

        @classmethod
        def cls_name(cls):
            return cls.__name__

    demo = Demo(x=5)

    assert demo.method() == 6
    assert demo.doubled == 10
    assert demo.identity("value") == "value"
    assert demo.cls_name() == "Demo"
    assert "__build_order__" in Demo.__dict__
    assert "method" not in Demo.__build_order__
    assert "doubled" not in Demo.__build_order__
    assert "identity" not in Demo.__build_order__
    assert "cls_name" not in Demo.__build_order__
