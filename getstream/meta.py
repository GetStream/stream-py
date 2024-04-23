def method_wrapper(client_method_name, attrs):
    def inner(self, *args, **kwargs):
        client_method = getattr(self.client, client_method_name)
        attr_args = attrs and map(lambda a: getattr(self, a), attrs) or []
        return client_method(*attr_args, *args, **kwargs)

    return inner


def resource(attrs_arg, methods):
    def decorator(cls):
        for src_name, dst_name in methods.items():
            cls.dst_name = method_wrapper(dst_name, attrs_arg)

    return decorator
