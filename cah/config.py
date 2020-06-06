import re
import collections

class ConfigParser(collections.MutableMapping):
    def __init__(self):
        self.content = ""
        self.data = dict()

    def load(self, f):
        self.loads(f.read())

    def loads(self, content: str):
        self.data = dict(default=dict(default=list()))
        
        currentGroup = "default"

        for line in content.splitlines():
            line = line.strip()
            if line.startswith('['):
                currentGroup = next(re.finditer(r"\[\s*(.*?)\s*\]", line)).group(1)
                self.data[currentGroup] = dict(default=list())
            else:
                # Could be default list, or named value
                try:
                    value = next(re.finditer(r"(.+?)\s*(?:=\s*(.+?))?\s*$", line)).groups()
                    if value[1]:
                        self.data[currentGroup][value[0]] = value[1]
                    else:
                        self.data[currentGroup]['default'].append(value[0])
                except StopIteration:
                    pass
    
    def dumps(self) -> str:
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

        output = dumpGroup(self.data['default'])

        for k, v in self.data:
            if k == 'default':
                continue
            output += dumpGroup(v, k)
        return output
    
    def dump(self, f):
        f.write(self.dumps())

    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __delitem__(self, key):
        del self.data[key]
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)
    
    def __repr__(self):
        return str(self.data)