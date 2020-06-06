import re


class ConfigParser():
    VALUE_REGEX = r"([^\s;](?:[^;\\=]*?(?:\\;|\\=|\\n)?)+)"

    def __init__(self):
        self.content = ""

    @classmethod
    def load(cls, f) -> dict:
        """
        Load a file object
        """
        return cls.loads(f.read())

    @classmethod
    def loads(cls, content: str) -> dict:
        """
        Load a string config
        """
        data = dict(default=dict(default=list()))

        currentGroup = "default"
        def unescape(s: str):
            if not s:
                return
            return s.replace(r"\;", ";").replace(r"\=", "=")


        for line in content.splitlines():
            line = line.strip()
            try:
                # Get the group
                currentGroup = unescape(next(re.finditer(r"\[\s*{v}\s*\]".format(v=cls.VALUE_REGEX), line)).group(1)).lower()
                data[currentGroup] = dict(default=list())
            except StopIteration:
                # Could be default list, or named value
                try:
                    regex = r"{v}(?:\s*=\s*{v})?\s*(?=$|;)".format(v=cls.VALUE_REGEX)
                    value = list(map(unescape, next(re.finditer(regex, line)).groups()))
                    if value[1]:
                        data[currentGroup][value[0].lower()] = value[1]
                    else:
                        data[currentGroup]['default'].append(value[0])
                except StopIteration:
                    pass
        return data

    @classmethod
    def dumps(cls, data: dict) -> str:
        """
        Dump to a string
        """
        def dumpGroup(value, group=None) -> str:
            out = ""
            if group:
                out = "[%s]\n" % group

            for k, v in value:
                if k == 'default':
                    continue
                out += "%s = %s\n" % (k, v)

            out += '\n'.join(value['default'])
            out += '\n'
            return out

        output = dumpGroup(data['default'])

        for k, v in data:
            if k == 'default':
                continue
            output += dumpGroup(v, k)
        return output

    @classmethod
    def dump(cls, f, data: dict):
        """
        Dump to a file
        """
        f.write(cls.dumps(data))

