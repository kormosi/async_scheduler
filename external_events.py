# A global variable to hold the currently running thread
current = None

# A queue of threads that are waiting to run
ready_list = []


# A way of getting a thread into the scheduling system
def schedule(thread):
    ready_list.append(thread)


# If the thread is still at the head of the ready list after it has
# yielded, we move it to the end, so that the ready threads will run
# round-robin fashion.
def move_thread_to_back_of_queue(thread):
    if ready_list and ready_list[0] is thread:
        del ready_list[0]
        ready_list.append(thread)


# When the thread finishes, we use the following function to remove
# it from the scheduling system.
def unschedule(thread):
    if thread in ready_list:
        ready_list.remove(thread)


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

    # To acquire a fork, we first check to see
    # whether it is available. If not, we block the current thread on the
    # queue, and then yield. When we get to run again, it's our turn, so we
    # mark the fork as being in use.
    def acquire(self):
        if not self.available:
            block(self.queue)
            yield
        self.available = False

    # To release the fork, we mark it as available and then unblock the
    # thread at the head of the queue, if any.
    def release(self):
        self.available = True
        unblock(self.queue)


# The core loop of the scheduler will repeatedly take the thread at the
# head of the queue and run it until it yields:
def run():
    global current
    while ready_list:  # Meaning until it's empty
        thread = ready_list[0]
        current = thread
        try:
            next(thread)
        except StopIteration:
            unschedule(thread)
        else:
            move_thread_to_back_of_queue(thread)


# # We've got enough so far to try a simple test.
# def person(name, count):
#     for i in range(count):
#         print(f"{name} running")
#         yield
#
# schedule(person("John", 2))
# schedule(person("Michael", 3))
# schedule(person("Terry", 4))
#
# run()


# Next we need a life cycle for a philosopher.
def philosopher(
    name, lifetime, think_time, eat_time, left_fork: Fork, right_fork: Fork
):
    for i in range(lifetime):
        for j in range(think_time):
            print(f"{name} thinking")
            yield

        print(f"{name} waiting for fork {left_fork.id}")
        yield from left_fork.acquire()
        print(f"{name} acquired fork {left_fork.id}")

        print(f"{name} waiting for fork {right_fork.id}")
        yield from right_fork.acquire()
        print(f"{name} acquired fork {right_fork.id}")

        for j in range(eat_time):
            print(f"{name} eating spaghetti")
            yield

        print(f"{name} releasing forks {left_fork.id} and {right_fork.id}")
        left_fork.release()
        right_fork.release()

    print(f"{name} leaving the table")


# Now we can set up a scenario.
forks = [Fork(i) for i in range(3)]
schedule(philosopher("Plato",    1, 1, 2, forks[0], forks[1]))
schedule(philosopher("Socrates", 2, 2, 1, forks[1], forks[2]))
schedule(philosopher("Euclid",   3, 2, 2, forks[2], forks[0]))

# forks = [Fork(i) for i in range(2)]
# schedule(philosopher("Plato",    1, 1, 2, forks[0], forks[1]))
# schedule(philosopher("Socrates", 2, 2, 1, forks[1], forks[0]))

run()
