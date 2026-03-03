import asyncio
from typing import AsyncGenerator #type hint for a function that yields values asynchronously

#in memory store
_progress_store: dict[str, list[str]] = {} # to store progress messages
_progress_events: dict[str,asyncio.Event] = {} # to store Event object per task

#called when upload process starts to create empty messsage list and fresh Event
def create_task(task_id: str):
    _progress_store[task_id] = []
    _progress_events[task_id] = asyncio.Event()

#called to add new messages 
def update_progress(task_id: str, message: str):
    if task_id in _progress_store:
        _progress_store[task_id].append(message)
        _progress_events[task_id].set() #signal for new message

#for debug to see all the messages for task
def get_progress(task_id:str) -> list[str]:
    return _progress_store.get(task_id, [])

#to remove task from memory after it's done
def cleanup_task(task_id:str):
    _progress_store.pop(task_id,None)
    _progress_events.pop(task_id,None)

#yield sse messages one by one
async def stream_progress(task_id: str) -> AsyncGenerator:
    sent_index = 0
    while True:
        messages = _progress_store.get(task_id, []) #check list

        while sent_index < len(messages):
            yield {"data": messages[sent_index]}
            sent_index+=1

            if messages[sent_index - 1] == "done":
                cleanup_task(task_id)
                return
            
        
        event = _progress_events.get(task_id)
        if event:
            event.clear()
            await asyncio.sleep(0.1)
        else:
            return
