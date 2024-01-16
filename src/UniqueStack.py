class UniqueStack:
    def __init__(self, ignore_stack=None):
        self.stack = []
        self.stackSet = set()
        self.ignoreSet = set(ignore_stack.stack) if ignore_stack else set()

    def push(self, url):
        if url not in self.stackSet and url not in self.ignoreSet:
            self.stack.append(url)
            self.stackSet.add(url)

    def push_all(self, urls, base=""):
        for url in urls:
            self.push(base+url)

    def pop(self):
        """
        Removes and returns the top URL from the stack.
        Also adds the url to the ignore-List so that URL can not be added anymore

        :return: The top URL from the stack, or None if the stack is empty.
        """
        if len(self.stack) == 0:
            return None
        url = self.stack.pop()
        self.stackSet.remove(url)
        self.ignoreSet.add(url)
        return url

    def is_empty(self):
        return len(self.stack) == 0

    def print_stack(self):
        for num, url in enumerate(self.stack, start=1):
            print(f"{num}:", url)
