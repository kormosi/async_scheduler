# A global variable to hold the currently running thread
current = None

# A queue of threads that are waiting to run
ready_list = []


# A way of getting a thread into the scheduling system
def schedule(g):
    ready_list.append(g)


# If the thread is still at the head of the ready list after it has
# yielded, we move it to the end, so that the ready threads will run
# round-robin fashion.
def expire_timeslice(g):
    if ready_list and ready_list[0] is g:
        del ready_list[0]
        ready_list.append(g)


# When the thread finishes, we use the following function to remove
# it from the scheduling system.
def unschedule(g):
    if g in ready_list:
        ready_list.remove(g)


# This removes the currently running thread from the ready list and
# adds it to a list that you specify.
def block(queue):
    queue.append(current)
    unschedule(current)


# This removes the thread at the head of the specified list, if
# any, and adds it to the ready list.
def unblock(queue):
    if queue:
        g = queue.pop(0)
        schedule(g)


class Fork:
    def __init__(self, id):
        self.id = id
        self.available = True
        self.queue = []  # Queue of threads waiting to use it.

    def acquire(self):
        if not self.available:
            block(self.queue)
            yield
        self.available = False


# The core loop of the scheduler will repeatedly take the thread at the
# head of the queue and run it until it yields:
def run():
    global current
    while ready_list:  # Meaning until it's empty
        g = ready_list[0]
        current = g
        try:
            next(g)
        except StopIteration:
            unschedule(g)
        else:
            expire_timeslice(g)


# We've got enough so far to try a simple test.
def person(name, count):
    for i in range(count):
        print(f"{name} running")
        yield


schedule(person("John", 2))
schedule(person("Michael", 3))
schedule(person("Terry", 4))

run()
