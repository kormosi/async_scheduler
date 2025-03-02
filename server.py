import sys
from select import select

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


def run2():
    while True:
        # breakpoint()
        run()
        if not wait_for_event():
            return


# We will need a data structure to hold threads waiting for files. Each
# file needs two queues associated with it, for threads waiting to read
# and write respectively.
class FdQueues:
    def __init__(self):
        self.readq = []
        self.writeq = []


# We will keep a mapping from file objects to their associated FdQueue
# instances.
fd_queues = {}


# The following function retrieves the queues for a given fd, creating
# new ones if they don't already exist.
def get_fd_queues(fd):
    q = fd_queues.get(fd)
    if not q:
        q = FdQueues()
        fd_queues[fd] = q
    return q


# Now we can write a new pair of scheduling primitives to block on a file.
def block_for_reading(fd):
    block(get_fd_queues(fd).readq)


def block_for_writing(fd):
    block(get_fd_queues(fd).writeq)


# We'll also want a way of removing a file from the fd_queues when
# we've finished with it, so we'll add a function to close it and
# clean up.
def close_fd(fd):
    fd_queues.pop(fd)
    fd.close()

# Now we can write wait_for_event(). It's a bit long winded, but fairly
# straightforward. We build lists of file objects having nonempty read
# or write queues, pass them to select(), and for each one that's ready,
# we unblock the thread at the head of the relevant queue. If there are
# no threads waiting on any files, we return False to tell the scheduler
# there's no more work to do.
def wait_for_event():
    read_fds = []
    write_fds = []
    for fd, q in fd_queues.items():
        if q.readq:
            read_fds.append(fd)
        if q.writeq:
            write_fds.append(fd)
    if not (read_fds or write_fds):
        return False
    read_fds, write_fds, _ = select(read_fds, write_fds, [])
    for fd in read_fds:
        unblock(fd_queues[fd].readq)
    for fd in write_fds:
        unblock(fd_queues[fd].writeq)
    return True


# We could do with some higher-level functions for blocking operations
# on sockets, so let's write a few. First, accepting a connection from
# a listening socket.
def sock_accept(sock):
    block_for_reading(sock)
    yield
    return sock.accept()


# Now reading a line of text from a socket. We keep reading until the
# data ends with a newline or EOF is reached. (We're assuming that the
# client will wait for a reply before sending another line, so we don't
# have to worry about reading too much.) We also close the socket on
# EOF, since we won't be reading from it again after that.
def sock_readline(sock):
    buf = ""
    # TODO can be [-1] only?
    while buf[-1:] != "\n":
        block_for_reading(sock)
        yield
        data = sock.recv(1024)
        if not data:
            break
        buf += data
    if not buf:
        close_fd(sock)
    return buf


# Writing data to a socket. We loop until all the data has been written.
# We don't use sendall(), because it might block, and we don't want to
# hold up other threads.
def sock_write(sock, data):
    while data:
        block_for_writing(sock)
        yield
        n = sock.send(data)
        data = data[n:]


# At this point we can try a quick test to see if everything works
# so far.
def loop():
    while True:
        print("Waiting for input")
        block_for_reading(sys.stdin)
        yield
        # I don't understand why the prompt gets displayed the following print statement.
        # But no matter for now.
        print("Input is ready")
        line = sys.stdin.readline()
        print(f"Input was '{repr(line)}'")
        if not line:
            break


schedule(loop())
run2()
