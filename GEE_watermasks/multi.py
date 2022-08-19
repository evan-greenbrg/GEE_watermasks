from contextlib import closing
import multiprocessing
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import current_process
from multiprocessing import cpu_count

from download import ee_export_image
#
# Function run by worker processes
#
NUMBER_OF_PROCESSES = cpu_count() - 1


def worker(input, output):
    for func, args in iter(input.get, 'STOP'):
        result = calculate(func, args)
        output.put(result)


def calculate(func, args):
    result = func(*args)
    return '%s says that %s%s = %s' % \
        (current_process().name, func.__name__, args, result)


def stop(task_queue):
    for i in range(NUMBER_OF_PROCESSES):
        task_queue.put('STOP')


def export(image, out):
    ee_export_image(
        image,
        out,
        30
    )
    return True


def multiprocess_orig(tasks):
    POOL_SIZE = cpu_count() - 1

    # Create queues
    task_queue = Queue()
    done_queue = Queue()

    # Submit tasks
    for task in tasks:
        task_queue.put(task)

    # Start worker processes
    for i in range(POOL_SIZE):
        Process(
            target=worker, args=(task_queue, done_queue)
        ).start()

    # Tell child processes to stop
    for i in range(POOL_SIZE):
        task_queue.put('STOP')


def multiprocess(tasks):
    POOL_SIZE = cpu_count() - 1
#    POOL_SIZE = 10

    task_args = []
    for task in tasks:
        fun, args = task
        task_args.append(args)

    results = []
    with closing(multiprocessing.Pool(POOL_SIZE)) as pool:
        completed = pool.starmap(fun, task_args)

    results.extend(completed)

    return results
