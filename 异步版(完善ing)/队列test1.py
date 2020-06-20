import asyncio
import random
import time


async def worker(name, queue):
    while True:
        sleep_for = await queue.get()

        await asyncio.sleep(sleep_for)

        queue.task_done()

        print(f'{name} has slept for {sleep_for:.2f} seconds')


async def main():
    queue = asyncio.Queue()

    total_sleep_time = 0
    for _ in range(20):
        sleep_for = random.uniform(0.05, 1.0)
        print(sleep_for)
        total_sleep_time += sleep_for
        queue.put_nowait(sleep_for)

    tasks = []
    for i in range(3):
        task = asyncio.create_task(worker(f'worker-{i}', queue))
        tasks.append(task)
    print(queue.qsize())
    started_at = time.monotonic()
    await queue.join()
    total_slept_for = time.monotonic() - started_at
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

    print('====')
    print(f'3 workers slept in parallel for {total_slept_for:.2f} seconds')
    print(f'total expected sleep time: {total_sleep_time:.2f} seconds')


asyncio.run(main())