class UniqueStack:
    """

    :class: UniqueStack

    A stack that stores unique URLs and provides methods for adding and removing URLs.

    :ivar stack: A list that stores the URLs in the stack.
    :ivar stackSet: A set that stores the URLs in the stack for quick lookup.
    :ivar ignoreSet: A set that stores the URLs that should be ignored and should not be added to the stack.

    Methods:
        - __init__(self, ignore_stack=None): Initializes the UniqueStack object.
        - push(self, url): Pushes a URL to the top of the stack.
        - push_all(self, urls, base=""): Pushes multiple URLs to the stack.
        - pop(self): Removes and returns the top URL from the stack.
        - is_empty(self): Checks if the stack is empty.
        - print_stack(self): Prints the URLs in the stack.

    """
    def __init__(self, ignore_stack=None):
        self.stack = []
        self.stackSet = set()
        self.ignoreSet = set(ignore_stack.stack) if ignore_stack else set()

    def push(self, url):
        if url not in self.stackSet and url not in self.ignoreSet:
            self.stack.append(url)
            self.stackSet.add(url)

    def push_all(self, urls, base=""):
        """
        Pushes all the URLs to a queue for processing.

        :param urls: List of URLs to push.
        :param base: Base URL to prepend to each URL.
                    This is neccesary if the URLs given are relative to the base URL
                    Default is an empty string.
        :return: None

        """
        for url in urls:
            if url[:4] == 'http':
                self.push(url)
            else:
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
